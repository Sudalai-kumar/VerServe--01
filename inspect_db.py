import sqlite3
import os

db_path = os.path.join('backend', 'veriserve.db')

def inspect_db():
    print(f"--- VeriServe DB Check: {db_path} ---")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table schema
        cursor.execute("PRAGMA table_info(opportunities);")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
        # Check content
        cursor.execute("SELECT title, trust_score, source_url FROM opportunities WHERE source != 'manual' LIMIT 15;")
        rows = cursor.fetchall()
        print("\nScraped Opportunities & Links:")
        if not rows:
            print("  (None found)")
        else:
            for title, score, url in rows:
                print(f"  [{score}%] {title[:40]:<40} -> {url}")
                
        # Also check all rows with reasoning NULL to see if we need to re-run
        cursor.execute("SELECT COUNT(*) FROM opportunities WHERE trust_reasoning IS NULL;")
        null_count = cursor.fetchone()[0]
        print(f"\nTotal rows with trust_reasoning=NULL: {null_count}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
