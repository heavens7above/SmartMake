import pytest
import json
import base64
from unittest.mock import patch, mock_open, MagicMock
import requests
from pydantic import ValidationError

from backend.analyze.ai_analyst import AIAnalyst
from backend.analyze.schemas import TradeSignal


@pytest.fixture
def mock_config():
    with patch("backend.analyze.ai_analyst.config") as mock_conf:
        mock_conf.API_KEY = "test_api_key"
        mock_conf.MODEL_NAME = "test/model"
        yield mock_conf

@pytest.fixture
def analyst(mock_config):
    return AIAnalyst()

def test_init(mock_config):
    analyst = AIAnalyst()
    assert analyst.api_key == "test_api_key"
    assert analyst.model == "test/model"

def test_encode_image(analyst):
    mock_file_content = b"fake_image_data"
    expected_base64 = base64.b64encode(mock_file_content).decode('utf-8')
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        encoded = analyst.encode_image("dummy.jpg")
        assert encoded == expected_base64

def test_analyze_chart_missing_api_key(analyst):
    analyst.api_key = None
    with pytest.raises(ValueError, match="API_KEY not found"):
        analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})

@patch("backend.analyze.ai_analyst.requests.post")
@patch.object(AIAnalyst, "encode_image", return_value="fake_encoded_image")
def test_analyze_chart_success(mock_encode, mock_post, analyst):
    mock_response = MagicMock()
    mock_response.ok = True
    valid_json_response = {
        "signal": "BUY",
        "entry_time": "14:30",
        "exit_time": "15:00",
        "lot_size": 1.5,
        "stop_loss": 50000.0,
        "take_profit": 55000.0,
        "confidence": 85,
        "reasoning": "Looks good"
    }
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(valid_json_response)
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    result = analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})

    assert isinstance(result, TradeSignal)
    assert result.signal == "BUY"
    assert result.lot_size == 1.5
    assert result.confidence == 85
    mock_encode.assert_called_once_with("dummy.jpg")
    mock_post.assert_called_once()

    # Check payload
    called_args, called_kwargs = mock_post.call_args
    assert called_kwargs["headers"]["Authorization"] == "Bearer test_api_key"
    assert "messages" in called_kwargs["json"]
    assert "symbol: BTCUSD" in called_kwargs["json"]["messages"][1]["content"][0]["text"]

@patch("backend.analyze.ai_analyst.requests.post")
@patch.object(AIAnalyst, "encode_image", return_value="fake_encoded_image")
def test_analyze_chart_markdown_cleaning(mock_encode, mock_post, analyst):
    mock_response = MagicMock()
    mock_response.ok = True
    valid_json_response = {
        "signal": "SELL",
        "entry_time": "09:15",
        "exit_time": "10:00",
        "lot_size": 2.0,
        "confidence": 90,
        "reasoning": "Trend is down"
    }

    markdown_content = f"```json\n{json.dumps(valid_json_response)}\n```"
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": markdown_content
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    result = analyst.analyze_chart("dummy.jpg", {"symbol": "ETHUSD"})

    assert isinstance(result, TradeSignal)
    assert result.signal == "SELL"
    assert result.lot_size == 2.0

@patch("backend.analyze.ai_analyst.requests.post")
@patch.object(AIAnalyst, "encode_image", return_value="fake_encoded_image")
def test_analyze_chart_api_error(mock_encode, mock_post, analyst):
    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.text = "Bad Request"
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error")
    mock_post.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError, match="400 Client Error"):
        analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})

@patch("backend.analyze.ai_analyst.requests.post")
@patch.object(AIAnalyst, "encode_image", return_value="fake_encoded_image")
def test_analyze_chart_validation_error(mock_encode, mock_post, analyst):
    mock_response = MagicMock()
    mock_response.ok = True
    invalid_json_response = {
        "signal": "INVALID_SIGNAL",
    }
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(invalid_json_response)
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    with pytest.raises(ValidationError):
        analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})
