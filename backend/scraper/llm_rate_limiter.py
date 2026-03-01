"""
VeriServe — LLM Rate Limiter
=============================
Shared module used by both scraper.py and scam_detector.py.

Strategy implemented:
  • Mandatory gap between every call
  • Batch cooldown after every N calls
  • Supports both Gemini and Groq (Groq limits are usually larger but we stay safe)

Usage:
    from scraper.llm_rate_limiter import llm_wait
    llm_wait(provider="groq")  # call this immediately before every LLM call
"""

import time

# ── Module-level state ────────────────────────────────────────────────────────
_call_counts: dict = {"gemini": 0, "groq": 0}
_last_call_ts: dict = {"gemini": 0.0, "groq": 0.0}

# Tuning knobs
LIMITS = {
    "gemini": {
        "MIN_GAP": 1.5,
        "BATCH_SIZE": 5,
        "BATCH_PAUSE": 10.0,
    },
    "groq": {
        "MIN_GAP": 0.5,
        "BATCH_SIZE": 10,
        "BATCH_PAUSE": 2.0,
    }
}


def llm_wait(label: str = "", provider: str = "gemini") -> None:
    """
    Enforce rate limiting before an LLM API call.
    """
    global _call_counts, _last_call_ts

    cfg = LIMITS.get(provider, LIMITS["gemini"])
    
    # 1. Batch cooldown
    count = _call_counts.get(provider, 0)
    if count > 0 and count % cfg["BATCH_SIZE"] == 0:
        print(f"[RateLimiter] {provider.upper()} {count} calls — pause {cfg['BATCH_PAUSE']}s...")
        time.sleep(cfg["BATCH_PAUSE"])

    # 2. Per-call gap
    last_ts = _last_call_ts.get(provider, 0.0)
    elapsed = time.time() - last_ts
    if elapsed < cfg["MIN_GAP"]:
        time.sleep(cfg["MIN_GAP"] - elapsed)

    # 3. Record the call
    _call_counts[provider] = count + 1
    _last_call_ts[provider] = time.time()

    tag = f" [{label[:40]}]" if label else ""
    print(f"[RateLimiter] {provider.upper()} Call #{_call_counts[provider]}{tag}")


def reset() -> None:
    """Reset counters (useful for testing)."""
    global _call_count, _last_call_ts
    _call_count = 0
    _last_call_ts = 0.0
