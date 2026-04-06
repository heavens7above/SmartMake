import pytest
from unittest.mock import MagicMock, patch, ANY
from backend.execute.paper_trader import PaperTrader
from backend.analyze.schemas import TradeSignal
from backend.db.models import Trade

@pytest.fixture
def paper_trader():
    return PaperTrader()

@pytest.fixture
def base_signal_kwargs():
    return {
        "confidence": 80,
        "lot_size": 1.5,
        "reasoning": "Test reasoning"
    }

def test_get_current_price(paper_trader):
    """Test that get_current_price returns a value within the expected mock range."""
    price = paper_trader.get_current_price("NIFTY")
    assert 21500.0 <= price <= 22000.0

def test_execute_trade_hold_signal(paper_trader, base_signal_kwargs):
    """Test execute_trade when signal is HOLD."""
    signal = TradeSignal(signal="HOLD", **base_signal_kwargs)

    with patch.object(paper_trader, 'get_current_price') as mock_get_price, \
         patch.object(paper_trader, '_log_trade') as mock_log_trade:

        paper_trader.execute_trade(
            run_id="test_run_id",
            symbol="NIFTY",
            signal=signal,
            screenshot_path="/path/to/screenshot",
            raw_response={"data": "test"},
            analysis_latency=100
        )

        # get_current_price should not be called for a HOLD signal
        mock_get_price.assert_not_called()

        # _log_trade should be called with specific arguments for HOLD (it is called positionally in the code)
        mock_log_trade.assert_called_once_with(
            "test_run_id",
            "NIFTY",
            signal,
            None, # entry_price
            None, # exit_price
            0,    # pnl
            0,    # lot_size
            "/path/to/screenshot",
            {"data": "test"},
            100,  # analysis_latency
            ANY   # execution_latency (we check type later or accept ANY here)
        )

        # For the ANY, we can verify it was an integer by getting the actual call args
        execution_latency = mock_log_trade.call_args[0][10]
        assert isinstance(execution_latency, int)

def test_execute_trade_buy_signal(paper_trader, base_signal_kwargs):
    """Test execute_trade when signal is BUY."""
    signal = TradeSignal(signal="BUY", **base_signal_kwargs)
    expected_price = 21750.5

    with patch.object(paper_trader, 'get_current_price', return_value=expected_price) as mock_get_price, \
         patch.object(paper_trader, '_log_trade') as mock_log_trade:

        paper_trader.execute_trade(
            run_id="test_run_id",
            symbol="NIFTY",
            signal=signal,
            screenshot_path="/path/to/screenshot",
            raw_response={"data": "test"},
            analysis_latency=150
        )

        # get_current_price should be called
        mock_get_price.assert_called_once_with("NIFTY")

        # _log_trade should be called with calculated kwargs (it is called with kwargs in the code)
        mock_log_trade.assert_called_once_with(
            run_id="test_run_id",
            symbol="NIFTY",
            signal_obj=signal,
            entry_price=expected_price,
            exit_price=None,
            pnl=0,
            lot_size=signal.lot_size,
            screenshot_path="/path/to/screenshot",
            raw_response={"data": "test"},
            analysis_latency=150,
            execution_latency=ANY
        )

        # Check that the ANY parameter execution_latency is an integer
        execution_latency = mock_log_trade.call_args[1]["execution_latency"]
        assert isinstance(execution_latency, int)

def test_log_trade(paper_trader, base_signal_kwargs):
    """Test the internal _log_trade method to ensure database operations occur."""
    signal = TradeSignal(signal="BUY", entry_time="09:15", exit_time="15:30", **base_signal_kwargs)

    mock_db_session = MagicMock()
    mock_get_db = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_db_session

    with patch('backend.execute.paper_trader.get_db', mock_get_db):
        paper_trader._log_trade(
            run_id="test_run_id",
            symbol="NIFTY",
            signal_obj=signal,
            entry_price=21500.0,
            exit_price=None,
            pnl=0,
            lot_size=signal.lot_size,
            screenshot_path="/path/to/screenshot",
            raw_response={"data": "test"},
            analysis_latency=100,
            execution_latency=50
        )

        # Assert database operations were called
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

        # Check the Trade object passed to db.add
        added_trade = mock_db_session.add.call_args[0][0]
        assert isinstance(added_trade, Trade)
        assert added_trade.run_id == "test_run_id"
        assert added_trade.symbol == "NIFTY"
        assert added_trade.signal == "BUY"
        assert added_trade.entry_time == "09:15"
        assert added_trade.exit_time == "15:30"
        assert added_trade.entry_price == 21500.0
        assert added_trade.exit_price is None
        assert added_trade.lot_size == 1.5
        assert added_trade.pnl == 0
        assert added_trade.confidence == 80
        assert added_trade.raw_ai_response == {"data": "test"}
        assert added_trade.screenshot_path == "/path/to/screenshot"
        assert added_trade.analysis_latency_ms == 100
        assert added_trade.execution_latency_ms == 50
