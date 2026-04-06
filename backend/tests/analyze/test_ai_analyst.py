import pytest
import base64
import responses
from pydantic import ValidationError
from unittest.mock import patch, mock_open

from backend.analyze.ai_analyst import AIAnalyst
from backend.analyze.schemas import TradeSignal
from backend.utils.config import config

@pytest.fixture
def mock_config(mocker):
    # Mocking the configuration to ensure API_KEY is present
    mocker.patch.object(config, 'API_KEY', 'test_api_key')
    mocker.patch.object(config, 'MODEL_NAME', 'test_model')
    return config

@pytest.fixture
def mock_ai_analyst(mock_config):
    return AIAnalyst()

@pytest.fixture
def mock_image_path():
    return "dummy_chart.jpg"

@pytest.fixture
def mock_metadata():
    return {"symbol": "BTC/USD", "timeframe": "1h"}

def test_analyze_chart_missing_api_key(mocker):
    mocker.patch.object(config, 'API_KEY', None)
    analyst = AIAnalyst()

    with pytest.raises(ValueError, match="API_KEY not found"):
        analyst.analyze_chart("dummy.jpg", {})

@responses.activate
def test_analyze_chart_success(mock_ai_analyst, mock_image_path, mock_metadata):
    # Mock the image reading
    mock_image_data = b"dummy_image_content"
    encoded_image = base64.b64encode(mock_image_data).decode('utf-8')

    # Successful AI response payload matching schemas.TradeSignal
    valid_json_content = """
    {
        "signal": "BUY",
        "entry_time": "14:30",
        "exit_time": "15:30",
        "lot_size": 1.5,
        "stop_loss": 50000,
        "take_profit": 55000,
        "confidence": 85,
        "reasoning": "Strong support level bounce"
    }
    """

    # Mock OpenRouter API response
    responses.add(
        responses.POST,
        "https://openrouter.ai/api/v1/chat/completions",
        json={
            "choices": [
                {
                    "message": {
                        "content": valid_json_content
                    }
                }
            ]
        },
        status=200
    )

    with patch("builtins.open", mock_open(read_data=mock_image_data)):
        signal = mock_ai_analyst.analyze_chart(mock_image_path, mock_metadata)

    assert isinstance(signal, TradeSignal)
    assert signal.signal == "BUY"
    assert signal.entry_time == "14:30"
    assert signal.exit_time == "15:30"
    assert signal.lot_size == 1.5
    assert signal.stop_loss == 50000.0
    assert signal.take_profit == 55000.0
    assert signal.confidence == 85
    assert signal.reasoning == "Strong support level bounce"

@responses.activate
def test_analyze_chart_success_with_markdown(mock_ai_analyst, mock_image_path, mock_metadata):
    # Mock the image reading
    mock_image_data = b"dummy_image_content"

    # Successful AI response with markdown formatting
    valid_json_content = """```json
    {
        "signal": "SELL",
        "entry_time": "09:00",
        "exit_time": "11:00",
        "lot_size": 0.5,
        "stop_loss": 60000,
        "take_profit": 58000,
        "confidence": 90,
        "reasoning": "Double top pattern"
    }
    ```"""

    # Mock OpenRouter API response
    responses.add(
        responses.POST,
        "https://openrouter.ai/api/v1/chat/completions",
        json={
            "choices": [
                {
                    "message": {
                        "content": valid_json_content
                    }
                }
            ]
        },
        status=200
    )

    with patch("builtins.open", mock_open(read_data=mock_image_data)):
        signal = mock_ai_analyst.analyze_chart(mock_image_path, mock_metadata)

    assert isinstance(signal, TradeSignal)
    assert signal.signal == "SELL"

@responses.activate
def test_analyze_chart_api_error(mock_ai_analyst, mock_image_path, mock_metadata):
    # Mock the image reading
    mock_image_data = b"dummy_image_content"

    # Mock OpenRouter API response (500 Error)
    responses.add(
        responses.POST,
        "https://openrouter.ai/api/v1/chat/completions",
        body="Internal Server Error",
        status=500
    )

    from requests.exceptions import HTTPError
    with patch("builtins.open", mock_open(read_data=mock_image_data)):
        with pytest.raises(HTTPError):
            mock_ai_analyst.analyze_chart(mock_image_path, mock_metadata)

@responses.activate
def test_analyze_chart_invalid_json_schema(mock_ai_analyst, mock_image_path, mock_metadata):
    # Mock the image reading
    mock_image_data = b"dummy_image_content"

    # Invalid AI response missing required field "lot_size" and "signal"
    invalid_json_content = """
    {
        "entry_time": "14:30",
        "confidence": 85
    }
    """

    # Mock OpenRouter API response
    responses.add(
        responses.POST,
        "https://openrouter.ai/api/v1/chat/completions",
        json={
            "choices": [
                {
                    "message": {
                        "content": invalid_json_content
                    }
                }
            ]
        },
        status=200
    )

    with patch("builtins.open", mock_open(read_data=mock_image_data)):
        with pytest.raises(ValidationError):
            mock_ai_analyst.analyze_chart(mock_image_path, mock_metadata)
