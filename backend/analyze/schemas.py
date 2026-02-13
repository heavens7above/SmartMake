from pydantic import BaseModel, Field, validator
from typing import Optional, Literal

class TradeSignal(BaseModel):
    signal: Literal["BUY", "SELL", "HOLD"]
    entry_time: Optional[str] = Field(None, description="HH:MM format") # Optional if HOLD
    exit_time: Optional[str] = Field(None, description="HH:MM format")
    lot_size: float = Field(..., gt=0)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: int = Field(..., ge=0, le=100)
    reasoning: Optional[str] = Field(None, description="Brief reasoning for the decision")

    @validator("entry_time", "exit_time")
    def validate_time_format(cls, v):
        if v is None:
            return v
        # Simple regex or strptime could work here, but keeping it simple for now
        # Ideally checks HH:MM
        import re
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Time must be in HH:MM format")
        return v
