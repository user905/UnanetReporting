"""
Unanet to Dataverse Integration
Downloads reports from Unanet and uploads them to PowerApps/Dataverse
"""

from unanet_downloader import download_report
from dataverse_client import upload_to_dataverse
from config import DATAVERSE_USERNAME, DATAVERSE_PASSWORD


def main():
    """Main entry point for the application"""
    print("=== Unanet to Dataverse Integration ===\n")

    # Step 1: Download the report from Unanet (or use today's existing file)
    csv_path = download_report()

    # Step 2: Upload to Dataverse if credentials are configured
    if DATAVERSE_USERNAME and DATAVERSE_PASSWORD:
        upload_to_dataverse(csv_path)
    else:
        print("\nSkipping Dataverse upload - credentials not configured")
        print("Please set DATAVERSE_USERNAME and DATAVERSE_PASSWORD in config.py")

    print("\n=== Process Complete ===")


if __name__ == "__main__":
    main()
