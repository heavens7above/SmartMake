import pytest
from unittest.mock import MagicMock, patch
from backend.execute.paper_trader import PaperTrader
from backend.analyze.schemas import TradeSignal

@pytest.fixture
def paper_trader():
    return PaperTrader()

@pytest.fixture
def mock_log_trade():
    with patch.object(PaperTrader, '_log_trade') as mock:
        yield mock

def test_execute_trade_hold(paper_trader, mock_log_trade):
    signal = TradeSignal(
        signal="HOLD",
        lot_size=10.0,
        confidence=80,
        reasoning="Market is volatile",
        entry_time="10:00"
    )
    with patch.object(paper_trader, 'get_current_price') as mock_get_price:
        paper_trader.execute_trade(
            run_id="test_run_1",
            symbol="NIFTY",
            signal=signal,
            screenshot_path="test.png",
            raw_response={"data": "test"},
            analysis_latency=100
        )

        # Verify get_current_price is NOT called for HOLD
        mock_get_price.assert_not_called()

        # Verify _log_trade is called with the correct parameters
        # From code: self._log_trade(run_id, symbol, signal, None, None, 0, 0, screenshot_path, raw_response, analysis_latency, execution_latency)
        mock_log_trade.assert_called_once()
        args, kwargs = mock_log_trade.call_args
        assert args[0] == "test_run_1" # run_id
        assert args[1] == "NIFTY" # symbol
        assert args[2] == signal # signal
        assert args[3] is None # entry_price
        assert args[4] is None # exit_price
        assert args[5] == 0 # pnl
        assert args[6] == 0 # lot_size
        assert args[7] == "test.png" # screenshot_path
        assert args[8] == {"data": "test"} # raw_response
        assert args[9] == 100 # analysis_latency
        # args[10] is execution_latency, which is measured in the function

def test_execute_trade_buy(paper_trader, mock_log_trade):
    signal = TradeSignal(
        signal="BUY",
        lot_size=15.5,
        confidence=90,
        reasoning="Strong uptrend",
        entry_time="10:00"
    )
    with patch.object(paper_trader, 'get_current_price', return_value=21500.50) as mock_get_price:
        paper_trader.execute_trade(
            run_id="test_run_2",
            symbol="BANKNIFTY",
            signal=signal,
            screenshot_path="test2.png",
            raw_response={"data": "test2"},
            analysis_latency=150
        )

        # Verify get_current_price is called for BUY
        mock_get_price.assert_called_once_with("BANKNIFTY")

        # Verify _log_trade is called with the correct parameters
        # From code: self._log_trade(run_id=run_id, symbol=symbol, signal_obj=signal, entry_price=entry_price, exit_price=None, pnl=0, lot_size=signal.lot_size, screenshot_path=screenshot_path, raw_response=raw_response, analysis_latency=analysis_latency, execution_latency=execution_latency)
        mock_log_trade.assert_called_once()
        args, kwargs = mock_log_trade.call_args
        assert kwargs["run_id"] == "test_run_2"
        assert kwargs["symbol"] == "BANKNIFTY"
        assert kwargs["signal_obj"] == signal
        assert kwargs["entry_price"] == 21500.50
        assert kwargs["exit_price"] is None
        assert kwargs["pnl"] == 0
        assert kwargs["lot_size"] == 15.5
        assert kwargs["screenshot_path"] == "test2.png"
        assert kwargs["raw_response"] == {"data": "test2"}
        assert kwargs["analysis_latency"] == 150
        # kwargs["execution_latency"] is measured in the function
