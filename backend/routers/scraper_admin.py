"""
Scraper Admin Router
====================
Exposes a manual trigger so the scraper can be kicked off on demand
without waiting for the 6-hour interval.
"""

from fastapi import APIRouter, HTTPException
from scheduler import scrape_and_store

router = APIRouter(prefix="/scraper", tags=["scraper"])


@router.post("/run", summary="Manually trigger a scrape run")
def trigger_scrape():
    """
    Trigger the VeriServe scraper immediately.
    Returns a summary of what was inserted, skipped, and flagged.
    """
    try:
        result = scrape_and_store()
        return {
            "status": "ok",
            "message": "Scrape run complete",
            **result,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(exc)}")


@router.get("/status", summary="Check scheduler status")
def scraper_status():
    """Returns whether the background scheduler is currently running."""
    from scheduler import scheduler
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time),
        })
    return {
        "scheduler_running": scheduler.running,
        "jobs": jobs,
    }
