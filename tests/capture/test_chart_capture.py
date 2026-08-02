import pytest
from unittest.mock import MagicMock, patch
from backend.capture.chart_capture import capture_chart

@patch("backend.capture.chart_capture.sync_playwright")
@patch("backend.capture.chart_capture.time.sleep")
@patch("backend.capture.chart_capture.logger")
def test_capture_chart_success(mock_logger, mock_sleep, mock_sync_playwright):
    # Setup mock playwright
    mock_playwright_context_manager = MagicMock()
    mock_sync_playwright.return_value = mock_playwright_context_manager

    mock_playwright = MagicMock()
    mock_playwright_context_manager.__enter__.return_value = mock_playwright

    mock_browser = MagicMock()
    mock_playwright.chromium.launch.return_value = mock_browser

    mock_context = MagicMock()
    mock_browser.new_context.return_value = mock_context

    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page

    # Call function
    capture_chart("NSE:NIFTY", "4h", "test_path.png")

    # Assertions
    mock_playwright.chromium.launch.assert_called_once_with(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )
    mock_browser.new_context.assert_called_once()
    mock_context.new_page.assert_called_once()

    expected_url = "https://in.tradingview.com/chart/?symbol=NSE:NIFTY&interval=4h"
    mock_page.goto.assert_called_once_with(expected_url)
    mock_page.wait_for_selector.assert_called_once_with(".chart-container", timeout=10000)
    mock_sleep.assert_called_once_with(5)
    mock_page.screenshot.assert_called_once_with(path="test_path.png", full_page=False)

    mock_logger.info.assert_any_call(f"Navigating to {expected_url}")
    mock_logger.info.assert_any_call("Taking screenshot...")
    mock_logger.info.assert_any_call(f"Screenshot saved to test_path.png")

    mock_browser.close.assert_called_once()

@patch("backend.capture.chart_capture.sync_playwright")
@patch("backend.capture.chart_capture.logger")
def test_capture_chart_exception(mock_logger, mock_sync_playwright):
    # Setup mock playwright
    mock_playwright_context_manager = MagicMock()
    mock_sync_playwright.return_value = mock_playwright_context_manager

    mock_playwright = MagicMock()
    mock_playwright_context_manager.__enter__.return_value = mock_playwright

    mock_browser = MagicMock()
    mock_playwright.chromium.launch.return_value = mock_browser

    mock_context = MagicMock()
    mock_browser.new_context.return_value = mock_context

    mock_page = MagicMock()
    mock_context.new_page.return_value = mock_page

    # Simulate exception during wait_for_selector
    test_exception = Exception("Test Error")
    mock_page.wait_for_selector.side_effect = test_exception

    # Call function and expect exception
    with pytest.raises(Exception) as exc_info:
        capture_chart("NSE:RELIANCE", "1D", "fail.png")

    assert str(exc_info.value) == "Test Error"

    # Assertions
    mock_logger.error.assert_called_once_with(f"Failed to capture chart: {test_exception}")

    # Ensure browser is closed even on exception
    mock_browser.close.assert_called_once()
