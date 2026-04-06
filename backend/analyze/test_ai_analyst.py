import pytest
import json
import base64
from unittest.mock import patch, mock_open, MagicMock
from requests.exceptions import HTTPError

from backend.analyze.ai_analyst import AIAnalyst
from backend.analyze.schemas import TradeSignal
from backend.utils.config import config

@pytest.fixture
def mock_config():
    with patch("backend.analyze.ai_analyst.config") as mock:
        mock.API_KEY = "test_api_key"
        mock.MODEL_NAME = "test-model"
        yield mock

@pytest.fixture
def analyst(mock_config):
    return AIAnalyst()

def test_encode_image(analyst):
    mock_file_content = b"fake_image_data"
    expected_encoded = base64.b64encode(mock_file_content).decode('utf-8')

    with patch("builtins.open", mock_open(read_data=mock_file_content)) as m:
        encoded_result = analyst.encode_image("dummy_path.jpg")

        m.assert_called_once_with("dummy_path.jpg", "rb")
        assert encoded_result == expected_encoded

def test_analyze_chart_missing_api_key():
    with patch("backend.analyze.ai_analyst.config") as mock_cfg:
        mock_cfg.API_KEY = None
        mock_cfg.MODEL_NAME = "test-model"

        analyst = AIAnalyst()

        with pytest.raises(ValueError, match="API_KEY not found"):
            analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})

def test_analyze_chart_success(analyst, mocker):
    mocker.patch.object(analyst, 'encode_image', return_value="encoded_data")

    mock_response = MagicMock()
    mock_response.ok = True

    valid_signal_dict = {
        "signal": "BUY",
        "entry_time": "14:30",
        "exit_time": "15:00",
        "lot_size": 1.5,
        "stop_loss": 50000,
        "take_profit": 55000,
        "confidence": 85,
        "reasoning": "Strong support level"
    }

    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(valid_signal_dict)
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_response) as mock_post:
        result = analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})

        mock_post.assert_called_once()
        assert isinstance(result, TradeSignal)
        assert result.signal == "BUY"
        assert result.lot_size == 1.5

def test_analyze_chart_markdown_cleanup(analyst, mocker):
    mocker.patch.object(analyst, 'encode_image', return_value="encoded_data")

    mock_response = MagicMock()
    mock_response.ok = True

    valid_signal_dict = {
        "signal": "SELL",
        "entry_time": "09:00",
        "exit_time": "10:00",
        "lot_size": 0.5,
        "confidence": 90
    }

    markdown_content = f"```json\n{json.dumps(valid_signal_dict)}\n```"

    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": markdown_content
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_response):
        result = analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})

        assert isinstance(result, TradeSignal)
        assert result.signal == "SELL"
        assert result.confidence == 90

def test_analyze_chart_api_error(analyst, mocker):
    mocker.patch.object(analyst, 'encode_image', return_value="encoded_data")

    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.text = "API Error Message"
    mock_response.raise_for_status.side_effect = HTTPError("HTTP Error occurred")

    with patch("requests.post", return_value=mock_response):
        with pytest.raises(HTTPError, match="HTTP Error occurred"):
            analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})

def test_analyze_chart_invalid_format(analyst, mocker):
    mocker.patch.object(analyst, 'encode_image', return_value="encoded_data")

    mock_response = MagicMock()
    mock_response.ok = True

    # Missing required fields like 'signal', 'lot_size', 'confidence'
    invalid_signal_dict = {
        "reasoning": "I don't know what I'm doing"
    }

    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(invalid_signal_dict)
                }
            }
        ]
    }

    from pydantic import ValidationError

    with patch("requests.post", return_value=mock_response):
        with pytest.raises(ValidationError):
            analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})
