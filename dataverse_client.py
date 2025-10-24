import csv
import requests
import uuid
from msal import PublicClientApplication
from config import (
    DATAVERSE_URL,
    DATAVERSE_USERNAME,
    DATAVERSE_PASSWORD,
    TABLE_PREFIX,
    TABLE_NAME,
    BATCH_SIZE
)
from logger import get_logger


def get_dataverse_token():
    """Authenticate to Dataverse using username/password"""
    # Microsoft Dynamics 365 client ID (public client for username/password flow)
    client_id = "51f81489-12ee-4a9e-aaae-a2591f45987d"
    authority = "https://login.microsoftonline.com/organizations"

    app = PublicClientApplication(client_id=client_id, authority=authority)

    # Get token using username/password
    scopes = [f"{DATAVERSE_URL}/.default"]
    result = app.acquire_token_by_username_password(
        username=DATAVERSE_USERNAME,
        password=DATAVERSE_PASSWORD,
        scopes=scopes
    )

    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Authentication failed: {result.get('error_description', 'Unknown error')}")


def convert_to_decimal(value):
    """Convert string to decimal, return None if empty or invalid"""
    if not value or value.strip() == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def map_csv_row_to_dataverse(row):
    """Map CSV columns to Dataverse columns with proper type conversion"""
    return {
        f"{TABLE_PREFIX}_projectorganization": row.get("ProjectOrganization") or None,
        f"{TABLE_PREFIX}_projectcode": row.get("ProjectCode") or None,
        f"{TABLE_PREFIX}_tasknumber": row.get("TaskNumber") or None,
        f"{TABLE_PREFIX}_task": row.get("Task") or None,
        f"{TABLE_PREFIX}_laborcategory": row.get("LaborCategory") or None,
        f"{TABLE_PREFIX}_location": row.get("Location") or None,
        f"{TABLE_PREFIX}_projecttype": row.get("ProjectType") or None,
        f"{TABLE_PREFIX}_paycode": row.get("PayCode") or None,
        f"{TABLE_PREFIX}_person": row.get("Person") or None,
        f"{TABLE_PREFIX}_reference": row.get("Reference") or None,
        f"{TABLE_PREFIX}_date": row.get("Date") or None,
        f"{TABLE_PREFIX}_adjposteddate": row.get("ADJPostedDate") or None,
        f"{TABLE_PREFIX}_financialposteddate": row.get("FinancialPostedDate") or None,
        f"{TABLE_PREFIX}_billingcurrency": row.get("BillingCurrency") or None,
        f"{TABLE_PREFIX}_billratebc": convert_to_decimal(row.get("BillRateBC")),
        f"{TABLE_PREFIX}_hours": convert_to_decimal(row.get("Hours")),
        f"{TABLE_PREFIX}_billamountbc": convert_to_decimal(row.get("BillAmountBC")),
        f"{TABLE_PREFIX}_billableamountbc": convert_to_decimal(row.get("BillableAmountBC")),
        f"{TABLE_PREFIX}_localcurrency": row.get("LocalCurrency") or None,
        f"{TABLE_PREFIX}_billamountlc": convert_to_decimal(row.get("BillAmountLC")),
        f"{TABLE_PREFIX}_billableamountlc": convert_to_decimal(row.get("BillableAmountLC"))
    }


def read_csv_records(csv_file_path):
    """Read CSV file and convert to Dataverse records"""
    logger = get_logger()
    logger.info(f"Reading CSV from: {csv_file_path}")
    records = []
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data = map_csv_row_to_dataverse(row)
            records.append(data)
    return records


def upload_batch(token, batch):
    """Upload a batch of records to Dataverse"""
    batch_id = str(uuid.uuid4())
    changeset_id = str(uuid.uuid4())

    # Build batch request body
    batch_body = f"--batch_{batch_id}\n"
    batch_body += f"Content-Type: multipart/mixed; boundary=changeset_{changeset_id}\n\n"

    for idx, record in enumerate(batch):
        batch_body += f"--changeset_{changeset_id}\n"
        batch_body += "Content-Type: application/http\n"
        batch_body += "Content-Transfer-Encoding: binary\n"
        batch_body += f"Content-ID: {idx + 1}\n\n"
        batch_body += f"POST {DATAVERSE_URL}/api/data/v9.2/{TABLE_NAME} HTTP/1.1\n"
        batch_body += "Content-Type: application/json; charset=utf-8\n\n"
        batch_body += f"{requests.compat.json.dumps(record)}\n"

    batch_body += f"--changeset_{changeset_id}--\n"
    batch_body += f"--batch_{batch_id}--\n"

    # Send batch request
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/mixed; boundary=batch_{batch_id}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0"
    }

    url = f"{DATAVERSE_URL}/api/data/v9.2/$batch"
    response = requests.post(url, headers=headers, data=batch_body)

    return response


