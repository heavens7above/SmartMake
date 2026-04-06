from playwright.sync_api import sync_playwright
import os
from ..utils.logger import logger

def capture_chart(symbol: str, interval: str = "4h", save_path: str = "custom_path.png"):
    """
    Captures a screenshot of the chart for the given symbol.
    """
    url = f"https://in.tradingview.com/chart/?symbol={symbol}&interval={interval}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()
        
        logger.info(f"Navigating to {url}")
        page.goto(url)
        
        # Wait for chart to load - this selector might need tuning based on TV updates
        try:
            # General wait for body or specific element
            page.wait_for_selector(".chart-container", timeout=10000) 
            # Allow some time for indicators to render
            page.wait_for_load_state("networkidle")
            
            # Hide widgets or popups if any (optional, might need specific selectors)
            
            logger.info("Taking screenshot...")
            page.screenshot(path=save_path, full_page=False)
            logger.info(f"Screenshot saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to capture chart: {e}")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    # Test run
    capture_chart("NSE:NIFTY", "240", "nifty_4h.png")
