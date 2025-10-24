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

### Prerequisites

- Python 3.8+
- Chrome/Chromium browser (for Playwright)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/UnanetReporting.git
   cd UnanetReporting
   ```

2. Install required packages:
   ```bash
   pip install playwright msal requests
   ```

3. Install Playwright browsers:
   ```bash
   python -m playwright install
   ```

4. Configure credentials in `config.py`:
   - Update Unanet credentials
   - Update Dataverse/PowerApps credentials
   - Update table prefix and name

## Usage

### Full Workflow

Run the complete process (download + upload):
```bash
python main.py
```

This will:
- Download the latest Unanet report (or use today's cached file)
- Upload all records to Dataverse in batches

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

- ✅ **Batch Processing** - Uploads 100 records per batch for optimal performance
- ✅ **Smart Caching** - Won't re-download reports from the same day
- ✅ **Type Conversion** - Automatically converts strings to proper data types
- ✅ **Error Handling** - Detailed error messages for troubleshooting
- ✅ **Safe Deletes** - Test queries before deleting data
- ✅ **Modular Design** - Separation of concerns for easy maintenance

## Security Notes

⚠️ **IMPORTANT:** The `config.py` file contains sensitive credentials.

**Recommendations:**
- Add `config.py` to `.gitignore` before committing
- Use environment variables for production deployments
- Consider using Azure Key Vault or similar for credential management
- Never commit credentials to version control

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

- [ ] Create standalone executable with PyInstaller
- [ ] Add logging to file
- [ ] Support for multiple reports
- [ ] Scheduled execution (Windows Task Scheduler / cron)
- [ ] Email notifications on success/failure
- [ ] Service Principal authentication option
- [ ] Configuration file encryption

## License

MIT License

## Contact

For questions or issues, please open a GitHub issue or contact the development team.
