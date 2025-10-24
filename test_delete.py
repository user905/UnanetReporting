"""
Test delete functionality with a safe date range
This will show how many records would be deleted without actually deleting them
"""

import requests
from dataverse_client import get_dataverse_token
from config import DATAVERSE_URL, TABLE_NAME, TABLE_PREFIX

def test_delete_query(date_string, date_field_name=None):
    """
    Test the delete query to see how many records would be affected

    Args:
        date_string: Date in format 'YYYY-MM-DD' (e.g., '2024-01-01')
        date_field_name: Name of the date field to filter on (default: cr834_date)
    """
    if date_field_name is None:
        date_field_name = f"{TABLE_PREFIX}_date"

    print(f"\n=== Testing Delete Query ===")
    print(f"Date field: {date_field_name}")
    print(f"Deleting records where {date_field_name} > {date_string}\n")

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

    # Query for records after the specified date
    primary_key_field = f"{TABLE_NAME.rstrip('s')}id"
    filter_query = f"?$filter={date_field_name} gt '{date_string}'&$select={primary_key_field},{date_field_name}&$top=10"
    url = f"{DATAVERSE_URL}/api/data/v9.2/{TABLE_NAME}{filter_query}"

    print(f"Fetching sample records where {date_field_name} > {date_string}...")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching records: {response.status_code}")
        print(f"Response: {response.text}")
        return

    data = response.json()
    records = data.get('value', [])

    print(f"\nFound {len(records)} sample records (showing up to 10):")
    print("-" * 60)
    for i, record in enumerate(records, 1):
        record_id = record.get(primary_key_field, 'N/A')
        record_date = record.get(date_field_name, 'N/A')
        print(f"{i}. ID: {record_id[:8]}... | Date: {record_date}")

    # Get total count
    count_url = f"{DATAVERSE_URL}/api/data/v9.2/{TABLE_NAME}?$filter={date_field_name} gt '{date_string}'&$count=true&$top=0"
    count_response = requests.get(count_url, headers=headers)

    if count_response.status_code == 200:
        total_count = count_response.json().get('@odata.count', 0)
        print("-" * 60)
        print(f"\nTOTAL RECORDS THAT WOULD BE DELETED: {total_count}")
    else:
        print("\nCould not get total count")

    print("\n" + "="*60)
    print("This was a TEST - NO records were deleted")
    print("="*60)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_delete.py YYYY-MM-DD")
        print("Example: python test_delete.py 2024-12-31")
        print("\nThis will show how many records would be deleted (TEST ONLY)")
        sys.exit(1)

    date_string = sys.argv[1]
    test_delete_query(date_string)
