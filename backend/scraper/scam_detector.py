"""
VeriServe Scam Detector — Hybrid Trust Engine (v2.0)
======================================================
Architecture: Two-stage scoring pipeline

  Stage 1 — Rule Engine (instant, zero quota cost)
    Fast heuristic scoring using keyword patterns, NGO name lists,
    and source metadata. Same logic as v1.0.

  Stage 2 — LLM Arbitration (Gemini 2.0 Flash, only when needed)
    Only invoked for the ambiguous middle zone (raw score 45–89).
    The LLM acts as a second-opinion judge, reading the full context
    and returning a structured verdict + score adjustment + reasoning.

    Clearly safe (score >= 90) and clearly scam (score < 45) rows
    skip the LLM entirely to preserve API quota.

Trust Score bands:
  90–100 : GREEN  — Verified
  50–89  : YELLOW — Needs Community Review
  0–49   : RED    — Flagged / Hidden from feed
"""

import os
import re
import json
from typing import Tuple, List

import google.generativeai as genai
from groq import Groq
from dotenv import load_dotenv
from scraper.llm_rate_limiter import llm_wait

load_dotenv()

# ── Red Flag Signals ──────────────────────────────────────────────────────────

MONEY_REQUEST_PATTERNS = [
    r"\bsend\s+money\b", r"\btransfer\s+funds?\b", r"\bpay\s+fee\b",
    r"\bregistration\s+fee\b", r"\bdonat[ei]\s+now\b", r"\bbank\s+transfer\b",
    r"\bupi\s+id\b", r"\bgooglep[ay]+\b", r"\bpayment\s+required\b",
    r"\bpay\s+\₹\b", r"\bpay\s+rs\.?\b", r"\bcash\s+required\b",
    r"\bwire\s+transfer\b", r"\bsend\s+cash\b",
]

EXTREME_URGENCY_PATTERNS = [
    r"\bact\s+now\b", r"\burgent[ly]*\b", r"\blast\s+chance\b",
    r"\bexpir[eing]+\s+soon\b", r"\blimited\s+time\b",
    r"\bonly\s+\d+\s+spots?\s+left\b", r"\btoday\s+only\b",
    r"\bimmediately?\b", r"\bdeadline\s+tonight\b",
]

UNVERIFIED_LINK_PATTERNS = [
    r"bit\.ly/", r"tinyurl\.com/", r"t\.co/", r"ow\.ly/",
    r"goo\.gl/", r"rb\.gy/", r"cutt\.ly/", r"shorturl\.",
]

SUSPICIOUS_PHRASES = [
    r"\bguaranteed\s+reward\b", r"\bwork\s+from\s+home\b",
    r"\bearn\s+money\b", r"\bmake\s+money\b",
    r"\bno\s+experience\s+needed\b", r"\bget\s+paid\b",
    r"\bwinners?\s+selected\b", r"\bprize\s+money\b",
    r"\bfree\s+gift\b", r"\bclaim\s+your\b",
]

# ── Trust Boosters ────────────────────────────────────────────────────────────

TRUSTED_NGOS = [
    "team everest", "chennai volunteers", "exnora", "aid india",
    "isha foundation", "habitat for humanity", "cry", "rotary",
    "lions club", "red cross", "unicef", "nss", "ngo", "trust",
    "foundation", "association", "society", "charity",
    "efi", "environmentalist foundation", "thuvakkam", "united way",
]

OFFICIAL_INDICATORS = [
    r"\bregistered\s+ngo\b", r"\bgovernment\s+approved\b",
    r"\bcsr\s+initiative\b", r"\biso\s+certified\b",
    r"\bofficial\s+partner\b", r"\baccredited\b",
]

POSITIVE_KEYWORDS = [
    "volunteer", "community", "help", "support", "education",
    "health", "environment", "clean", "teach", "mentor",
    "relief", "flood", "disaster", "elderly", "children", "women",
]


# ── Stage 1: Rule Engine ──────────────────────────────────────────────────────

