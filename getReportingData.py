from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path
import csv
import requests
from msal import PublicClientApplication
import uuid

# === CONFIG ===
UNANET_URL = "https://goaztech.unanet.biz"
UNANET_USERNAME = "afearnley"
UNANET_PASSWORD = "Welcome1!"

# Dataverse/PowerApps config
DATAVERSE_URL = "https://org4bd86d49.crm.dynamics.com"
DATAVERSE_USERNAME = "elias@goaztech.com"  # Your Microsoft 365 email
DATAVERSE_PASSWORD = "RunAzTech=1234"  # Your Microsoft 365 password
TABLE_PREFIX = "cr834"  # PowerApps table prefix
TABLE_NAME = f"{TABLE_PREFIX}_tests"  # PowerApps table logical name

# Get the project directory and create reports subdirectory
PROJECT_DIR = Path(__file__).parent
DOWNLOAD_DIR = PROJECT_DIR / "reports"
REPORT_NAME = "EAC Master Report Monthly (SHARED)"  # or whatever you see in the alt/title tag



def run():
    # Create reports directory if it doesn't exist
    DOWNLOAD_DIR.mkdir(exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    final_path = DOWNLOAD_DIR / f"unanet_report_{today}.csv"

    # Check if today's report already exists
    if final_path.exists():
        print(f"Found existing report from today: {final_path}")
        print("Using existing file instead of downloading from Unanet")
        return final_path

    # Download from Unanet if no file exists for today
    print("No report found for today, downloading from Unanet...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # === LOGIN ===
        page.goto(f"{UNANET_URL}/goaztech/")
        page.fill('input[name="username"]', UNANET_USERNAME)
        page.fill('input[name="password"]', UNANET_PASSWORD)
        page.click('#button_ok')  # ✅ click the button by ID
        page.wait_for_load_state("networkidle")

        # === SAVED REPORTS PAGE ===
        page.goto(f"{UNANET_URL}/goaztech/action/reports/saved")

        # === CLICK RUN ON REPORT R_91 ===
        print("Clicking run on saved report...")
        page.click('tr#R_91 td.icon a[href*="runReport"]')

        # === WAIT FOR REPORT PAGE TO LOAD ===
        print("Waiting for report data to load...")
        page.wait_for_selector('a[href*="doCSVFile"]', timeout=60000)  # Change if another element is more reliable

        # === DOWNLOAD CSV ===
        print("Downloading CSV...")
        with page.expect_download() as download_info:
            page.click('a[href*="doCSVFile"]')  # This triggers javascript:doCSVFile()

        download = download_info.value
        download.save_as(final_path)
        print(f"Downloaded to: {final_path}")

        browser.close()

    return final_path


def get_dataverse_token():
    """Authenticate to Dataverse using username/password"""
    # Microsoft Dynamics 365 client ID (public client for username/password flow)
    client_id = "51f81489-12ee-4a9e-aaae-a2591f45987d"  # Common Dynamics 365 client ID
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


def upload_to_dataverse(csv_file_path):
    """Read CSV and upload data to Dataverse table using batch requests"""
    print("\n=== Uploading to Dataverse ===")

    # Get authentication token
    print("Authenticating to Dataverse...")
    token = get_dataverse_token()

    # Read CSV file and prepare all records
    print(f"Reading CSV from: {csv_file_path}")
    records = []
    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Map CSV columns to Dataverse columns using the prefix variable
            data = {
                f"{TABLE_PREFIX}_projectorganization": row.get("ProjectOrganization", ""),
                f"{TABLE_PREFIX}_projectcode": row.get("ProjectCode", ""),
                f"{TABLE_PREFIX}_tasknumber": row.get("TaskNumber", ""),
                f"{TABLE_PREFIX}_task": row.get("Task", ""),
                f"{TABLE_PREFIX}_laborcategory": row.get("LaborCategory", ""),
                f"{TABLE_PREFIX}_location": row.get("Location", ""),
                f"{TABLE_PREFIX}_projecttype": row.get("ProjectType", ""),
                f"{TABLE_PREFIX}_paycode": row.get("PayCode", ""),
                f"{TABLE_PREFIX}_person": row.get("Person", ""),
                f"{TABLE_PREFIX}_reference": row.get("Reference", ""),
                f"{TABLE_PREFIX}_date": row.get("Date", ""),
                f"{TABLE_PREFIX}_adjposteddate": row.get("ADJPostedDate", ""),
                f"{TABLE_PREFIX}_financialposteddate": row.get("FinancialPostedDate", ""),
                f"{TABLE_PREFIX}_billingcurrency": row.get("BillingCurrency", ""),
                f"{TABLE_PREFIX}_billratebc": row.get("BillRateBC", ""),
                f"{TABLE_PREFIX}_hours": row.get("Hours", ""),
                f"{TABLE_PREFIX}_billamountbc": row.get("BillAmountBC", ""),
                f"{TABLE_PREFIX}_billableamountbc": row.get("BillableAmountBC", ""),
                f"{TABLE_PREFIX}_localcurrency": row.get("LocalCurrency", ""),
                f"{TABLE_PREFIX}_billamountlc": row.get("BillAmountLC", ""),
                f"{TABLE_PREFIX}_billableamountlc": row.get("BillableAmountLC", "")
            }
            records.append(data)

    total_records = len(records)
    print(f"Found {total_records} records to upload")

    # Upload in batches of 100 (Dataverse batch limit is 1000, but 100 is safer)
    BATCH_SIZE = 100
    row_count = 0

    for i in range(0, total_records, BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
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

        if response.status_code in [200, 201, 204]:
            batch_count = len(batch)
            row_count += batch_count
            print(f"  Uploaded batch {i // BATCH_SIZE + 1}: {batch_count} records (Total: {row_count}/{total_records})")
        else:
            print(f"  Error uploading batch {i // BATCH_SIZE + 1}: {response.status_code} - {response.text[:500]}")

    print(f"\n✓ Successfully uploaded {row_count} rows to Dataverse table '{TABLE_NAME}'")


if __name__ == "__main__":
    # Download the report from Unanet
    csv_path = run()

    # Upload to Dataverse if credentials are configured
    if DATAVERSE_USERNAME and DATAVERSE_PASSWORD:
        upload_to_dataverse(csv_path)
    else:
        print("\nSkipping Dataverse upload - credentials not configured")
        print("Please set DATAVERSE_USERNAME and DATAVERSE_PASSWORD in the script")