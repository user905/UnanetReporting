"""
Unanet to Dataverse Integration
Downloads reports from Unanet and uploads them to PowerApps/Dataverse

Workflow:
1. Download report from Unanet (or use cached version)
2. Delete existing records from the past year
3. Upload only records from the past year from the CSV
"""

from datetime import datetime, timedelta
from unanet_downloader import download_report
from dataverse_client import upload_to_dataverse, delete_records_in_date_range
from config import DATAVERSE_USERNAME, DATAVERSE_PASSWORD
from logger import setup_logger


def main():
    """Main entry point for the application"""
    # Initialize logger
    logger = setup_logger()

    logger.info("=== Unanet to Dataverse Integration ===")

    try:
        # Calculate date range (past year from today)
        today = datetime.now()
        one_year_ago = today - timedelta(days=365)

        today_str = today.strftime("%Y-%m-%d")
        one_year_ago_str = one_year_ago.strftime("%Y-%m-%d")

        logger.info(f"Date range: {one_year_ago_str} to {today_str}")
        logger.info(f"Processing records from the past 365 days")

        # Step 1: Download the report from Unanet (or use today's existing file)
        csv_path = download_report()

        # Step 2: Upload to Dataverse if credentials are configured
        if DATAVERSE_USERNAME and DATAVERSE_PASSWORD:
            # Delete existing records in the date range
            delete_records_in_date_range(one_year_ago_str, today_str)

            # Upload records from CSV (only those in the date range)
            upload_to_dataverse(csv_path, start_date=one_year_ago_str, end_date=today_str)
        else:
            logger.warning("Skipping Dataverse upload - credentials not configured")
            logger.warning("Please set DATAVERSE_USERNAME and DATAVERSE_PASSWORD in .env file")

        logger.info("=== Process Complete ===")

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