def parse_date(date_string):
    """Parse date string in various formats to YYYY-MM-DD"""
    from datetime import datetime

    if not date_string:
        return None

    # Common date formats
    formats = [
        "%m/%d/%Y",  # 5/30/2025
        "%Y-%m-%d",  # 2025-05-30
        "%m-%d-%Y",  # 5-30-2025
        "%Y/%m/%d",  # 2025/05/30
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_string.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def filter_records_by_date(records, start_date, end_date):
    """Filter records to only include those within the date range"""
    from datetime import datetime

    if not start_date or not end_date:
        return records

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    filtered_records = []
    for record in records:
        date_field = record.get(f"{TABLE_PREFIX}_date")
        if date_field:
            parsed_date = parse_date(date_field)
            if parsed_date:
                record_dt = datetime.strptime(parsed_date, "%Y-%m-%d")
                if start_dt <= record_dt <= end_dt:
                    filtered_records.append(record)

    return filtered_records


def upload_to_dataverse(csv_file_path, start_date=None, end_date=None):
    """
    Read CSV and upload data to Dataverse table using batch requests

    Args:
        csv_file_path: Path to the CSV file
        start_date: Optional start date (YYYY-MM-DD) to filter records
        end_date: Optional end date (YYYY-MM-DD) to filter records
    """
    logger = get_logger()
    logger.info("=== Uploading to Dataverse ===")

    # Get authentication token
    logger.info("Authenticating to Dataverse...")
    token = get_dataverse_token()

    # Read CSV file and prepare all records
    records = read_csv_records(csv_file_path)

    # Filter by date range if specified
    if start_date and end_date:
        logger.info(f"Filtering records between {start_date} and {end_date}...")
        records = filter_records_by_date(records, start_date, end_date)

    total_records = len(records)
    logger.info(f"Found {total_records} records to upload")

    if total_records == 0:
        logger.warning("No records to upload")
        return

    # Upload in batches
    row_count = 0
    for i in range(0, total_records, BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        response = upload_batch(token, batch)

        if response.status_code in [200, 201, 204]:
            batch_count = len(batch)
            row_count += batch_count
            logger.info(f"  Uploaded batch {i // BATCH_SIZE + 1}: {batch_count} records (Total: {row_count}/{total_records})")
        else:
            logger.error(f"  Error uploading batch {i // BATCH_SIZE + 1}: {response.status_code} - {response.text[:500]}")

    logger.info(f"✓ Successfully uploaded {row_count} rows to Dataverse table '{TABLE_NAME}'")


def delete_records_in_date_range(start_date, end_date, date_field_name=None):
    """
    Delete all records from the table where the date is within the specified range

    Args:
        start_date: Start date in format 'YYYY-MM-DD'
        end_date: End date in format 'YYYY-MM-DD'
        date_field_name: Name of the date field to filter on (default: cr834_date)
    """
    logger = get_logger()

    if date_field_name is None:
        date_field_name = f"{TABLE_PREFIX}_date"

    logger.info(f"=== Deleting Records Between {start_date} and {end_date} ===")

    # Get authentication token
    logger.info("Authenticating to Dataverse...")
    token = get_dataverse_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json"
    }

    # Query for records in the date range
    primary_key_field = f"{TABLE_NAME.rstrip('s')}id"
    filter_query = f"?$filter={date_field_name} ge '{start_date}' and {date_field_name} le '{end_date}'&$select={primary_key_field}"
    url = f"{DATAVERSE_URL}/api/data/v9.2/{TABLE_NAME}{filter_query}"

    logger.info(f"Fetching records where {start_date} <= {date_field_name} <= {end_date}...")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.error(f"Error fetching records: {response.status_code} - {response.text}")
        return

    records = response.json().get('value', [])
    total_records = len(records)

    if total_records == 0:
        logger.info(f"No records found in date range {start_date} to {end_date}")
        return

    logger.info(f"Found {total_records} records to delete")

    # Delete records in batches
    deleted_count = 0
    DELETE_BATCH_SIZE = BATCH_SIZE * 10
    for i in range(0, total_records, DELETE_BATCH_SIZE):
        batch = records[i:i + DELETE_BATCH_SIZE]
        batch_id = str(uuid.uuid4())
        changeset_id = str(uuid.uuid4())

        # Build batch delete request body
        batch_body = f"--batch_{batch_id}\n"
        batch_body += f"Content-Type: multipart/mixed; boundary=changeset_{changeset_id}\n\n"

        for idx, record in enumerate(batch):
            record_id = record[primary_key_field]
            batch_body += f"--changeset_{changeset_id}\n"
            batch_body += "Content-Type: application/http\n"
            batch_body += "Content-Transfer-Encoding: binary\n"
            batch_body += f"Content-ID: {idx + 1}\n\n"
            batch_body += f"DELETE {DATAVERSE_URL}/api/data/v9.2/{TABLE_NAME}({record_id}) HTTP/1.1\n\n"

        batch_body += f"--changeset_{changeset_id}--\n"
        batch_body += f"--batch_{batch_id}--\n"

        # Send batch delete request
        delete_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/mixed; boundary=batch_{batch_id}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0"
        }

        url = f"{DATAVERSE_URL}/api/data/v9.2/$batch"
        response = requests.post(url, headers=delete_headers, data=batch_body)

        if response.status_code in [200, 201, 204]:
            batch_count = len(batch)
            deleted_count += batch_count
            logger.info(f"  Deleted batch {i // DELETE_BATCH_SIZE + 1}: {batch_count} records (Total: {deleted_count}/{total_records})")
        else:
            logger.error(f"  Error deleting batch {i // DELETE_BATCH_SIZE + 1}: {response.status_code} - {response.text[:500]}")

    logger.info(f"✓ Successfully deleted {deleted_count} records from table '{TABLE_NAME}'")


