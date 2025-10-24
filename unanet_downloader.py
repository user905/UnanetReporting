from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path
from config import (
    UNANET_URL,
    UNANET_USERNAME,
    UNANET_PASSWORD,
    UNANET_REPORT_ID,
    DOWNLOAD_DIR
)
from logger import get_logger


def download_report():
    """Download report from Unanet or use existing file from today"""
    logger = get_logger()

    # Create reports directory if it doesn't exist
    DOWNLOAD_DIR.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    final_path = DOWNLOAD_DIR / f"unanet_report_{today}.csv"

    # Check if today's report already exists
    if final_path.exists():
        logger.info(f"Found existing report from today: {final_path}")
        logger.info("Using existing file instead of downloading from Unanet")
        return final_path

    # Download from Unanet if no file exists for today
    logger.info("No report found for today, downloading from Unanet...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            # === LOGIN ===
            logger.info(f"Logging into Unanet at {UNANET_URL}")
            page.goto(f"{UNANET_URL}/goaztech/")
            page.fill('input[name="username"]', UNANET_USERNAME)
            page.fill('input[name="password"]', UNANET_PASSWORD)
            page.click('#button_ok')
            page.wait_for_load_state("networkidle")
            logger.info("Login successful")

            # === SAVED REPORTS PAGE ===
            page.goto(f"{UNANET_URL}/goaztech/action/reports/saved")

            # === CLICK RUN ON REPORT ===
            logger.info(f"Clicking run on saved report {UNANET_REPORT_ID}...")
            page.click(f'tr#{UNANET_REPORT_ID} td.icon a[href*="runReport"]')

            # === WAIT FOR REPORT PAGE TO LOAD ===
            logger.info("Waiting for report data to load...")
            page.wait_for_selector('a[href*="doCSVFile"]', timeout=60000)

            # === DOWNLOAD CSV ===
            logger.info("Downloading CSV...")
            with page.expect_download() as download_info:
                page.click('a[href*="doCSVFile"]')

            download = download_info.value
            download.save_as(final_path)
            logger.info(f"Downloaded to: {final_path}")

            browser.close()

        return final_path

    except Exception as e:
        logger.error(f"Error downloading report from Unanet: {str(e)}", exc_info=True)
        raise
