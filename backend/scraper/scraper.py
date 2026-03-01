"""
VeriServe Scraper — Plugin Architecture
=========================================
Each data source is a class that extends SiteScraper.
Adding a new source = write one class + add one line to SITE_SCRAPERS.

Active scrapers (verified Feb 2026):
  - UnitedWayChennaiScraper  → unitedwaychennai.org/volunteering/ (9 real opportunities)
  - EFIScraper               → indiaenvironment.org/volunteer/ (Lake clean-ups, wall painting, plantation)
  - ThuvakkamScraper         → thuvakkam.org/ (Afforestation, Blue Zone, Education)
  - RotaryFeedScraper        → rotary3232.org/feed/ (RSS, ready when they post)

Future (requires headless browser):
  - IVolunteerScraper        → ivolunteer.in/search (JS-rendered, needs Playwright)
"""

import sys
import os
import re
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import feedparser
import httpx
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import List, Dict
import google.generativeai as genai
from groq import Groq
import json
from dotenv import load_dotenv
from scraper.scam_detector import detect_scam
from scraper.llm_rate_limiter import llm_wait

# Load environment variables (like GEMINI_API_KEY) from .env
load_dotenv()


# ── HTML / whitespace helper ──────────────────────────────────────────────────

def strip_html(raw: str) -> str:
    """Strip HTML tags and normalise whitespace from RSS/HTML descriptions."""
    if not raw:
        return ""
    # Ensure we use the lxml parser for robust cleaning
    soup = BeautifulSoup(raw, "lxml")
    
    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    text = soup.get_text(separator=" ")
    # Normalise whitespace and remove zero-width chars
    text = re.sub(r"\s+", " ", text).replace("\u200b", "").strip()
    return text


# Contact-method words the LLM sometimes picks up as "titles" from bold text
_CONTACT_TITLE_PATTERN = re.compile(
    r'^(email|phone|tel|contact|fax|whatsapp|call us|reach us|address)\b',
    re.IGNORECASE
)


