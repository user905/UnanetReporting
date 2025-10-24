# Unanet to Dataverse Integration

Automated tool to download reports from Unanet and upload them to Microsoft PowerApps/Dataverse.

## Overview

This project automates the process of:
1. Downloading CSV reports from Unanet
2. Parsing and transforming the data
3. Bulk uploading to Microsoft Dataverse/PowerApps tables

## Project Structure

```
UnanetReporting/
├── config.py                  # Configuration settings (credentials, URLs, table names)
├── main.py                    # Main entry point - orchestrates the full workflow
├── unanet_downloader.py       # Handles Unanet report downloads via Playwright
├── dataverse_client.py        # Dataverse API client with batch upload/delete
├── delete_records.py          # Delete records from Dataverse based on date filter
├── test_upload.py             # Test single record upload
├── test_delete.py             # Test delete query (read-only, shows what would be deleted)
├── upload_sample.py           # Upload small sample of records for testing
├── getReportingData.py        # Legacy monolithic script (kept for reference)
└── reports/                   # Directory where CSV reports are stored
    └── template.csv           # Sample CSV structure
```

## Files Description

### Core Files

- **`config.py`**
  Central configuration file containing:
  - Unanet credentials and URL
  - Dataverse/PowerApps credentials and environment URL
  - Table name and prefix
  - Batch size settings

