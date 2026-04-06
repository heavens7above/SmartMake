import pytest
from unittest.mock import patch
from backend.execute.paper_trader import PaperTrader
import random

def test_get_current_price_mocked():
    """Test get_current_price with mocked random to ensure bounds."""
    trader = PaperTrader()

    # Test min bound
    with patch('random.uniform', return_value=21500.0):
        assert trader.get_current_price("NIFTY") == 21500.0

    # Test max bound
    with patch('random.uniform', return_value=22000.0):
        assert trader.get_current_price("NIFTY") == 22000.0

    # Test intermediate value
    with patch('random.uniform', return_value=21750.55):
        assert trader.get_current_price("NIFTY") == 21750.55

    # Test rounding
    with patch('random.uniform', return_value=21750.555):
        assert trader.get_current_price("NIFTY") == 21750.56
