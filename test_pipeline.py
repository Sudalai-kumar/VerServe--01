import sys
import os

# Add backend to path so we can import modules
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from scheduler import scrape_and_store
from database import SessionLocal
import models

def test_full_pipeline():
    print("=== VeriServe Pipeine Test (Groq Integration) ===")
    
    # 1. Run the scraper + DB storage
    print("\n[1/3] Running scrape_and_store()...")
    results = scrape_and_store()
    print(f"      Results: {results}")

    # 2. Check the DB for the latest reasoning
    print("\n[2/3] Verifying LLM reasoning in Database...")
    db = SessionLocal()
    try:
        # Get the 5 most recent opportunities
        recent_ops = db.query(models.Opportunity).order_by(models.Opportunity.id.desc()).limit(5).all()
        
        if not recent_ops:
            print("      No opportunities found in DB.")
        else:
            for op in recent_ops:
                provider = "Groq" if "Groq" in (op.trust_reasoning or "") else ("Gemini" if "Gemini" in (op.trust_reasoning or "") else "Rules/Other")
                print(f"      - [{op.trust_score}] {op.title[:40]}... | Provider: {provider}")
                print(f"        Reasoning: {op.trust_reasoning}")
                print("-" * 40)
    finally:
        db.close()

    print("\n[3/3] Test complete.")

if __name__ == "__main__":
    test_full_pipeline()
