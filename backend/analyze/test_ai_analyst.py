import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError
from pydantic import ValidationError

from .ai_analyst import AIAnalyst
from .schemas import TradeSignal

@pytest.fixture
def mock_config():
    with patch('backend.analyze.ai_analyst.config') as mock_config:
        mock_config.API_KEY = "test_api_key"
        mock_config.MODEL_NAME = "test_model"
        yield mock_config

def test_analyze_chart_missing_api_key():
    with patch('backend.analyze.ai_analyst.config') as mock_config:
        mock_config.API_KEY = ""
        analyst = AIAnalyst()

        with pytest.raises(ValueError, match="API_KEY not found"):
            analyst.analyze_chart("dummy.jpg", {})

@patch('backend.analyze.ai_analyst.requests.post')
def test_analyze_chart_success_valid_json(mock_post, mock_config):
    # Mocking encode_image to avoid file I/O
    with patch.object(AIAnalyst, 'encode_image', return_value="dummy_base64"):
        analyst = AIAnalyst()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"signal": "BUY", "entry_time": "10:00", "exit_time": "11:00", "lot_size": 1.0, "stop_loss": 100.0, "take_profit": 200.0, "confidence": 95, "reasoning": "Looks good"}'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})

        assert isinstance(result, TradeSignal)
        assert result.signal == "BUY"
        assert result.confidence == 95
        assert result.reasoning == "Looks good"

@patch('backend.analyze.ai_analyst.requests.post')
def test_analyze_chart_success_markdown_wrapped_json(mock_post, mock_config):
    with patch.object(AIAnalyst, 'encode_image', return_value="dummy_base64"):
        analyst = AIAnalyst()

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '```json\n{"signal": "SELL", "entry_time": "14:00", "exit_time": "15:00", "lot_size": 0.5, "stop_loss": 150.0, "take_profit": 50.0, "confidence": 80, "reasoning": "Bearish trend"}\n```'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = analyst.analyze_chart("dummy.jpg", {})

        assert isinstance(result, TradeSignal)
        assert result.signal == "SELL"
        assert result.confidence == 80

@patch('backend.analyze.ai_analyst.requests.post')
def test_analyze_chart_api_error(mock_post, mock_config):
    with patch.object(AIAnalyst, 'encode_image', return_value="dummy_base64"):
        analyst = AIAnalyst()

        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = HTTPError("401 Client Error")
        mock_post.return_value = mock_response

        with pytest.raises(HTTPError):
            analyst.analyze_chart("dummy.jpg", {})

@patch('backend.analyze.ai_analyst.requests.post')
def test_analyze_chart_invalid_json_structure(mock_post, mock_config):
    with patch.object(AIAnalyst, 'encode_image', return_value="dummy_base64"):
        analyst = AIAnalyst()

        mock_response = MagicMock()
        mock_response.ok = True
        # Missing required 'lot_size' and 'confidence'
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"signal": "HOLD"}'
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        with pytest.raises(ValidationError):
            analyst.analyze_chart("dummy.jpg", {})
