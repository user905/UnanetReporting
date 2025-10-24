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


def main():
    """Main entry point for the application"""
    print("=== Unanet to Dataverse Integration ===\n")

    # Calculate date range (past year from today)
    today = datetime.now()
    one_year_ago = today - timedelta(days=365)

    today_str = today.strftime("%Y-%m-%d")
    one_year_ago_str = one_year_ago.strftime("%Y-%m-%d")

    print(f"Date range: {one_year_ago_str} to {today_str}")
    print(f"Processing records from the past 365 days\n")

    # Step 1: Download the report from Unanet (or use today's existing file)
    csv_path = download_report()

    # Step 2: Upload to Dataverse if credentials are configured
    if DATAVERSE_USERNAME and DATAVERSE_PASSWORD:
        # Delete existing records in the date range
        delete_records_in_date_range(one_year_ago_str, today_str)

        # Upload records from CSV (only those in the date range)
        upload_to_dataverse(csv_path, start_date=one_year_ago_str, end_date=today_str)
    else:
        print("\nSkipping Dataverse upload - credentials not configured")
        print("Please set DATAVERSE_USERNAME and DATAVERSE_PASSWORD in .env file")

    print("\n=== Process Complete ===")


if __name__ == "__main__":
    main()
