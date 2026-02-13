from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, nullable=False, index=True) # UUID string
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    symbol = Column(String, nullable=False)
    signal = Column(String, nullable=False) # BUY, SELL, HOLD
    entry_time = Column(String) # Keeping as string for "HH:MM" format from JSON, or could be Time
    exit_time = Column(String)
    entry_price = Column(Float)
    exit_price = Column(Float)
    lot_size = Column(Float)
    pnl = Column(Float)
    confidence = Column(Integer)
    raw_ai_response = Column(JSON)
    screenshot_path = Column(String)
    analysis_latency_ms = Column(Integer)
    execution_latency_ms = Column(Integer)
    metadata_content = Column(JSON) # 'metadata' is reserved in SQLAlchemy Base

    def __repr__(self):
        return f"<Trade(id={self.id}, symbol={self.symbol}, signal={self.signal}, pnl={self.pnl})>"
