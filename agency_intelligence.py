import requests
from bs4 import BeautifulSoup
import os
import json
import re
from openai import OpenAI

# Initialize OpenAI client (will use OPENAI_API_KEY from env)
client = None
if os.environ.get("OPENAI_API_KEY"):
    client = OpenAI()

def clean_and_score_agency(data):
    """
    Module 1: Lead Extraction & Scoring
    Cleans raw data and assigns initial classification and score (1-10).
    """
    # Standardize data
    agency_name = data.get("agency_name", "Unknown Agency")
    if agency_name is None:
        agency_name = "Unknown Agency"
    agency_name = str(agency_name).strip()

    try:
        listings = int(data.get("num_listings", 0))
    except (ValueError, TypeError):
        listings = 0

    try:
        rating = float(data.get("google_rating", 0))
    except (ValueError, TypeError):
        rating = 0.0

    # Classification logic
    if listings >= 50:
        classification = "Large Brokerage"
        base_score = 8
    elif "Luxury" in agency_name or "Premium" in agency_name:
        classification = "Luxury Brokerage"
        base_score = 9
    elif listings >= 15:
        classification = "Small Team"
        base_score = 6
    else:
        classification = "Solo Agent"
        base_score = 4

    # Adjustment based on rating
    if rating >= 4.5:
        base_score += 1
    elif rating > 0 and rating < 3.5:
        base_score -= 1

    # Cap score
    score = max(1, min(10, base_score))

    strength_summary = f"{classification} with {listings} listings and {rating} rating."
    growth_opp = "High potential for AI speed-to-lead automation." if score > 5 else "Nurture for future growth."

    return {
        "agency_name": agency_name,
        "classification": classification,
        "score": score,
        "strength_summary": strength_summary,
        "growth_opportunity_summary": growth_opp
    }

def scrape_homepage(url):
    """
    Module 2: Scrape homepage text using BeautifulSoup.
    """
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=' ')
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text[:5000] # Limit to 5000 chars for LLM
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def analyze_website_with_gpt(homepage_text, agency_name):
    """
    Module 2: Website Analysis using GPT (or fallback)
    """
    prompt = f"""
    You are analyzing a US real estate agency website for '{agency_name}'.

    Based on the provided homepage content:
    {homepage_text}

    1. Identify:
       - Primary market (city/state)
       - Niche (luxury, commercial, residential, rental, etc.)
       - Target audience
       - Brand positioning
       - Unique selling proposition

    2. Identify weaknesses:
       - No automation mentioned
       - No instant response system
       - No chatbot
       - Weak lead capture
       - No SMS follow-up
       - Manual contact forms

    3. Identify business opportunities where AI automation can improve:
       - Speed to lead
       - Lead qualification
       - 24/7 response
       - Follow-up automation
       - Conversion rate

    Output a structured JSON response with keys:
    'market', 'niche', 'target_audience', 'positioning', 'usp', 'weaknesses', 'opportunities'.
    """

    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"GPT Error: {e}")

    # Fallback / Mock Analysis
    return {
        "market": "US Market",
        "niche": "Residential",
        "target_audience": "Home Buyers/Sellers",
        "positioning": "Professional Agency",
        "usp": "Local expertise",
        "weaknesses": ["Manual contact forms", "No 24/7 response"],
        "opportunities": ["AI Lead Qualification", "Instant SMS Follow-up"]
    }

def qualify_agency(agency_data, analysis):
    """
    Module 3: Qualification Engine
    Classifies lead into Tier 1, 2, or 3.
    """
    listings = agency_data.get("num_listings", 0)

    if listings >= 50:
        tier = "Tier 1 – Enterprise"
        explanation = "Large inventory and team size indicate high volume and need for enterprise infrastructure."
        budget_capability = "High"
    elif listings >= 15:
        tier = "Tier 2 – Growth Agency"
        explanation = "Growing agency that needs automation to scale without increasing headcount."
        budget_capability = "Medium"
    else:
        tier = "Tier 3 – Solo Agent"
        explanation = "Individual agent focusing on personal brand, ideal for simple automated assistance."
        budget_capability = "Low"

    return {
        "tier": tier,
        "explanation": explanation,
        "budget_capability": budget_capability,
        "ideal_for_premium_ai": "Yes" if listings >= 15 else "Maybe"
    }

def generate_outreach_email(agency_data, analysis, qualification):
    """
    Module 4: Premium Personalized Outreach Generator
    """
    agency_name = agency_data.get("agency_name")
    city = agency_data.get("city", "your area")
    niche = analysis.get("niche", "Real Estate")

    prompt = f"""
    Generate a highly personalized enterprise outreach email for {agency_name}.

    Details:
    - Agency: {agency_name}
    - City: {city}
    - Niche: {niche}
    - Tier: {qualification['tier']}
    - Weaknesses found: {', '.join(analysis.get('weaknesses', []))}

    Rules:
    - Tone: Professional, confident, not spammy
    - Position product as AI Sales Infrastructure
    - Avoid hype language
    - Be consultative
    - Show understanding of their business
    - Include Custom opening referencing city, niche, and team strength
    - Identify a real business gap (from weaknesses)
    - Introduce solution as: “AI Real Estate Sales Assistant Infrastructure”
    - Focus on: Speed-to-lead, AI qualification, 24/7 response, SMS + Web automation, Conversion increase
    - CTA: 15-minute demo
    - Include CAN-SPAM compliance language (Address, Unsubscribe)

    Output Subject Line and Email Body.
    """

    if client:
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            # Simple parsing of Subject and Body
            if "Subject:" in content:
                parts = content.split("Subject:", 1)[1].split("\n", 1)
                subject = parts[0].strip()
                body = parts[1].strip() if len(parts) > 1 else content
            else:
                subject = f"Scaling {agency_name} with AI Sales Infrastructure"
                body = content

            return {"subject": subject, "body": body}
        except Exception as e:
            print(f"GPT Error generating email: {e}")

    # Fallback Template
    subject = f"Optimizing Speed-to-Lead for {agency_name} in {city}"
    body = f"""Hi {agency_data.get('owner_name', 'Team')},

I’ve been following {agency_name}’s work in {city} and was impressed by your {niche} focus.

In reviewing your current digital presence, I noticed that while you have a strong brand, there might be an opportunity to further capture and qualify leads instantly. Most agencies in your tier lose 40% of leads due to response delays.

We provide “AI Real Estate Sales Assistant Infrastructure” designed specifically for agencies like yours. Our system ensures:
- 24/7 Instant response via SMS and Web
- Automated lead qualification
- Direct appointment booking into your calendar

I’d love to show you how this could work for your team. Do you have 15 minutes for a brief demo next Tuesday?

Best regards,

[Your Name]
SpeedToLead AI Team

---
123 AI Way, San Francisco, CA
To unsubscribe, reply STOP or click here.
"""
    return {"subject": subject, "body": body}
