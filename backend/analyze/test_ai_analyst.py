import pytest
from backend.analyze.ai_analyst import AIAnalyst

def test_analyze_chart_missing_api_key():
    # Instantiate with no api key
    analyst = AIAnalyst()
    analyst.api_key = None

    with pytest.raises(ValueError) as exc_info:
        analyst.analyze_chart("dummy_path.png", {})

    assert str(exc_info.value) == "API_KEY not found"
