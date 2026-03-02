import sys
import os
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import models
from database import SessionLocal, engine

# Clear and Recreate tables
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_p2p():
    db = SessionLocal()
    try:
        # 1. Create Users
        users_data = [
            {"email": "arun@test.com", "full_name": "Arun Kumar"},
            {"email": "priya@test.com", "full_name": "Priya Dharshini"},
            {"email": "deepak@test.com", "full_name": "Deepak Raj"},
            {"email": "kavitha@test.com", "full_name": "Kavitha S."},
        ]
        
        users = []
        print("👤 Creating users...")
        for u in users_data:
            user = models.User(
                email=u["email"],
                hashed_password=get_password_hash("password123"),
                full_name=u["full_name"]
            )
            db.add(user)
            db.flush()
            
            # Init impact
            impact = models.UserImpact(user_id=user.id, karma=100)
            db.add(impact)
            users.append(user)
            print(f"✅ Created: {u['full_name']}")

        # 2. Create Help Requests
        requests_data = [
            {
                "email": "arun@test.com",
                "title": "Need help moving a heavy refrigerator",
                "description": "I just bought a new fridge and need help moving it from the ground floor to the 2nd floor. It's quite heavy, so need at least two strong people.",
                "category": "Heavy Lifting",
                "lat": 13.0405, "lng": 80.2337, # T. Nagar
                "people_needed": 2,
                "location_name": "T. Nagar, Chennai"
            },
            {
                "email": "priya@test.com",
                "title": "Grocery pickup for elderly neighbor",
                "description": "My neighbor is 80 years old and can't go out in the heat. Need someone to pick up a few essential items from the local supermarket and deliver them.",
                "category": "Groceries",
                "lat": 13.0850, "lng": 80.2101, # Anna Nagar
                "people_needed": 1,
                "location_name": "Anna Nagar, Chennai"
            },
            {
                "email": "deepak@test.com",
                "title": "Basic laptop troubleshooting",
                "description": "My laptop is running very slow and I'm not very tech-savvy. Hoping someone could spend 30 minutes to help me clean up some files.",
                "category": "Technical",
                "lat": 13.0067, "lng": 80.2574, # Adyar
                "people_needed": 1,
                "location_name": "Adyar, Chennai"
            },
            {
                "email": "kavitha@test.com",
                "title": "Planting trees in community park",
                "description": "Got 10 saplings to plant in our neighborhood park. Need a hand with the digging!",
                "category": "Environment",
                "lat": 13.1147, "lng": 80.2564, # Vyasarpadi
                "people_needed": 3,
                "location_name": "Vyasarpadi, Chennai"
            },
            {
                "email": "arun@test.com",
                "title": "Reading to visually impaired student",
                "description": "Looking for a volunteer to spend an hour reading textbooks to a student preparing for exams.",
                "category": "Education",
                "lat": 13.0569, "lng": 80.2425, # Nungambakkam
                "people_needed": 1,
                "location_name": "Nungambakkam, Chennai"
            }
        ]

        print("\n🤝 Creating help requests...")
        for r in requests_data:
            owner = next(u for u in users if u.email == r["email"])
            req = models.HelpRequest(
                user_id=owner.id,
                title=r["title"],
                description=r["description"],
                category=r["category"],
                lat=r["lat"],
                lng=r["lng"],
                people_needed=r["people_needed"],
                location_name=r["location_name"],
                status="seeking",
                trust_score=90,
                trust_reasoning="Manual seed data - verified."
            )
            db.add(req)
            print(f"✅ Created: {r['title']}")

        db.commit()
        print("\n✨ P2P Fresh Start Seeding Complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_p2p()
