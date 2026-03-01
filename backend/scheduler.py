"""
VeriServe Background Scheduler
================================
Uses APScheduler to run the scraper every 6 hours automatically.
- Deduplicates by (title, ngo_name) before inserting into DB
- Exposed to FastAPI via start_scheduler() / stop_scheduler()
- A manual trigger is also available via the scraper_admin router
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import SessionLocal
import models
from scraper.scraper import run_scraper

logger = logging.getLogger("veriserve.scheduler")

# Global scheduler instance (initialised once)
scheduler = BackgroundScheduler(timezone="Asia/Kolkata")


# ── Core DB-Writer ────────────────────────────────────────────────────────────

def scrape_and_store() -> dict:
    """
    Run the scraper, deduplicate against the DB, insert new opportunities.
    Returns a summary dict: {inserted, skipped, flagged}.
    """
    logger.info("[SCHEDULER] Starting scheduled scrape run...")
    db = SessionLocal()
    inserted = skipped = flagged = 0

    try:
        items = run_scraper()           # list of dicts with trust_score & status
        for item in items:
            # ── Deduplication ────────────────────────────────────────────────
            exists = (
                db.query(models.Opportunity)
                .filter_by(title=item["title"], ngo_name=item["ngo_name"])
                .first()
            )
            if exists:
                skipped += 1
                continue

            # Strip internal-only keys before storing
            clean = {k: v for k, v in item.items() if not k.startswith("_")}
            
            # Ensure source_url is absolute
            surl = clean.get("source_url")
            if surl and not surl.startswith("http"):
                # Default to IndiaEnvironment if it's been clipped or is relative
                if "indiaenvironment" in item.get("ngo_name", "").lower():
                    clean["source_url"] = "https://indiaenvironment.org/" + surl.lstrip("/")

            op = models.Opportunity(
                title=clean.get("title", "Untitled"),
                description=clean.get("description", ""),
                ngo_name=clean.get("ngo_name", "Unknown"),
                location=clean.get("location", "Chennai"),
                lat=clean.get("lat", 13.0827),
                lng=clean.get("lng", 80.2707),
                trust_score=clean.get("trust_score", 50),
                status=clean.get("status", "needs_review"),
                trust_reasoning=clean.get("trust_reasoning"),
                category=clean.get("category", "General"),
                contact=clean.get("contact"),
                source=clean.get("source", "scraper"),
                source_url=clean.get("source_url"),
            )
            db.add(op)
            inserted += 1
            if op.status == "flagged":
                flagged += 1

        db.commit()
        logger.info(
            f"[SCHEDULER] Done — inserted={inserted}, skipped={skipped}, flagged={flagged}"
        )

    except Exception as exc:
        db.rollback()
        logger.error(f"[SCHEDULER] Scrape run failed: {exc}", exc_info=True)
        raise
    finally:
        db.close()

    return {"inserted": inserted, "skipped": skipped, "flagged": flagged}


# ── Lifecycle helpers (called from main.py lifespan) ─────────────────────────

def start_scheduler():
    """Register the job and start the scheduler. Called on app startup."""
    scheduler.add_job(
        func=scrape_and_store,
        trigger=IntervalTrigger(hours=6),
        id="scrape_job",
        name="VeriServe Scraper — every 6 h",
        replace_existing=True,
        next_run_time=datetime.now(),   # run immediately on startup too
    )
    scheduler.start()
    logger.info("[SCHEDULER] APScheduler started. Next run: immediately, then every 6 hours.")


def stop_scheduler():
    """Gracefully shut down the scheduler. Called on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[SCHEDULER] APScheduler stopped.")
