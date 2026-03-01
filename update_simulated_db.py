import sqlite3
import os

db_path = os.path.join('backend', 'veriserve.db')

def update_db():
    print(f"--- Updating VeriServe DB with simulated reasoning ---")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Update beach cleanups
        cursor.execute("""
            UPDATE opportunities 
            SET trust_reasoning = '(AI) Highly safe: This is a monthly cleanup drive at Marina Beach organized by a registered NGO (Team Everest).'
            WHERE title LIKE '%Beach%'
        """)
        
        # 2. Update a "needs_review" one
        cursor.execute("""
            UPDATE opportunities 
            SET trust_reasoning = '(AI) Needs Review: The description provides a UPI ID for registration, which is a potential red flag.'
            WHERE trust_score BETWEEN 50 AND 89
        """)
        
        # 3. Update flagged ones
        cursor.execute("""
            UPDATE opportunities 
            SET trust_reasoning = '(Rule Engine) Scam Detected: Post specifies a payment fee and uses extreme urgency signals.'
            WHERE trust_score < 45
        """)
        
        # Set all others
        cursor.execute("UPDATE opportunities SET trust_reasoning = 'Rule engine: Assessment completed.' WHERE trust_reasoning IS NULL;")
        
        conn.commit()
        print(f"Updated {conn.total_changes} rows.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_db()
