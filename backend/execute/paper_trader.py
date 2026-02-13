from datetime import datetime
from ..db.database import get_db
from ..db.models import Trade
from ..analyze.schemas import TradeSignal
from ..utils.logger import logger
import random # Mock price data

import time

class PaperTrader:
    def __init__(self):
        pass

    def get_current_price(self, symbol: str) -> float:
        # Mock price fetcher - replace with real API (e.g. Yahoo Finance, Kite) later
        # For NIFTY, roughly 21000-22000
        return round(random.uniform(21500, 22000), 2)

    def execute_trade(self, run_id: str, symbol: str, signal: TradeSignal, screenshot_path: str, raw_response: dict, analysis_latency: int):
        start_time = time.time()
        
        if signal.signal == "HOLD":
            logger.info(f"Signal is HOLD for {symbol}. No trade executed.")
            execution_latency = int((time.time() - start_time) * 1000)
            self._log_trade(run_id, symbol, signal, None, None, 0, 0, screenshot_path, raw_response, analysis_latency, execution_latency)
            return

        current_price = self.get_current_price(symbol)
        logger.info(f"Executing {signal.signal} for {symbol} at {current_price}")

        # Simulate Entry
        entry_price = current_price
        
        execution_latency = int((time.time() - start_time) * 1000)
        
        self._log_trade(
            run_id=run_id,
            symbol=symbol,
            signal_obj=signal,
            entry_price=entry_price,
            exit_price=None, # To be filled by a position manager or manual update
            pnl=0,
            lot_size=signal.lot_size,
            screenshot_path=screenshot_path,
            raw_response=raw_response,
            analysis_latency=analysis_latency,
            execution_latency=execution_latency
        )

    def _log_trade(self, run_id, symbol, signal_obj, entry_price, exit_price, pnl, lot_size, screenshot_path, raw_response, analysis_latency, execution_latency):
        with get_db() as db:
            trade = Trade(
                run_id=run_id,
                symbol=symbol,
                signal=signal_obj.signal,
                entry_time=str(signal_obj.entry_time), # Ensure string format for JSON compatibility if needed
                exit_time=str(signal_obj.exit_time),
                entry_price=entry_price,
                exit_price=exit_price,
                lot_size=lot_size,
                pnl=pnl,
                confidence=signal_obj.confidence,
                raw_ai_response=raw_response,
                screenshot_path=screenshot_path,
                analysis_latency_ms=analysis_latency,
                execution_latency_ms=execution_latency
            )
            db.add(trade)
            db.commit()
            db.refresh(trade)
            logger.info(f"Trade logged: {trade} (Run ID: {run_id})")

