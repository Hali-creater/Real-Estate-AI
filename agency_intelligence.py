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

def discover_agencies(query):
    """
    Module 1: Lead Discovery
    Scrapes Google search results for the given query.
    Targeting Zillow or Realtor.com profiles as per the prompt.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    # Append site restriction if not present
    if "site:" not in query:
        query = f"site:zillow.com {query}"

    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

    results = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Google's current structure for organic results
        for g in soup.select('.g'):
            anchor = g.select_one('a')
            title_el = g.select_one('h3')
            snippet_el = g.select_one('.VwiC3b') # Common snippet class

            if anchor and title_el:
                link = anchor['href']
                title = title_el.get_text()
                snippet = snippet_el.get_text() if snippet_el else ""

                # Basic cleaning of Zillow/Realtor titles
                clean_title = title.split('|')[0].split('-')[0].strip()

                results.append({
                    "agency_name": clean_title,
                    "website": link,
                    "snippet": snippet,
                    "city": query.replace("site:zillow.com", "").replace("site:realtor.com", "").strip()
                })
    except Exception as e:
        print(f"Search error: {e}")

    return results

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

    # Strength indicators (Consultative/Data-driven)
    indicators = str(data).lower()
    if any(kw in indicators for kw in ["premier", "elite", "luxury", "international", "commercial"]):
        base_score += 1

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
    Module 2: Scrape homepage text and metadata using BeautifulSoup.
    """
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Enterprise Intelligence Bot)"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract Meta Tags
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_desc = meta_desc["content"] if meta_desc else ""

        title = soup.title.string if soup.title else ""

        # Remove script and style elements
        for script in soup(["script", "style", "header", "footer", "nav"]):
            script.decompose()

        text = soup.get_text(separator=' ')
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        main_text = '\n'.join(chunk for chunk in chunks if chunk)

        combined_content = f"Title: {title}\nDescription: {meta_desc}\n\nContent:\n{main_text}"

        return combined_content[:6000] # Increased limit for better intelligence
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def analyze_website_with_gpt(homepage_text, agency_name):
    """
    Module 2: Website Analysis using GPT (or fallback)
    """
    prompt = f"""
    You are an Enterprise Real Estate Lead Intelligence AI built for the USA market.
    You are not a chatbot. You are an Enterprise Business Intelligence Engine.
    Analyzing website for agency: '{agency_name}'.

    Based on the provided homepage content:
    {homepage_text}

    1. Identify:
       - Primary market (city/state)
       - Niche (luxury, commercial, residential, rental, etc.)
       - Target audience
       - Brand positioning
       - Unique selling proposition

    2. Identify weaknesses in their digital sales infrastructure:
       - No automation mentioned
       - No instant response system
       - No chatbot
       - Weak lead capture
       - No SMS follow-up
       - Manual contact forms

    3. Identify business opportunities where "AI Real Estate Sales Assistant Infrastructure" can improve:
       - Speed to lead
       - Lead qualification
       - 24/7 response
       - Follow-up automation
       - Conversion rate

    Your tone must be professional, data-driven, and consultative.
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

    # Fallback / Mock Analysis (Professional Consultative Tone)
    return {
        "market": "US Regional Market",
        "niche": "High-End Residential",
        "target_audience": "High-intent Home Buyers and Sellers",
        "positioning": "Established Local Real Estate Authority",
        "usp": "Personalized client-centric approach combined with local market expertise",
        "weaknesses": ["Manual lead qualification workflows", "Limited 24/7 automated engagement systems", "No instant SMS response infrastructure"],
        "opportunities": ["Implementation of AI Sales Assistant Infrastructure", "Optimization of Speed-to-Lead metrics", "24/7 automated lead qualification"]
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
    You are an Enterprise Real Estate Lead Intelligence AI.
    Generate a highly personalized enterprise outreach email for {agency_name}.

    Rules:
    - Tone: Professional, confident, consultative, NOT spammy
    - Position product as: "AI Real Estate Sales Assistant Infrastructure"
    - Avoid hype language
    - Be consultative
    - Show deep understanding of their business strengths and gaps

    Details:
    - Agency: {agency_name}
    - City: {city}
    - Niche: {niche}
    - Tier: {qualification['tier']}
    - Identified Weaknesses: {', '.join(analysis.get('weaknesses', []))}
    - Identified Opportunities: {', '.join(analysis.get('opportunities', []))}

    Email Structure:
    1. Custom opening referencing their city, niche, and specific team strength.
    2. Identify a real business gap from the website analysis.
    3. Introduce solution as: “AI Real Estate Sales Assistant Infrastructure”.
    4. Focus on: Speed-to-lead automation, AI lead qualification, 24/7 response, SMS + Web automation, and conversion increase.
    5. CTA: 15-minute demo.
    6. Include professional CAN-SPAM compliance language.

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

    # Fallback Template (Enterprise Consultative Style)
    subject = f"Infrastructure Optimization for {agency_name} | {city}"
    body = f"""Hi {agency_data.get('owner_name', 'Team')},

I’ve been analyzing {agency_name}’s market positioning in {city} and was impressed by your team’s focus on the {niche} sector.

In evaluating your digital sales infrastructure, I identified a significant opportunity to enhance your conversion metrics. While your brand presence is strong, the transition from lead capture to qualification currently appears to rely on manual workflows, which can impact your Speed-to-Lead efficiency.

We specialize in deploying "AI Real Estate Sales Assistant Infrastructure" for premium brokerages. Our enterprise-grade system handles:
- 24/7 Intelligent Lead Qualification (SMS & Web)
- Instant Speed-to-Lead Automation (Under 60 seconds)
- Automated Appointment Scheduling for your top agents

Given {agency_name}'s market strength, I believe this infrastructure could significantly scale your output without increasing overhead.

Do you have 15 minutes next week for a brief consultative demo?

Best regards,

[Your Name]
Enterprise Consultant
SpeedToLead AI

---
SpeedToLead AI: 123 Enterprise Way, NY.
Reply STOP to unsubscribe. [CAN-SPAM Compliant]
"""
    return {"subject": subject, "body": body}
