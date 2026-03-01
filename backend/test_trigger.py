from scheduler import scrape_and_store
from database import SessionLocal
import models
import logging

# Enable logging to see what's happening
logging.basicConfig(level=logging.INFO)

def test_run():
    print("--- VeriServe Backend Test Run ---")
    
    # 1. Trigger the scraper and storage
    results = scrape_and_store()
    print(f"Scrape results: {results}")
    
    # 2. Verify some results
    db = SessionLocal()
    try:
        # Get latest 5
        ops = db.query(models.Opportunity).order_by(models.Opportunity.id.desc()).limit(5).all()
        for op in ops:
            print(f"ID: {op.id} | Score: {op.trust_score} | Title: {op.title[:30]}...")
            print(f"Reasoning: {op.trust_reasoning}")
            print("-" * 20)
    finally:
        db.close()

if __name__ == "__main__":
    test_run()
