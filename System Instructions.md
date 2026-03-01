Project Name: VeriServe Chennai

Version: 1.0 (MVP)

## Project Overview
Build a Verified Volunteering Aggregator for the Chennai area. The application pulls real-time volunteering opportunities from social media and official NGO sites, processes them through an AI "Trust Layer" to filter scams, and notifies users of high-priority needs.

## Navigation Structure
### Top Navigation Tabs
Feed (Home): A chronological list of verified opportunities.

Map View: Interactive map of Chennai showing "Help Needed" pins.

My Impact: Personal dashboard showing hours volunteered and badges earned.

Verify Center: A "community-review" queue where users can flag or confirm new posts.

NGO Directory: A list of pre-vetted, registered organizations (e.g., Team Everest, Chennai Volunteers).

### Core Logic: The "Trust Engine"
Scraper Input: Pulls data from Instagram (#ChennaiVolunteers), X (Twitter), and NGO RSS feeds.

AI Classifier: Checks for "Scam Red Flags" (requests for money, extreme urgency, unverified links).

Trust Score (0-100): * 90+: Green (Official NGO, Verified).

50-89: Yellow (New post, Needs Community Review).

<50: Red (Hidden from public feed).