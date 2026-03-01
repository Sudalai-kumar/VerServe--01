import sys
import os
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from scraper.scam_detector import detect_scam

def test_single_call():
    print("--- VeriServe Gemini Health Check ---")
    load_dotenv('backend/.env')
    
    title = "Beach Cleanup Drive"
    description = "Join us for a manual beach cleanup at Marina Beach this weekend. Organized by Chennai Volunteers."
    ngo_name = "Chennai Volunteers"
    
    try:
        score, status, flags, reasoning = detect_scam(title, description, ngo_name)
        print(f"Status: SUCCESS")
        print(f"Score: {score}")
        print(f"Reasoning: {reasoning}")
    except Exception as e:
        print(f"Status: FAILED")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_single_call()
