import pytest
from backend.execute.paper_trader import PaperTrader

def test_get_current_price_range():
    """Test that get_current_price returns a float within the expected range."""
    trader = PaperTrader()

    # Test multiple times since it returns a random value
    for _ in range(100):
        price = trader.get_current_price("NIFTY")

        # Assert the returned type is a float
        assert isinstance(price, float)

        # Assert the returned price is within the range 21500 to 22000
        assert 21500.0 <= price <= 22000.0
