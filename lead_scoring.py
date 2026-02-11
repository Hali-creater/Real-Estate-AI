def calculate_lead_score(lead_data: dict):
    """
    Calculates lead score, status and close probability based on lead data.
    lead_data should contain:
    - cash_buyer (bool)
    - mortgage_status (str)
    - timeframe (str)
    - budget (float)
    - message (str)
    """
    score = 0

    if lead_data.get("cash_buyer"):
        score += 40

    if lead_data.get("mortgage_status") == "approved":
        score += 30

    timeframe = lead_data.get("timeframe")
    if timeframe == "Immediate":
        score += 30
    elif timeframe == "3 months":
        score += 15

    budget = lead_data.get("budget", 0)
    # US Market high value threshold often starts at $800k - $1M
    if budget >= 1_000_000:
        score += 20
    elif budget >= 500_000:
        score += 10

    message = lead_data.get("message", "").lower()
    if "urgent" in message:
        score += 10

    # US ROI Calculation (Conservative 2.5% commission)
    estimated_commission = budget * 0.025

    # Cap score at 100
    score = min(score, 100)

    # US Realtor Classification & Action
    if score >= 70:
        status = "HOT"
        action = "Call & Text Immediately. Book Appointment."
    elif score >= 35:
        status = "WARM"
        action = "Send matching listings. Enroll in SMS drip."
    else:
        status = "COLD"
        action = "Long-term nurture. Monthly email."

    # Close probability (Speed-to-lead factor)
    probability = min(score * 1.2, 95)

    return {
        "score": score,
        "status": status,
        "probability": probability,
        "action": action,
        "commission": estimated_commission
    }
