"""
Delete records from Dataverse table based on date filter
"""

from dataverse_client import delete_records_after_date
from logger import setup_logger, get_logger
import sys


def main():
    """Delete records with date after the specified date"""
    logger = setup_logger()

    if len(sys.argv) < 2:
        logger.info("Usage: python delete_records.py YYYY-MM-DD")
        logger.info("Example: python delete_records.py 2024-12-31")
        logger.info("This will delete all records where the date is AFTER the specified date")
        return

    date_string = sys.argv[1]

    # Confirm before deleting
    logger.warning(f"WARNING: This will delete ALL records with date > {date_string}")
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() != 'yes':
        logger.info("Deletion cancelled")
        return

    delete_records_after_date(date_string)


if __name__ == "__main__":
    main()
