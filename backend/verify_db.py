from backend.db.database import get_db
from backend.db.models import Trade
from backend.utils.logger import logger
from sqlalchemy import desc

def verify_trades():
    with get_db() as db:
        trade = db.query(Trade).order_by(desc(Trade.timestamp)).first()
        if trade:
            print(f"Latest Trade: {trade.symbol} | Signal: {trade.signal} | Entry: {trade.entry_price} | ID: {trade.id}")
            print(f"Run ID: {trade.run_id}")
            print(f"Analysis Latency: {trade.analysis_latency_ms}ms | Execution Latency: {trade.execution_latency_ms}ms")
            print(f"Raw AI Response: {trade.raw_ai_response}")
        else:
            print("No trades found in database.")

if __name__ == "__main__":
    verify_trades()
