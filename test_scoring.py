
from lead_scoring import calculate_lead_score

def test_hot_lead():
    lead_data = {
        "cash_buyer": True,
        "mortgage_status": "approved",
        "timeframe": "Immediate",
        "budget": 2000000,
        "message": "I am urgent"
    }
    result = calculate_lead_score(lead_data)
    print(f"HOT Test Result: {result}")
    assert result['status'] == "HOT"
    assert result['score'] == 100
    assert "Book Appointment" in result['action']
    assert result['commission'] == 50000.0

def test_warm_lead():
    lead_data = {
        "cash_buyer": False,
        "mortgage_status": "not_approved",
        "timeframe": "Immediate",
        "budget": 500000,
        "message": "Interested"
    }
    # Score: 0 (cash) + 0 (mortgage) + 30 (timeframe) + 10 (budget) = 40
    result = calculate_lead_score(lead_data)
    print(f"WARM Test Result: {result}")
    assert result['status'] == "WARM"
    assert result['score'] == 40
    assert result['commission'] == 12500.0

def test_cold_lead():
    lead_data = {
        "cash_buyer": False,
        "mortgage_status": "not_approved",
        "timeframe": "6 months+",
        "budget": 100000,
        "message": "Maybe later"
    }
    # Score: 0 + 0 + 0 + 0 = 0
    result = calculate_lead_score(lead_data)
    print(f"COLD Test Result: {result}")
    assert result['status'] == "COLD"
    assert result['score'] <= 30
    assert "nurture" in result['action'].lower()
