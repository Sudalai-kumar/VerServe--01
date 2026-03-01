"""
Seed database with realistic Chennai volunteering data and NGO profiles.
Run once: python seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, SessionLocal
import models

models.Base.metadata.create_all(bind=engine)


NGOS = [
    {
        "name": "Team Everest",
        "description": "India's largest volunteering network dedicated to environmental conservation, disaster relief, and community upliftment. Active in Chennai since 2011.",
        "category": "Environment & Disaster Relief",
        "contact_email": "volunteer@teameverest.ngo",
        "contact_phone": "+91 98400 10001",
        "website": "https://teameverest.ngo",
        "address": "T. Nagar, Chennai, Tamil Nadu 600017",
        "logo_emoji": "⛰️",
        "founded_year": 2011,
        "volunteers_count": 12000,
    },
    {
        "name": "Chennai Volunteers",
        "description": "A platform that connects passionate volunteers with meaningful causes across Chennai. Focused on education, environment, and social welfare.",
        "category": "Community & Education",
        "contact_email": "hello@chennaivolunteers.org",
        "contact_phone": "+91 98400 10002",
        "website": "https://Chennai.com/en",
        "address": "Anna Nagar, Chennai, Tamil Nadu 600040",
        "logo_emoji": "🤝",
        "founded_year": 2014,
        "volunteers_count": 8500,
    },
    {
        "name": "Exnora International",
        "description": "Pioneer in civic activism for a better Chennai. Works on waste management, road safety, and urban cleanliness campaigns.",
        "category": "Civic & Environment",
        "contact_email": "exnora@gmail.com",
        "contact_phone": "+91 98400 10003",
        "website": "https://exnora.org",
        "address": "Nungambakkam, Chennai, Tamil Nadu 600034",
        "logo_emoji": "🌍",
        "founded_year": 1989,
        "volunteers_count": 3000,
    },
    {
        "name": "AID India",
        "description": "Works at the grassroots level to empower marginalized communities through education, health, and livelihoods. Government approved CSR partner.",
        "category": "Education & Health",
        "contact_email": "contact@aidindia.org",
        "contact_phone": "+91 98400 10004",
        "website": "https://aidindia.org",
        "address": "Mylapore, Chennai, Tamil Nadu 600004",
        "logo_emoji": "❤️",
        "founded_year": 2001,
        "volunteers_count": 5200,
    },
    {
        "name": "Rotary Club of Chennai",
        "description": "Part of Rotary International. Runs literacy programs, health camps, and vocational training across Chennai's underserved communities.",
        "category": "Health & Education",
        "contact_email": "rotarychennai@rotary.org",
        "contact_phone": "+91 98400 10005",
        "website": "https://rotary.org",
        "address": "Egmore, Chennai, Tamil Nadu 600008",
        "logo_emoji": "⚙️",
        "founded_year": 1920,
        "volunteers_count": 900,
    },
    {
        "name": "Dignity Foundation",
        "description": "Dedicated to enriching the lives of senior citizens in Chennai. Runs day-care programs, helplines, and companionship visits. ISO certified.",
        "category": "Elder Care",
        "contact_email": "dignityf@gmail.com",
        "contact_phone": "+91 98400 10006",
        "website": "https://dignityfoundation.com",
        "address": "Adyar, Chennai, Tamil Nadu 600020",
        "logo_emoji": "🕊️",
        "founded_year": 1995,
        "volunteers_count": 2100,
    },
]

OPPORTUNITIES = [
    {
        "title": "Marina Beach Monthly Cleanup",
        "description": "Join Team Everest for our flagship beach cleanup drive at Marina Beach. Gloves, bags, and refreshments provided. Registered NGO. Government approved. All are welcome!",
        "ngo_name": "Team Everest",
        "location": "Marina Beach, Chennai",
        "lat": 13.0492,
        "lng": 80.2831,
        "trust_score": 95,
        "status": "verified",
        "category": "Environment",
        "contact": "+91 98400 10001",
        "source": "rss",
    },
    {
        "title": "Flood Relief Distribution — Tambaram",
        "description": "Team Everest is coordinating flood relief operations in Tambaram. Volunteers needed to distribute food packets, water, and essential supplies to affected families. Registered NGO.",
        "ngo_name": "Team Everest",
        "location": "Tambaram, Chennai",
        "lat": 12.9249,
        "lng": 80.1000,
        "trust_score": 97,
        "status": "verified",
        "category": "Disaster Relief",
        "contact": "+91 98400 10001",
        "source": "rss",
    },
    {
        "title": "Weekend English Teaching — Vyasarpadi",
        "description": "Rotary Club runs a weekend English and Math teaching program for underprivileged children. Every Saturday 9am–12pm at the community center. No experience needed — just patience and compassion.",
        "ngo_name": "Rotary Club of Chennai",
        "location": "Vyasarpadi, Chennai",
        "lat": 13.1147,
        "lng": 80.2564,
        "trust_score": 91,
        "status": "verified",
        "category": "Education",
        "contact": "+91 98400 10005",
        "source": "rss",
    },
    {
        "title": "Tree Plantation Drive — Anna Nagar",
        "description": "Chennai Volunteers is organizing a tree plantation drive this Sunday. We'll be planting 500 saplings across Anna Nagar Park. Join us for a greener Chennai! CSR initiative with Green Chennai Mission.",
        "ngo_name": "Chennai Volunteers",
        "location": "Anna Nagar, Chennai",
        "lat": 13.0900,
        "lng": 80.2100,
        "trust_score": 93,
        "status": "verified",
        "category": "Environment",
        "contact": "+91 98400 10002",
        "source": "rss",
    },
    {
        "title": "Elderly Companionship Visits — Adyar",
        "description": "Dignity Foundation invites you to spend a few hours with senior citizens at our day-care centre. No special skills needed. Just bring your warmth! ISO certified organization.",
        "ngo_name": "Dignity Foundation",
        "location": "Adyar, Chennai",
        "lat": 13.0067,
        "lng": 80.2573,
        "trust_score": 92,
        "status": "verified",
        "category": "Elder Care",
        "contact": "+91 98400 10006",
        "source": "rss",
    },
    {
        "title": "Blood Donation Camp — Government General Hospital",
        "description": "Chennai Red Cross urgently needs blood donors. O+ and B+ are critically needed. Walk-ins welcome at Government General Hospital, Park Town.",
        "ngo_name": "Red Cross Society",
        "location": "Government General Hospital, Chennai",
        "lat": 13.0618,
        "lng": 80.2785,
        "trust_score": 78,
        "status": "needs_review",
        "category": "Health",
        "contact": "+91 98400 20001",
        "source": "social",
    },
    {
        "title": "Community Kitchen — Sowcarpet",
        "description": "A new initiative to provide free meals to daily wage workers. Volunteers needed for cooking, serving, and distribution. Urgent need this week due to increased footfall.",
        "ngo_name": "Chennai Cares Foundation",
        "location": "Sowcarpet, Chennai",
        "lat": 13.0895,
        "lng": 80.2834,
        "trust_score": 65,
        "status": "needs_review",
        "category": "Food & Nutrition",
        "contact": "+91 98400 20002",
        "source": "social",
    },
    {
        "title": "Digital Literacy Workshop — Tondiarpet",
        "description": "Teach basic smartphone and internet skills to elderly residents. 2-hour sessions on weekday evenings. Material provided. CSR initiative.",
        "ngo_name": "AID India",
        "location": "Tondiarpet, Chennai",
        "lat": 13.1201,
        "lng": 80.2933,
        "trust_score": 82,
        "status": "needs_review",
        "category": "Education",
        "contact": "+91 98400 10004",
        "source": "social",
    },
    {
        "title": "EARN MONEY: Get Paid ₹2000/Day to 'Volunteer'",
        "description": "Work from home! Earn money while helping. Guaranteed reward of ₹2000 per day. No experience needed. Winners selected daily. Send fee via UPI to register. Click bit.ly/scam777",
        "ngo_name": "QuickVolunteer Pro",
        "location": "Online",
        "lat": 13.0827,
        "lng": 80.2707,
        "trust_score": 5,
        "status": "flagged",
        "category": "General",
        "contact": "unknown",
        "source": "social",
        "source_url": "bit.ly/scam777",
    },
    {
        "title": "URGENT: Pay ₹500 Registration Fee — Limited Spots!",
        "description": "ACT NOW! Only 5 spots left. Pay ₹500 via UPI to confirm your slot. Last chance! Today only. Wire transfer also accepted. Get certified after payment.",
        "ngo_name": "VolunteerFast",
        "location": "Online",
        "lat": 13.0827,
        "lng": 80.2707,
        "trust_score": 3,
        "status": "flagged",
        "category": "General",
        "contact": "unknown",
        "source": "social",
    },
    {
        "title": "Waste Segregation Awareness Drive",
        "description": "Exnora International invites volunteers to visit apartments and educate residents about wet/dry waste segregation. Training provided. Half-day commitment.",
        "ngo_name": "Exnora International",
        "location": "Nungambakkam, Chennai",
        "lat": 13.0569,
        "lng": 80.2425,
        "trust_score": 88,
        "status": "needs_review",
        "category": "Environment",
        "contact": "+91 98400 10003",
        "source": "social",
    },
    {
        "title": "Women's Safety Workshop — Velachery",
        "description": "AID India is conducting a self-defence and safety awareness workshop for women. Free of charge. Government approved CSR initiative. Sessions every Wednesday evening.",
        "ngo_name": "AID India",
        "location": "Velachery, Chennai",
        "lat": 12.9815,
        "lng": 80.2176,
        "trust_score": 90,
        "status": "verified",
        "category": "Women Empowerment",
        "contact": "+91 98400 10004",
        "source": "rss",
    },
]


def seed():
    db = SessionLocal()
    try:
        # Clear existing
        db.query(models.NGO).delete()
        db.query(models.Opportunity).delete()
        db.commit()

        # Seed NGOs
        for ngo_data in NGOS:
            ngo = models.NGO(**ngo_data, verified=True)
            db.add(ngo)

        # Seed Opportunities
        for opp_data in OPPORTUNITIES:
            opp = models.Opportunity(**opp_data)
            db.add(opp)

        # Seed demo user impact
        demo_impact = models.UserImpact(
            user_id="demo_user",
            hours_volunteered=34.5,
            activities_count=8,
            verifications_count=12,
            badges='["First Responder","Community Seed","Trust Guardian","Green Hero"]',
        )
        db.add(demo_impact)

        db.commit()
        print(f"✅ Seeded {len(NGOS)} NGOs and {len(OPPORTUNITIES)} opportunities.")
        print("   Run: uvicorn main:app --reload --port 8000")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
