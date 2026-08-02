import pytest
from unittest.mock import patch, MagicMock

from backend.capture.chart_capture import capture_chart

@patch('backend.capture.chart_capture.sync_playwright')
@patch('backend.capture.chart_capture.time.sleep')
def test_capture_chart_success(mock_sleep, mock_sync_playwright):
    # Setup mocks
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

    # Call the function
    capture_chart("NSE:NIFTY", "240", "nifty_test.png")

    # Verify playwright launch
    mock_playwright.chromium.launch.assert_called_once_with(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"]
    )

    # Verify new context
    mock_browser.new_context.assert_called_once_with(
        viewport={'width': 1920, 'height': 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    # Verify new page
    mock_context.new_page.assert_called_once()

    # Verify goto
    expected_url = "https://in.tradingview.com/chart/?symbol=NSE:NIFTY&interval=240"
    mock_page.goto.assert_called_once_with(expected_url)

    # Verify wait_for_selector
    mock_page.wait_for_selector.assert_called_once_with(".chart-container", timeout=10000)

    # Verify sleep
    mock_sleep.assert_called_once_with(5)

    # Verify screenshot
    mock_page.screenshot.assert_called_once_with(path="nifty_test.png", full_page=False)

    # Verify browser close
    mock_browser.close.assert_called_once()

@patch('backend.capture.chart_capture.sync_playwright')
@patch('backend.capture.chart_capture.time.sleep')
def test_capture_chart_exception_handling(mock_sleep, mock_sync_playwright):
    # Setup mocks
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

    # Simulate an exception during wait_for_selector
    mock_page.wait_for_selector.side_effect = Exception("Timeout waiting for selector")

    # Call the function and assert it raises
    with pytest.raises(Exception, match="Timeout waiting for selector"):
        capture_chart("NSE:NIFTY", "240", "nifty_test_fail.png")

    # Verify playwright launch
    mock_playwright.chromium.launch.assert_called_once()

    # Verify new context
    mock_browser.new_context.assert_called_once()

    # Verify new page
    mock_context.new_page.assert_called_once()

    # Verify goto
    expected_url = "https://in.tradingview.com/chart/?symbol=NSE:NIFTY&interval=240"
    mock_page.goto.assert_called_once_with(expected_url)

    # Verify wait_for_selector was called
    mock_page.wait_for_selector.assert_called_once_with(".chart-container", timeout=10000)

    # Verify sleep was not called due to exception
    mock_sleep.assert_not_called()

    # Verify screenshot was not called
    mock_page.screenshot.assert_not_called()

    # Verify browser close was STILL called (in finally block)
    mock_browser.close.assert_called_once()
