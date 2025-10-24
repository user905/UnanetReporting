"""
Delete records from Dataverse table based on date filter
"""

from dataverse_client import delete_records_after_date
import sys


def main():
    """Delete records with date after the specified date"""

    if len(sys.argv) < 2:
        print("Usage: python delete_records.py YYYY-MM-DD")
        print("Example: python delete_records.py 2024-12-31")
        print("\nThis will delete all records where the date is AFTER the specified date")
        return

    date_string = sys.argv[1]

    # Confirm before deleting
    print(f"WARNING: This will delete ALL records with date > {date_string}")
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() != 'yes':
        print("Deletion cancelled")
        return

    delete_records_after_date(date_string)


if __name__ == "__main__":
    main()