def _rule_score(
    title: str,
    description: str,
    ngo_name: str,
    source: str,
    source_url: str,
) -> Tuple[int, List[str]]:
    """
    Fast heuristic scoring. Returns (raw_score, flags).
    """
    text = f"{title} {description} {ngo_name}".lower()
    flags: List[str] = []
    score = 60  # neutral baseline

    # Source bonus
    if source == "rss":
        score += 15
    elif source == "social":
        score -= 5

    # Trusted NGO name
    ngo_lower = ngo_name.lower()
    for trusted in TRUSTED_NGOS:
        if trusted in ngo_lower:
            score += 10
            break

    # Official indicators
    for pattern in OFFICIAL_INDICATORS:
        if re.search(pattern, text, re.IGNORECASE):
            score += 5

    # Positive keywords
    positive_hits = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    score += min(positive_hits * 2, 10)

    # RED FLAG: Money requests
    for pattern in MONEY_REQUEST_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append("💸 Money/payment request detected")
            score -= 30
            break

    # RED FLAG: Extreme urgency
    urgency_hits = sum(
        1 for p in EXTREME_URGENCY_PATTERNS
        if re.search(p, text, re.IGNORECASE)
    )
    if urgency_hits >= 2:
        flags.append("⚡ Multiple extreme urgency signals")
        score -= 20
    elif urgency_hits == 1:
        score -= 8

    # RED FLAG: Shortened/suspicious URLs
    url_to_check = f"{description} {source_url or ''}".lower()
    for pattern in UNVERIFIED_LINK_PATTERNS:
        if re.search(pattern, url_to_check, re.IGNORECASE):
            flags.append("🔗 Shortened/unverified URL detected")
            score -= 20
            break

    # RED FLAG: Suspicious phrases
    for pattern in SUSPICIOUS_PHRASES:
        if re.search(pattern, text, re.IGNORECASE):
            flags.append("⚠️ Suspicious phrase detected")
            score -= 15
            break

    return max(0, min(100, score)), flags


# ── Stage 2: LLM Arbitration ─────────────────────────────────────────────────

def _llm_arbitrate(
    title: str,
    description: str,
    ngo_name: str,
    source_url: str,
    rule_score: int,
    rule_flags: List[str],
) -> Tuple[int, str, str]:
    """
    Ask Groq (fallback to Gemini) to review an opportunity.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not groq_key and not gemini_key:
        return 0, "", "LLM skipped: no API keys"

    rule_flags_text = "\n".join(rule_flags) if rule_flags else "None"
    prompt = f"""You are VeriServe's AI Trust Analyst for Chennai volunteering opportunities.

Your job: Decide if this post is a genuine volunteer opportunity or a scam/misleading listing.

INPUT:
  Title       : {title}
  Description : {description}
  NGO Name    : {ngo_name}
  Source URL  : {source_url or "not provided"}
  Rule Score  : {rule_score}/100 (from heuristic engine)
  Rule Flags  : {rule_flags_text}

EVALUATION CRITERIA:
  - Is this a real, specific volunteering activity (not just contact info or an internship application)?
  - Does the NGO seem legitimate (known name, proper description, no payment demands)?
  - Are there subtle manipulation tactics the rules may have missed?
  - Is the description coherent and contextually appropriate for a volunteering post?

