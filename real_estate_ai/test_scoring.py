from lead_scoring import calculate_lead_score

def test_hot_lead():
    lead_data = {
        "cash_buyer": True,
        "mortgage_status": "approved",
        "timeframe": "1 month",
        "budget": 2000000,
        "message": "I am urgent"
    }
    result = calculate_lead_score(lead_data)
    print(f"HOT Test Result: {result}")
    assert result['status'] == "HOT"
    assert result['score'] == 100
    assert result['action'] == "Call within 10 minutes"

def test_warm_lead():
    lead_data = {
        "cash_buyer": True, # +25
        "mortgage_status": "not_approved",
        "timeframe": "1 month", # +30
        "budget": 1000000,
        "message": "Interested"
    }
    # Total 55
    result = calculate_lead_score(lead_data)
    print(f"WARM Test Result: {result}")
    assert result['status'] == "WARM"
    assert result['score'] == 55
    assert result['action'] == "Send matching listings"

def test_cold_lead():
    lead_data = {
        "cash_buyer": False,
        "mortgage_status": "not_approved",
        "timeframe": "6 months+",
        "budget": 500000,
        "message": "Maybe later"
    }
    result = calculate_lead_score(lead_data)
    print(f"COLD Test Result: {result}")
    assert result['status'] == "COLD"
    assert result['score'] == 0
    assert result['action'] == "Add to long-term follow-up"

if __name__ == "__main__":
    test_hot_lead()
    test_warm_lead()
    test_cold_lead()
    print("All scoring tests passed!")