- **`main.py`**
  Main application entry point. Runs the complete workflow:
  1. Downloads report from Unanet (or reuses today's file)
  2. Uploads data to Dataverse

- **`unanet_downloader.py`**
  Downloads reports from Unanet using Playwright browser automation:
  - Logs into Unanet
  - Navigates to saved reports
  - Downloads CSV file
  - Caches downloads by date (won't re-download same day's report)

- **`dataverse_client.py`**
  Handles all Dataverse/PowerApps interactions:
  - Authentication via MSAL
  - CSV to Dataverse field mapping
  - Batch upload (100 records per batch)
  - Batch delete with date filtering
  - Type conversion (strings to decimals, etc.)

### Utility Scripts

- **`delete_records.py`**
  Deletes records from Dataverse table based on date filter.
  Usage: `python delete_records.py 2024-12-31`
  Requires confirmation before deleting.

- **`test_delete.py`**
  Tests delete functionality without actually deleting records.
  Shows sample records and total count that would be affected.
  Usage: `python test_delete.py 2024-12-31`

- **`upload_sample.py`**
  Uploads a small number of records for testing purposes.
  Usage: `python upload_sample.py [num_records]`
  Default: 10 records

- **`test_upload.py`**
  Tests uploading a single record and shows full error messages if any.
  Useful for debugging field mapping issues.

### Legacy Files

- **`getReportingData.py`**
  Original monolithic script before refactoring.
  Kept for reference but not used in current workflow.

## Setup

### Option 1: Using the Executable (Recommended for End Users)

**Prerequisites:**
- Google Chrome browser must be installed on the system

**Steps:**
1. Download the `UnanetSync.exe` file from the `dist/` folder
2. Create a `.env` file in the same directory as the executable with your credentials:
   ```
   UNANET_URL=https://your-instance.unanet.biz
   UNANET_USERNAME=your-username
   UNANET_PASSWORD=your-password
   UNANET_REPORT_ID=R_91

   DATAVERSE_URL=https://your-org.crm.dynamics.com
   DATAVERSE_USERNAME=your-email@domain.com
   DATAVERSE_PASSWORD=your-password
   TABLE_PREFIX=cr834
   TABLE_NAME=cr834_eacdataraws
   BATCH_SIZE=500
   ```
3. Double-click `UnanetSync.exe` to run

**Note:** The executable will create `reports/` and `logs/` directories automatically in the same location.

### Option 2: Running from Source (For Developers)

#### Prerequisites

- Python 3.8+
- Chrome/Chromium browser (for Playwright)

#### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/UnanetReporting.git
   cd UnanetReporting
   ```

2. Install required packages:
   ```bash
   pip install playwright msal requests python-dotenv
   ```

3. Install Playwright browsers:
   ```bash
   python -m playwright install
   ```

4. Create a `.env` file with your credentials (see example above)

### Building the Executable

To rebuild the executable from source:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the executable:
   ```bash
   python -m PyInstaller UnanetSync.spec --clean
   ```

3. The executable will be created in the `dist/` directory

## Usage

### Running the Application

**Using the executable:**
```bash
UnanetSync.exe
```

**Running from source:**
```bash
python main.py
```

This will:
- Delete all Dataverse records from the past 365 days
- Download the latest Unanet report (or use today's cached file)
- Upload only records from the past 365 days to Dataverse in batches
- Create timestamped logs in the `logs/` directory

### Testing Workflow

1. **Upload sample data:**
   ```bash
   python upload_sample.py 10
   ```

2. **Test delete query (without deleting):**
   ```bash
   python test_delete.py 2024-12-31
   ```

3. **Delete records (if test looks good):**
   ```bash
   python delete_records.py 2024-12-31
   ```

### Individual Operations

**Test single record upload:**
```bash
python test_upload.py
```

**Delete records after a specific date:**
```bash
python delete_records.py 2025-01-01
```

## Configuration

### Unanet Settings

In `config.py`:
```python
UNANET_URL = "https://your-instance.unanet.biz"
UNANET_USERNAME = "your-username"
UNANET_PASSWORD = "your-password"
UNANET_REPORT_ID = "R_91"  # The report ID from Unanet
```

### Dataverse Settings

```python
DATAVERSE_URL = "https://your-org.crm.dynamics.com"
DATAVERSE_USERNAME = "your-email@domain.com"
DATAVERSE_PASSWORD = "your-password"
TABLE_PREFIX = "cr834"  # Your environment's table prefix
TABLE_NAME = f"{TABLE_PREFIX}_projecttaskbillings"
```

### Performance Settings

```python
BATCH_SIZE = 100  # Number of records per batch upload
```

## Field Mapping

The script maps CSV columns to Dataverse fields with the configured prefix:

| CSV Column | Dataverse Field |
|------------|-----------------|
| ProjectOrganization | cr834_projectorganization |
| ProjectCode | cr834_projectcode |
| Hours | cr834_hours (decimal) |
| BillAmountBC | cr834_billamountbc (decimal) |
| etc. | ... |

Numeric fields (Hours, BillRate, amounts) are automatically converted from strings to decimals.

## Features

- ✅ **Standalone Executable** - No Python installation required for end users
- ✅ **Rolling 365-Day Window** - Automatically maintains only the past year of data
- ✅ **Batch Processing** - Uploads/deletes up to 1000 records per batch for optimal performance
- ✅ **Pagination Support** - Handles datasets larger than 5000 records
- ✅ **Smart Caching** - Won't re-download reports from the same day
- ✅ **Type Conversion** - Automatically converts strings to proper data types
- ✅ **Comprehensive Logging** - Timestamped logs in `/logs` directory
- ✅ **Error Handling** - Detailed error messages for troubleshooting
- ✅ **Secure Credentials** - Uses `.env` file for sensitive data
- ✅ **Safe Deletes** - Test queries before deleting data
- ✅ **Modular Design** - Separation of concerns for easy maintenance

## Security Notes

⚠️ **IMPORTANT:** The `.env` file contains sensitive credentials.

**Recommendations:**
- The `.env` file is already in `.gitignore` and should NEVER be committed
- Store `.env` securely and share it only through secure channels
- Consider using Azure Key Vault or similar for credential management in enterprise environments
- Each user should create their own `.env` file with their credentials
- When distributing the executable, provide a `.env.template` file with placeholder values

## Troubleshooting

### "Resource not found" error
- Verify `TABLE_NAME` in `config.py` matches your Dataverse table's logical name
- Check that the table name includes the plural form (e.g., "cr834_projecttaskbillings")

### "Invalid property" error
- Verify column names in Dataverse match the prefix in `config.py`
- Check field data types (text vs decimal) in PowerApps

### "Cannot convert to Edm.Decimal" error
- Already fixed in current version with `convert_to_decimal()` function
- Numeric fields are now properly converted to float/decimal

### Authentication failures
- Verify credentials in `config.py`
- Ensure your account has permissions to the Dataverse environment
- Check that MFA is not required (or use Service Principal authentication instead)

## Future Enhancements

- [x] Create standalone executable with PyInstaller
- [x] Add logging to file
- [x] Rolling 365-day data window
- [x] Pagination for large datasets
- [ ] Support for multiple reports
- [ ] Scheduled execution (Windows Task Scheduler / cron)
- [ ] Email notifications on success/failure
- [ ] Service Principal authentication option
- [ ] GUI interface for credential configuration

## License

MIT License

## Contact

For questions or issues, please open a GitHub issue or contact the development team.
