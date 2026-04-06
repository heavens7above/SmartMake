import pytest
import json
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError

from backend.analyze.ai_analyst import AIAnalyst
from backend.analyze.schemas import TradeSignal

@pytest.fixture
def mock_config(mocker):
    config_mock = mocker.patch('backend.analyze.ai_analyst.config')
    config_mock.API_KEY = "test_api_key"
    config_mock.MODEL_NAME = "test_model"
    return config_mock

@pytest.fixture
def mock_config_no_key(mocker):
    config_mock = mocker.patch('backend.analyze.ai_analyst.config')
    config_mock.API_KEY = None
    config_mock.MODEL_NAME = "test_model"
    return config_mock

def test_init_defaults(mocker):
    # Setup mock to test defaults when MODEL_NAME is None
    config_mock = mocker.patch('backend.analyze.ai_analyst.config')
    config_mock.API_KEY = "test_api_key"
    config_mock.MODEL_NAME = None

    analyst = AIAnalyst()
    assert analyst.api_key == "test_api_key"
    assert analyst.base_url == "https://openrouter.ai/api/v1/chat/completions"
    assert analyst.model == "google/gemini-2.0-flash-exp:free"

def test_init_with_config(mock_config):
    analyst = AIAnalyst()
    assert analyst.api_key == "test_api_key"
    assert analyst.model == "test_model"

def test_encode_image(mock_config, mocker):
    mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake_image_data'))
    analyst = AIAnalyst()
    encoded = analyst.encode_image("dummy/path.jpg")
    assert encoded == "ZmFrZV9pbWFnZV9kYXRh" # base64 for 'fake_image_data'

def test_analyze_chart_no_api_key(mock_config_no_key):
    analyst = AIAnalyst()
    with pytest.raises(ValueError, match="API_KEY not found"):
        analyst.analyze_chart("dummy/path.jpg", {"symbol": "BTCUSD"})

@pytest.fixture
def valid_trade_signal_json():
    return json.dumps({
        "signal": "BUY",
        "entry_time": "12:00",
        "exit_time": "14:00",
        "lot_size": 1.0,
        "stop_loss": 50000.0,
        "take_profit": 55000.0,
        "confidence": 80,
        "reasoning": "Looks good"
    })

def test_analyze_chart_success(mock_config, valid_trade_signal_json, mocker):
    mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake_image_data'))

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": valid_trade_signal_json
                }
            }
        ]
    }

    mock_post = mocker.patch('backend.analyze.ai_analyst.requests.post', return_value=mock_response)

    analyst = AIAnalyst()
    result = analyst.analyze_chart("dummy.jpg", {"symbol": "BTCUSD"})

    assert isinstance(result, TradeSignal)
    assert result.signal == "BUY"
    assert result.confidence == 80
    assert result.reasoning == "Looks good"

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs['headers']['Authorization'] == "Bearer test_api_key"
    assert kwargs['json']['model'] == "test_model"
    assert "Market Context: symbol: BTCUSD" in kwargs['json']['messages'][1]['content'][0]['text']

def test_analyze_chart_markdown_cleanup(mock_config, valid_trade_signal_json, mocker):
    mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake_image_data'))

    markdown_content = f"```json\n{valid_trade_signal_json}\n```"

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": markdown_content
                }
            }
        ]
    }

    mocker.patch('backend.analyze.ai_analyst.requests.post', return_value=mock_response)

    analyst = AIAnalyst()
    result = analyst.analyze_chart("dummy.jpg", {})

    assert isinstance(result, TradeSignal)
    assert result.signal == "BUY"

def test_analyze_chart_api_error(mock_config, mocker):
    mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake_image_data'))

    mock_response = MagicMock()
    mock_response.ok = False
    mock_response.text = "Unauthorized"
    mock_response.raise_for_status.side_effect = HTTPError("401 Client Error")

    mocker.patch('backend.analyze.ai_analyst.requests.post', return_value=mock_response)

    analyst = AIAnalyst()
    with pytest.raises(HTTPError):
        analyst.analyze_chart("dummy.jpg", {})

def test_analyze_chart_invalid_json(mock_config, mocker):
    mocker.patch('builtins.open', mocker.mock_open(read_data=b'fake_image_data'))

    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "{invalid json}"
                }
            }
        ]
    }

    mocker.patch('backend.analyze.ai_analyst.requests.post', return_value=mock_response)

    analyst = AIAnalyst()
    with pytest.raises(Exception): # Pydantic will raise a validation error, which is caught and re-raised, or JSONDecodeError
        analyst.analyze_chart("dummy.jpg", {})