def extract_opportunities_with_llm(raw_text: str, source_url: str = "") -> List[Dict]:
    """
    Calls Groq (primary) or Gemini to extract structured volunteering opportunities.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not groq_key and not gemini_key:
        print("[LLM] ERROR: No LLM API keys provided.")
        return []

    prompt = (
        "You are extracting volunteering opportunities from an NGO website block.\n"
        "Rules:\n"
        "  1. Return ONLY a JSON array of objects. Each object must have:\n"
        "       title       - the specific activity name (e.g. 'Lake Clean-up', 'Wall Painting')\n"
        "       description - 1-3 sentence summary of the activity\n"
        "       category    - one of: Environment, Education, Health, Disaster Relief, Elder Care, General\n"
        "  2. DO NOT extract objects where the title is just a contact method.\n"
        "  3. DO NOT include footer text, navigation links, or email addresses as titles.\n"
        "  4. If no genuine volunteering activity is described, return an empty array [].\n\n"
        f"TEXT:\n{raw_text}"
    )

    # 1. Try Groq
    if groq_key:
        try:
            client = Groq(api_key=groq_key)
            llm_wait(label="extract_opportunities", provider="groq")
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"},
            )
            items = json.loads(chat_completion.choices[0].message.content)
            if isinstance(items, dict) and "opportunities" in items: # Some models wrap in a key
                items = items["opportunities"]
            if not isinstance(items, list):
                # Check for alternative wrapper keys
                for key in items:
                    if isinstance(items[key], list):
                        items = items[key]
                        break
            
            if isinstance(items, list):
                # Post-LLM safety filter
                cleaned = []
                for item in items:
                    title = item.get("title", "").strip()
                    if not title or _CONTACT_TITLE_PATTERN.match(title):
                        continue
                    if source_url:
                        item["source_url"] = source_url
                    cleaned.append(item)
                return cleaned
        except Exception as exc:
            print(f"[LLM] Groq extraction failed: {exc}")

    # 2. Try Gemini Fallback
    if gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            llm_wait(label="extract_opportunities", provider="gemini")
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            items = json.loads(response.text)
            if not isinstance(items, list): return []
            cleaned = []
            for item in items:
                title = item.get("title", "").strip()
                if not title or _CONTACT_TITLE_PATTERN.match(title): continue
                if source_url: item["source_url"] = source_url
                cleaned.append(item)
            return cleaned
        except Exception as exc:
            print(f"[LLM] Gemini extraction failed: {exc}")

    return []


# ── Base Plugin Class ─────────────────────────────────────────────────────────

class SiteScraper(ABC):
    """
    All site-specific scrapers inherit from this.
    Implement scrape() to return a list of raw opportunity dicts.
    """
    NAME: str = "Unknown"

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """Fetch and return a list of raw opportunity dicts (no trust score yet)."""
        ...

    def _log(self, msg: str):
        print(f"[{self.NAME}] {msg}")


# ── Scraper 1: United Way Chennai ─────────────────────────────────────────────

class UnitedWayChennaiScraper(SiteScraper):
    """
    Scrapes the United Way Chennai volunteering page.
    Titles are fetched live from <h2> headings.
    Descriptions are hand-written (originals are behind JS popups).
    Source: https://unitedwaychennai.org/volunteering/
    """
    NAME = "United Way Chennai"
    URL  = "https://unitedwaychennai.org/volunteering/"

    # Known <h2> titles → short description, category, location coords
    OPPORTUNITY_DETAILS: Dict[str, Dict] = {
        "Paint-A-Thon": {
            "description": (
                "Brighten the walls of Govt. schools across Chennai! Join United Way volunteers "
                "to create eye-catching murals and awareness messages. No prior art experience needed."
            ),
            "category": "Education",
            "location": "Government Schools, Chennai",
            "lat": 13.0827, "lng": 80.2707,
        },
        "Craft-A-Thought": {
            "description": (
                "Create fun, hands-on learning materials for underprivileged children in Anganwadis "
                "using recyclable everyday items — origami, flashcards, paper bags, and more."
            ),
            "category": "Education",
            "location": "Anganwadis, Chennai",
            "lat": 13.0827, "lng": 80.2707,
        },
        "Help the visually-impaired": {
            "description": (
                "Lend your voice to help visually-impaired students prepare for competitive exams. "
                "Record audiobook chapters using your phone — a few hours makes a lasting difference."
            ),
            "category": "Health",
            "location": "Virtual / Chennai",
            "lat": 13.0827, "lng": 80.2707,
        },
        "Kadhaikana Neram": {
            "description": (
                "Spend an hour reading stories and engaging with children from underserved communities. "
                "foster imagination and a love for learning through storytelling sessions."
            ),
            "category": "Education",
            "location": "Community Centres, Chennai",
            "lat": 13.0827, "lng": 80.2707,
        },
        "Engage & Encourage": {
            "description": (
                "Mentor and motivate school students from low-income backgrounds. "
                "Share career insights, life skills, and encouragement through structured sessions."
            ),
            "category": "Education",
            "location": "Chennai",
            "lat": 13.0827, "lng": 80.2707,
        },
        "Each One Plant One": {
            "description": (
                "Join United Way Chennai's green initiative — plant a sapling and commit to nurturing it. "
                "Help build a greener, cooler Chennai one tree at a time."
            ),
            "category": "Environment",
            "location": "Chennai",
            "lat": 13.0827, "lng": 80.2707,
        },
        "Beat Plastic": {
            "description": (
                "Volunteer to spread awareness about plastic pollution and take part in collection drives "
                "at Chennai beaches, parks, and public spaces. Registered NGO initiative."
            ),
            "category": "Environment",
            "location": "Chennai",
            "lat": 13.0492, "lng": 80.2831,
        },
        "Back2School Kits": {
            "description": (
                "Assemble and distribute school kits — notebooks, pencils, bags — to children from "
                "marginalised communities at the start of the academic year."
            ),
            "category": "Education",
            "location": "Chennai",
            "lat": 13.0827, "lng": 80.2707,
        },
        "Project Ink": {
            "description": (
                "Support literacy by helping children and adults practise reading and writing. "
                "Weekend sessions at community libraries and schools across Chennai."
            ),
            "category": "Education",
            "location": "Chennai",
            "lat": 13.0827, "lng": 80.2707,
            "source_url": "https://unitedwaychennai.org/volunteering/", # Specific section anchor if available
        },
    }

    # Headings on the page that are NOT volunteer opportunities
    _SKIP_HEADINGS = {"About", "Get Involved"}

    def scrape(self) -> List[Dict]:
        results = []
        try:
            resp = httpx.get(self.URL, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Strategy: Target the main content area to avoid footer/header junk
            # Most modern sites use <main>, #content, or specific article containers
            main_container = soup.find("main") or soup.find(id="content") or soup.find(class_="elementor-main-content") or soup
            
            # Pull all <h2> headings — these are the opportunity titles
            headings = [
                h2.get_text(strip=True)
                for h2 in main_container.find_all("h2")
                if h2.get_text(strip=True) not in self._SKIP_HEADINGS
            ]

            seen = set()
            for title in headings:
                if title in seen:
                    continue
                seen.add(title)

                details = self.OPPORTUNITY_DETAILS.get(title, {
                    "description": f"Volunteer opportunity from United Way Chennai: {title}.",
                    "category": "General",
                    "location": "Chennai",
                    "lat": 13.0827,
                    "lng": 80.2707,
                })

                results.append({
                    "title": title,
                    "description": details["description"],
                    "ngo_name": self.NAME,
                    "location": details["location"],
                    "lat": details["lat"],
                    "lng": details["lng"],
                    "category": details["category"],
                    "contact": "chennai@iVolunteer.in",
                    "source": "rss",
                    "source_url": details.get("source_url", self.URL),
                })

            self._log(f"{len(results)} opportunities scraped from {self.URL}")

        except Exception as exc:
            self._log(f"Failed to scrape {self.URL}: {exc}")

        return results


# ── Scraper 2: Rotary District 3232 RSS ───────────────────────────────────────

class RotaryFeedScraper(SiteScraper):
    """
    Fetches the Rotary India District 3232 RSS feed.
    Currently returns 0 entries (empty feed) but is ready for when they post.
    Source: https://rotary3232.org/feed/
    """
    NAME = "Rotary India District 3232"
    URL  = "https://rotary3232.org/feed/"

    def scrape(self) -> List[Dict]:
        results = []
        try:
            feed = feedparser.parse(self.URL)
            if not feed.entries:
                self._log(f"RSS feed returned 0 entries — feed may be empty.")
                return []

            for entry in feed.entries[:5]:
                raw_desc = entry.get("summary", entry.get("description", ""))
                results.append({
                    "title": strip_html(entry.get("title", "Untitled")),
                    "description": strip_html(raw_desc),
                    "ngo_name": self.NAME,
                    "location": "Chennai",
                    "lat": 13.0827,
                    "lng": 80.2707,
                    "category": "General",
                    "contact": None,
                    "source": "rss",
                    "source_url": entry.get("link", self.URL),
                })

            self._log(f"{len(results)} entries fetched.")

        except Exception as exc:
            self._log(f"RSS fetch failed: {exc}")

        return results


# ── Scraper 3: EFI (Environmentalist Foundation of India) ────────────────────

class EFIScraper(SiteScraper):
    """
    Scrapes EFI's volunteer page using contextual block chunking:
      1. Identifies discrete content blocks in the HTML (h2/h3-anchored sections).
      2. Sends each block individually to the LLM so context is clean.
      3. Resolves the best available link for each block (specific page > volunteer page > homepage).
    Source: https://indiaenvironment.org/volunteer/
    """
    NAME = "EFI (Environmentalist Foundation of India)"
    URL  = "https://indiaenvironment.org/volunteer/"

    # Keyword → most specific project page (used when no <a> found in block)
    PROJECT_LINKS: Dict[str, str] = {
        "lake":       "https://indiaenvironment.org/our-projects/",
        "pond":       "https://indiaenvironment.org/our-projects/",
        "clean":      "https://indiaenvironment.org/our-projects/",
        "beach":      "https://indiaenvironment.org/our-projects/",
        "ocean":      "https://indiaoceanproject.com/",
        "samudra":    "https://indiaoceanproject.com/",
        "plantation": "https://indiaenvironment.org/volunteer/",
        "wall":       "https://indiaenvironment.org/volunteer/",
        "internship": "https://forms.gle/ZZBF1BgAGiAeRah2A",
        "forest":     "https://indiaenvironment.org/our-projects/",
        "wildlife":   "https://indiaenvironment.org/our-projects/",
        "documentary":"https://indiaenvironment.org/volunteer/",
    }

    # Headings that are navigation / boilerplate — skip entirely
    _SKIP_HEADINGS = {
        "about efi", "contact", "home", "projects", "updates",
        "volunteer", "blog", "team", "environmentainment",
    }

    def _best_link_for_block(self, frag: BeautifulSoup, block_text: str) -> str:
        """
        Priority:
          1. First <a> inside the block whose href is a real absolute URL
             (not mailto: / tel: / # / cdn-cgi / bare homepage).
          2. Keyword match against PROJECT_LINKS.
          3. Default to the volunteer landing page (not the org homepage).
        """
        for a in frag.find_all("a", href=True):
            href = a["href"].strip()
            # Priority: Google Forms (registration), specialized project domains, or deep project paths
            if "forms.gle" in href or "docs.google.com/forms" in href:
                return href
            
            if href.startswith(("mailto:", "tel:", "#")):
                continue
            if not href.startswith("http"):
                href = "https://indiaenvironment.org/" + href.lstrip("/")
            
            # Skip bare homepage and generic volunteer page if we want deep links
            if href.rstrip("/") in (
                "https://indiaenvironment.org",
                "https://www.indiaenvironment.org",
                "https://indiaenvironment.org/volunteer",
                "https://indiaenvironment.org/volunteer/"
            ):
                continue
            if "cdn-cgi" in href:
                continue
            return href

        lower = block_text.lower()
        for keyword, link in self.PROJECT_LINKS.items():
            if keyword in lower:
                return link

        return self.URL  # volunteer page, not the org homepage

    def _split_into_blocks(self, soup: BeautifulSoup):
        """
        Walk the main content area and split on every h2 / h3 heading.
        Returns list of (heading_text, BeautifulSoup_fragment) tuples.
        """
        main = (
            soup.find("main")
            or soup.find(id="content")
            or soup.find(class_=re.compile(r"entry-content|page-content|site-content"))
            or soup
        )

        blocks = []
        current_heading = "General Volunteering"
        current_tags = []

        for tag in main.find_all(["h2", "h3", "p", "ul", "ol"], recursive=True):
            if tag.name in ("h2", "h3"):
                if current_tags:
                    frag = BeautifulSoup(
                        "".join(str(t) for t in current_tags), "lxml"
                    )
                    blocks.append((current_heading, frag))
                current_heading = tag.get_text(strip=True)
                current_tags = [tag]
            else:
                current_tags.append(tag)

        if current_tags:
            frag = BeautifulSoup(
                "".join(str(t) for t in current_tags), "lxml"
            )
            blocks.append((current_heading, frag))

        return blocks

    def scrape(self) -> List[Dict]:
        results = []
        try:
            resp = httpx.get(self.URL, timeout=20, follow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            blocks = self._split_into_blocks(soup)
            self._log(f"Found {len(blocks)} content blocks to process.")

            # ── Build one batched prompt across all relevant blocks ────────────
            # Each block is labelled with its canonical URL so the LLM can tag
            # each extracted item with the right source link.  This way we make
            # exactly ONE LLM call regardless of how many blocks exist.
            batched_sections: List[str] = []
            block_link_map: Dict[str, str] = {}   # heading -> best_link

            for heading, frag in blocks:
                if heading.lower().strip() in self._SKIP_HEADINGS:
                    self._log(f"  Skipping boilerplate block: '{heading}'")
                    continue

                block_text = frag.get_text(separator=" ", strip=True)
                if len(block_text) < 40:
                    continue

                best_link = self._best_link_for_block(frag, block_text)
                block_link_map[heading] = best_link
                self._log(f"  Block '{heading[:45]}' -> {best_link}")

                batched_sections.append(
                    f"[SECTION: {heading} | LINK: {best_link}]\n{block_text}"
                )

            if not batched_sections:
                self._log("No meaningful blocks found.")
                return results

            combined_text = "\n\n".join(batched_sections)

            # ── Single LLM call with the batched context ──────────────────────
            # Priority: Groq (Llama 3 8B) -> Gemini fallback
            groq_key = os.getenv("GROQ_API_KEY")
            gemini_key = os.getenv("GEMINI_API_KEY")

            prompt = (
                "You are extracting volunteering opportunities from NGO website sections.\n"
                "Each section is marked [SECTION: <heading> | LINK: <url>].\n"
                "Rules:\n"
                "  1. Return ONLY a JSON array of objects. Each object must have:\n"
                "       title       - specific activity name (e.g. 'Lake Clean-up', 'Wall Painting')\n"
                "       description - 1-3 sentence summary\n"
                "       category    - one of: Environment, Education, Health, Disaster Relief, Elder Care, General\n"
                "       source_url  - copy the LINK value from the [SECTION] header\n"
                "  2. DO NOT extract items where the title is a contact method.\n"
                "  3. If a section has no genuine activity, skip it — do NOT invent items.\n\n"
                f"SECTIONS:\n{combined_text}"
            )

            results_list = []
            
            # Try Groq
            if groq_key:
                try:
                    client = Groq(api_key=groq_key)
                    llm_wait(label="EFIScraper.scrape batch", provider="groq")
                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama-3.1-8b-instant",
                        response_format={"type": "json_object"},
                    )
                    items = json.loads(chat_completion.choices[0].message.content)
                    if isinstance(items, dict):
                        for k, v in items.items():
                            if isinstance(v, list):
                                results_list = v
                                break
                    elif isinstance(items, list):
                        results_list = items
                except Exception as exc:
                    print(f"[EFIScraper] Groq failed: {exc}")

            # Try Gemini Fallback
            if not results_list and gemini_key:
                try:
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel("gemini-2.0-flash")
                    llm_wait(label="EFIScraper.scrape batch", provider="gemini")
                    response = model.generate_content(
                        prompt,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    results_list = json.loads(response.text)
                except Exception as exc:
                    print(f"[EFIScraper] Gemini fallback failed: {exc}")

            if not isinstance(results_list, list):
                return results

            seen_titles: set = set()
            for item in results_list:
                title = item.get("title", "").strip()
                if not title or _CONTACT_TITLE_PATTERN.match(title):
                    continue
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                results.append({
                    "title":       title,
                    "description": item.get("description", ""),
                    "ngo_name":    self.NAME,
                    "location":    "Chennai",
                    "lat":         13.0827,
                    "lng":         80.2707,
                    "category":    item.get("category", "Environment"),
                    "contact":     "arun@indiaenvironment.org",
                    "source":      "rss",
                    "source_url":  item.get("source_url", self.URL),
                })

            self._log(f"{len(results)} initiatives extracted via single batched LLM call.")
        except Exception as exc:
            self._log(f"Scrape failed: {exc}")
        return results




# ── Scraper 4: Thuvakkam ───────────────────────────────────────────────────────

class ThuvakkamScraper(SiteScraper):
    """
    Scrapes Thuvakkam's active project landing pages.
    Source: https://thuvakkam.org/
    """
    NAME = "Thuvakkam"
    URL  = "https://thuvakkam.org/"
    
    # Core project categories derived from research
    PROJECTS = [
        {"title": "Afforestation", "path": "afforestation/", "category": "Environment"},
        {"title": "Project Blue Zone", "path": "project-blue-zone/", "category": "Environment"},
        {"title": "Clean and Color", "path": "clean-and-color/", "category": "Arts & Culture"},
        {"title": "Karka Kasadara", "path": "karka-kasadara/", "category": "Education"},
    ]

    def scrape(self) -> List[Dict]:
        results = []
        for proj in self.PROJECTS:
            try:
                full_url = f"{self.URL}{proj['path']}"
                resp = httpx.get(full_url, timeout=15, follow_redirects=True)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, "lxml")
                # Extract main description (usually first couple of <p> tags in entry-content or similar)
                content = soup.find(class_=re.compile("content|entry|description"))
                if content:
                    ps = content.find_all("p")
                    desc = " ".join([p.get_text(strip=True) for p in ps[:3]])
                else:
                    desc = f"Join Thuvakkam's {proj['title']} initiative in Chennai."

                results.append({
                    "title": proj["title"],
                    "description": strip_html(desc),
                    "ngo_name": self.NAME,
                    "location": "Chennai",
                    "lat": 13.0827, "lng": 80.2707,
                    "category": proj["category"],
                    "contact": "info@thuvakkam.org",
                    "source": "rss",
                    "source_url": full_url,
                })
            except Exception as exc:
                self._log(f"Failed to scrape project {proj['title']}: {exc}")
        
        self._log(f"{len(results)} projects scraped.")
        return results


# ── Plugin Registry ───────────────────────────────────────────────────────────
# To add a new source: write a SiteScraper subclass and add one line here.

SITE_SCRAPERS: List[SiteScraper] = [
    UnitedWayChennaiScraper(),
    EFIScraper(),
    ThuvakkamScraper(),
    RotaryFeedScraper(),
    # IVolunteerScraper(),   ← future: needs Playwright for JS rendering
]


# ── Simulated Social Media Posts (MVP Mock) ───────────────────────────────────
MOCK_SOCIAL_POSTS = [
    {
        "title": "Tree Plantation Drive — Anna Nagar",
        "description": "Volunteer with Chennai Volunteers this Sunday for a tree plantation drive at Anna Nagar. Community service for a greener Chennai. Registered NGO. All welcome!",
        "ngo_name": "Chennai Volunteers",
        "location": "Anna Nagar, Chennai",
        "lat": 13.0900, "lng": 80.2100,
        "category": "Environment",
        "contact": "+91 98400 00001",
        "source": "social",
    },
    {
        "title": "Blood Donation Camp",
        "description": "Chennai Red Cross Society urgently needs blood donors. Type O+ and B+ critically needed. Walk-in accepted at Government General Hospital.",
        "ngo_name": "Red Cross Society",
        "location": "Government General Hospital, Chennai",
        "lat": 13.0618, "lng": 80.2785,
        "category": "Health",
        "contact": "+91 98400 00002",
        "source": "social",
    },
    {
        "title": "SCAM ALERT TEST: Send UPI to register",
        "description": "ACT NOW! Pay ₹1000 registration fee via UPI. Only 3 spots left. Earn money while volunteering. Work from home. Guaranteed reward!",
        "ngo_name": "QuickVolunteer",
        "location": "Online",
        "lat": 13.0827, "lng": 80.2707,
        "category": "General",
        "contact": "unknown",
        "source": "social",
    },
    {
        "title": "Teach English to Kids — Vyasarpadi",
        "description": "Join our weekend teaching program. Help underprivileged children learn English and basic math. Every Saturday 9am–12pm. Rotary Club initiative.",
        "ngo_name": "Rotary Club Chennai",
        "location": "Vyasarpadi, Chennai",
        "lat": 13.1147, "lng": 80.2564,
        "category": "Education",
        "contact": "+91 98400 00003",
        "source": "social",
    },
    {
        "title": "Flood Relief Support — Tambaram",
        "description": "Team Everest is coordinating flood relief in Tambaram. Volunteers needed to distribute food packets and essential supplies to affected families.",
        "ngo_name": "Team Everest",
        "location": "Tambaram, Chennai",
        "lat": 12.9249, "lng": 80.1000,
        "category": "Disaster Relief",
        "contact": "+91 98400 00004",
        "source": "social",
    },
    {
        "title": "Elderly Care Visits — Adyar",
        "description": "Spend a few hours with the elderly at Dignity Foundation. Share stories, play games, or just listen. Registered NGO. ISO certified.",
        "ngo_name": "Dignity Foundation",
        "location": "Adyar, Chennai",
        "lat": 13.0067, "lng": 80.2573,
        "category": "Elder Care",
        "contact": "+91 98400 00005",
        "source": "social",
    },
    {
        "title": "Marina Beach Cleanup",
        "description": "Monthly cleanup drive at Marina Beach. Join Team Everest volunteers. Gloves and bags provided. Registered NGO - Government approved.",
        "ngo_name": "Team Everest",
        "location": "Marina Beach, Chennai",
        "lat": 13.0492, "lng": 80.2831,
        "category": "Environment",
        "contact": "+91 98400 00006",
        "source": "social",
    },
    {
        "title": "Suspicious Volunteer Opportunity",
        "description": "Earn money as a volunteer! Get paid ₹2000 per day. No experience needed. Winners selected daily. Click bit.ly/volunteer123 to sign up now!",
        "ngo_name": "EasyVolunteer",
        "location": "Online",
        "lat": 13.0827, "lng": 80.2707,
        "category": "General",
        "contact": "unknown",
        "source": "social",
        "source_url": "bit.ly/volunteer123",
    },
]


# ── Trust Engine pass-through ─────────────────────────────────────────────────

def process_opportunities(raw_items: List[Dict]) -> List[Dict]:
    """Run each raw opportunity through the Scam Detector and enrich with trust score."""
    processed = []
    
    # Junk filter keywords — any title containing these (case-insensitive) is skipped
    JUNK_KEYWORDS = [
        # Boilerplate / legal
        'Terms', 'Copyright', 'Rights Reserved', 'Hello world', 'Fill the form',
        'All Rights Reserved', 'Privacy Policy', 'Cookie Policy',
        # Contact pollution (LLM sometimes picks up bold contact fields)
        'Email:', 'E-mail', 'Phone:', 'Contact Us', 'Apply for Job',
        # Pay-to-volunteer / scam signals
        'Pay ', 'Earn Money', 'Get Paid', 'Registration Fee', 'SCAM ALERT',
        'URGENT:', 'Limited Spots',
    ]

    for item in raw_items:
        title = item.get("title", "")
        desc = item.get("description", "")

        # 1a. Skip if a junk keyword is in the title
        if any(kw.lower() in title.lower() for kw in JUNK_KEYWORDS):
            continue

        # 1b. Skip if the title matches a bare contact-method pattern
        if _CONTACT_TITLE_PATTERN.match(title.strip()):
            continue


        # 2. Skip if title/description is too short after stripping
        clean_title = strip_html(title)
        clean_desc = strip_html(desc)
        
        if len(clean_title) < 3 or len(clean_desc) < 5:
            continue

        score, status, flags, reasoning = detect_scam(
            title=clean_title,
            description=clean_desc,
            ngo_name=item["ngo_name"],
            source=item.get("source", "manual"),
            source_url=item.get("source_url", ""),
        )
        processed.append({
            **item,
            "title": clean_title,
            "description": clean_desc,
            "trust_score": score,
            "status": status,
            "trust_reasoning": reasoning,
            "_flags": flags,   # internal only, not stored in DB
        })
    return processed


# ── Main entry point ──────────────────────────────────────────────────────────

def run_scraper() -> List[Dict]:
    """
    Main entry point called by scheduler.py.
    Loops through SITE_SCRAPERS registry + mock data, returns processed opportunities.
    """
    print("[SCRAPER] Starting VeriServe data collection...")
    all_raw: List[Dict] = []

    # 1. Plugin scrapers
    for scraper in SITE_SCRAPERS:
        items = scraper.scrape()
        all_raw.extend(items)
        print(f"[SCRAPER] {scraper.NAME}: {len(items)} items")

    # 2. Mock social media data
    all_raw.extend(MOCK_SOCIAL_POSTS)
    print(f"[SCRAPER] Mock social: {len(MOCK_SOCIAL_POSTS)} items loaded")

    # 3. Process through Trust Engine
    processed = process_opportunities(all_raw)
    verified = [p for p in processed if p["status"] == "verified"]
    review   = [p for p in processed if p["status"] == "needs_review"]
    flagged  = [p for p in processed if p["status"] == "flagged"]

    print(f"\n[SCRAPER] Results:")
    print(f"  Verified     : {len(verified)}")
    print(f"  Needs Review : {len(review)}")
    print(f"  Flagged      : {len(flagged)}")

    return processed


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    results = run_scraper()
    print("\n[SCRAPER] All Processed Opportunities:")
    for r in results:
        icon = {"verified": "[V]", "needs_review": "[?]", "flagged": "[X]"}.get(r["status"], "[ ]")
        print(f"  {icon} [{r['trust_score']:3d}] [{r['source'].upper():6}] {r['title'][:55]}")
