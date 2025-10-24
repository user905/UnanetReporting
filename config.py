import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# When running as EXE, .env should be in the same directory as the executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = Path(sys.executable).parent
else:
    # Running as script
    application_path = Path(__file__).parent

env_path = application_path / '.env'
load_dotenv(dotenv_path=env_path)

# === UNANET CONFIG ===
UNANET_URL = os.getenv('UNANET_URL', 'https://goaztech.unanet.biz')
UNANET_USERNAME = os.getenv('UNANET_USERNAME', '')
UNANET_PASSWORD = os.getenv('UNANET_PASSWORD', '')
UNANET_REPORT_ID = os.getenv('UNANET_REPORT_ID', 'R_91')

# === DATAVERSE/POWERAPPS CONFIG ===
DATAVERSE_URL = os.getenv('DATAVERSE_URL', 'https://org4bd86d49.crm.dynamics.com')
DATAVERSE_USERNAME = os.getenv('DATAVERSE_USERNAME', '')
DATAVERSE_PASSWORD = os.getenv('DATAVERSE_PASSWORD', '')
TABLE_PREFIX = os.getenv('TABLE_PREFIX', 'cr834')
TABLE_NAME = os.getenv('TABLE_NAME', f"{TABLE_PREFIX}_eacdataraws")

# === FILE PATHS ===
PROJECT_DIR = application_path
DOWNLOAD_DIR = PROJECT_DIR / "reports"

# === BATCH SETTINGS ===
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '500'))
