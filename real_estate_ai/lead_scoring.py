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
        score += 25

    if lead_data.get("mortgage_status") == "approved":
        score += 20

    timeframe = lead_data.get("timeframe")
    if timeframe == "1 month":
        score += 30
    elif timeframe == "3 months":
        score += 15

    budget = lead_data.get("budget", 0)
    if budget > 1_500_000:
        score += 15

    message = lead_data.get("message", "").lower()
    if "urgent" in message:
        score += 10

    # Classification
    if score >= 70:
        status = "HOT"
        action = "Call within 10 minutes"
    elif score >= 40:
        status = "WARM"
        action = "Send matching listings"
    else:
        status = "COLD"
        action = "Add to long-term follow-up"

    # Close probability
    probability = min(score * 1.2, 95)

    return {
        "score": score,
        "status": status,
        "probability": probability,
        "action": action
    }
