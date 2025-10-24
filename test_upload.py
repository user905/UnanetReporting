"""
Test upload with a single record to see the full error message
"""

import requests
from dataverse_client import get_dataverse_token, map_csv_row_to_dataverse
from config import DATAVERSE_URL, TABLE_NAME, DOWNLOAD_DIR
import csv
from datetime import datetime

# Read just the first row from CSV
today = datetime.now().strftime("%Y-%m-%d")
csv_path = DOWNLOAD_DIR / f"unanet_report_{today}.csv"

if not csv_path.exists():
    print(f"No CSV found at: {csv_path}")
    print("Please run main.py first to download a report")
    exit(1)

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    first_row = next(reader)

# Map to Dataverse format
data = map_csv_row_to_dataverse(first_row)

print("Mapped data:")
for key, value in data.items():
    print(f"  {key}: {value}")

# Get token
print("\nAuthenticating...")
token = get_dataverse_token()

# Try to upload single record
headers = {
    "Authorization": f"Bearer {token}",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0",
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json"
}

url = f"{DATAVERSE_URL}/api/data/v9.2/{TABLE_NAME}"
print(f"\nPosting to: {url}")

response = requests.post(url, headers=headers, json=data)

print(f"\nStatus: {response.status_code}")
if response.status_code in [200, 201, 204]:
    print("✓ Successfully uploaded test record!")
else:
    print(f"✗ Error: {response.text}")