def delete_records_after_date(date_string, date_field_name=None):
    """
    Delete all records from the table where the date is after the specified date

    Args:
        date_string: Date in format 'YYYY-MM-DD' (e.g., '2024-01-01')
        date_field_name: Name of the date field to filter on (default: cr834_date)
    """
    logger = get_logger()

    if date_field_name is None:
        date_field_name = f"{TABLE_PREFIX}_date"

    logger.info(f"=== Deleting Records After {date_string} ===")

    # Get authentication token
    logger.info("Authenticating to Dataverse...")
    token = get_dataverse_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json"
    }

    # Query for records after the specified date
    # Note: Date format in OData filter should be YYYY-MM-DD
    # Primary key is usually: {table_logical_name}id
    primary_key_field = f"{TABLE_NAME.rstrip('s')}id"
    filter_query = f"?$filter={date_field_name} gt '{date_string}'&$select={primary_key_field}"
    url = f"{DATAVERSE_URL}/api/data/v9.2/{TABLE_NAME}{filter_query}"

    logger.info(f"Fetching records where {date_field_name} > {date_string}...")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.error(f"Error fetching records: {response.status_code} - {response.text}")
        return

    records = response.json().get('value', [])
    total_records = len(records)

    if total_records == 0:
        logger.info(f"No records found with {date_field_name} after {date_string}")
        return

    logger.info(f"Found {total_records} records to delete")

    # Delete records in batches
    deleted_count = 0
    DELETE_BATCH_SIZE = BATCH_SIZE*10
    for i in range(0, total_records, DELETE_BATCH_SIZE):
        batch = records[i:i + DELETE_BATCH_SIZE]
        batch_id = str(uuid.uuid4())
        changeset_id = str(uuid.uuid4())

        # Build batch delete request body
        batch_body = f"--batch_{batch_id}\n"
        batch_body += f"Content-Type: multipart/mixed; boundary=changeset_{changeset_id}\n\n"

        for idx, record in enumerate(batch):
            record_id = record[primary_key_field]
            batch_body += f"--changeset_{changeset_id}\n"
            batch_body += "Content-Type: application/http\n"
            batch_body += "Content-Transfer-Encoding: binary\n"
            batch_body += f"Content-ID: {idx + 1}\n\n"
            batch_body += f"DELETE {DATAVERSE_URL}/api/data/v9.2/{TABLE_NAME}({record_id}) HTTP/1.1\n\n"

        batch_body += f"--changeset_{changeset_id}--\n"
        batch_body += f"--batch_{batch_id}--\n"

        # Send batch delete request
        delete_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/mixed; boundary=batch_{batch_id}",
            "OData-MaxVersion": "4.0",
            "OData-Version": "4.0"
        }

        url = f"{DATAVERSE_URL}/api/data/v9.2/$batch"
        response = requests.post(url, headers=delete_headers, data=batch_body)

        if response.status_code in [200, 201, 204]:
            batch_count = len(batch)
            deleted_count += batch_count
            logger.info(f"  Deleted batch {i // DELETE_BATCH_SIZE + 1}: {batch_count} records (Total: {deleted_count}/{total_records})")
        else:
            logger.error(f"  Error deleting batch {i // DELETE_BATCH_SIZE + 1}: {response.status_code} - {response.text[:500]}")

    logger.info(f"✓ Successfully deleted {deleted_count} records from table '{TABLE_NAME}'")