RESPOND with a JSON object (no markdown, raw JSON only):
{{
  "verdict": "verified" | "needs_review" | "flagged",
  "score_adjustment": <integer from -30 to +30>,
  "reasoning": "<one concise sentence explaining your decision>"
}}
"""

    # 1. Try Groq (Primary)
    if groq_key:
        try:
            client = Groq(api_key=groq_key)
            llm_wait(label=title[:40], provider="groq")
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"},
            )
            result = json.loads(chat_completion.choices[0].message.content)
            verdict = result.get("verdict", "needs_review")
            adj = int(result.get("score_adjustment", 0))
            reasoning = result.get("reasoning", "")
            return max(-30, min(30, adj)), verdict, f"Groq: {reasoning}"
        except Exception as exc:
            print(f"[TrustEngine] Groq call failed: {exc}")

    # 2. Try Gemini (Fallback)
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-2.0-flash")
            llm_wait(label=title[:40], provider="gemini")
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            result = json.loads(response.text)
            verdict = result.get("verdict", "needs_review")
            adj = int(result.get("score_adjustment", 0))
            reasoning = result.get("reasoning", "")
            return max(-30, min(30, adj)), verdict, f"Gemini: {reasoning}"
        except Exception as exc:
            print(f"[TrustEngine] Gemini fallback failed: {exc}")

    return 0, "", "LLM error: both providers failed"


# ── Main entry point ──────────────────────────────────────────────────────────

def detect_scam(
    title: str,
    description: str,
    ngo_name: str,
    source: str = "manual",
    source_url: str = "",
) -> Tuple[int, str, list, str]:
    """
    Hybrid trust scoring pipeline.
    Returns: (trust_score, status, flags, reasoning)
    """
    # Stage 1: Rule engine (always runs)
    rule_score, flags = _rule_score(title, description, ngo_name, source, source_url)

    llm_reasoning = ""

    # Stage 2: LLM arbitration (only for ambiguous middle zone)
    if 45 <= rule_score <= 89:
        adj, llm_verdict, llm_reasoning = _llm_arbitrate(
            title, description, ngo_name, source_url, rule_score, flags
        )

        final_score = max(0, min(100, rule_score + adj))

        if llm_reasoning:
            flags.append(f"🤖 AI: {llm_reasoning}")

        print(
            f"[TrustEngine] LLM arbitrated: rule={rule_score} adj={adj:+d} "
            f"final={final_score} verdict={llm_verdict} | {title[:40]}"
        )
    else:
        final_score = rule_score
        reason = "clearly safe (rule >= 90)" if rule_score >= 90 else "clearly scam (rule < 45)"
        llm_reasoning = f"Rule engine assessment: {reason}"
        print(f"[TrustEngine] LLM skipped ({reason}): score={rule_score} | {title[:40]}")

    # Determine final status
    if final_score >= 90:
        status = "verified"
    elif final_score >= 50:
        status = "needs_review"
    else:
        status = "flagged"

    return final_score, status, flags, llm_reasoning


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        {
            "title": "Beach Cleanup Drive — Marina Beach",
            "description": "Join Team Everest for our monthly beach cleanup. Gloves and bags provided. Registered NGO. Community service.",
            "ngo_name": "Team Everest",
            "source": "rss",
        },
        {
            "title": "URGENT: Send UPI payment fee to register",
            "description": "Act now, only 5 spots left! Pay Rs.500 registration fee via UPI ID volunteer@pay. Last chance!",
            "ngo_name": "HelpNow Initiative",
            "source": "social",
        },
        {
            "title": "Teaching children in Vyasarpadi",
            "description": "Volunteer to teach English to underprivileged children every Saturday morning.",
            "ngo_name": "Chennai Volunteers",
            "source": "rss",
        },
        {
            "title": "Earn money while helping — work from home",
            "description": "Get paid Rs.2000 per day. Guaranteed reward. No experience needed. Click bit.ly/scam123",
            "ngo_name": "QuickHelp",
            "source": "social",
            "source_url": "bit.ly/scam123",
        },
        {
            "title": "Afforestation Drive",
            "description": "Thuvakkam organises tree planting sessions across Chennai. Join us to plant native species and restore green cover.",
            "ngo_name": "Thuvakkam",
            "source": "rss",
        },
        {
            "title": "Waste Segregation Awareness",
            "description": "Help spread awareness about dry/wet waste segregation in residential areas. Weekend activity.",
            "ngo_name": "Exnora International",
            "source": "social",
        },
    ]

    print("=" * 65)
    print("VeriServe Hybrid Trust Engine v2.0 — Test Results")
    print("=" * 65)
    for tc in test_cases:
        score, status, flags, reasoning = detect_scam(
            tc["title"], tc["description"], tc["ngo_name"],
            tc.get("source", "manual"), tc.get("source_url", "")
        )
        icon = "🟢" if status == "verified" else ("🟡" if status == "needs_review" else "🔴")
        print(f"\n{icon} [{score}/100]  {tc['title'][:55]}")
        print(f"   Status : {status.upper()}")
        for f in flags:
            print(f"   Flag   : {f}")
    print("\n" + "=" * 65)
