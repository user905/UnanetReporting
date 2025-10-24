"""
Upload a small sample of records for testing
"""

import csv
import requests
from dataverse_client import get_dataverse_token, map_csv_row_to_dataverse
from config import DATAVERSE_URL, TABLE_NAME
import sys


def upload_sample_records(csv_file_path, num_records=10):
    """Upload just a few sample records for testing"""
    print(f"\n=== Uploading {num_records} Sample Records ===")

    # Get authentication token
    print("Authenticating to Dataverse...")
    token = get_dataverse_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json"
    }

    # Read sample records from CSV
    print(f"Reading {num_records} records from: {csv_file_path}")
    records = []
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            if i >= num_records:
                break
            data = map_csv_row_to_dataverse(row)
            records.append(data)

    print(f"Found {len(records)} records to upload\n")

    # Upload each record individually
    url = f"{DATAVERSE_URL}/api/data/v9.2/{TABLE_NAME}"
    success_count = 0

    for i, record in enumerate(records, 1):
        response = requests.post(url, headers=headers, json=record)

        if response.status_code in [200, 201, 204]:
            success_count += 1
            date_value = record.get(list(record.keys())[10], 'N/A')  # Get date field
            print(f"  ✓ Uploaded record {i}/{len(records)} - Date: {date_value}")
        else:
            print(f"  ✗ Error uploading record {i}: {response.status_code}")
            print(f"    {response.text[:200]}")

    print(f"\n✓ Successfully uploaded {success_count}/{len(records)} sample records")


if __name__ == "__main__":
    csv_path = r"C:\Users\elias\Documents\Repos\UnanetReporting\reports\unanet_report_2025-10-24.csv"

    # Allow custom number of records via command line
    num_records = 10
    if len(sys.argv) > 1:
        try:
            num_records = int(sys.argv[1])
        except ValueError:
            print("Invalid number, using default of 10")

    upload_sample_records(csv_path, num_records)
