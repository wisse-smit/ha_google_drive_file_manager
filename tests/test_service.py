# Import the necessary new service here
from custom_components.google_drive_file_manager.helpers.google_drive_actions import (
    get_list_files_by_pattern
)
from tests.get_google_credentials import get_google_drive_credentials

if __name__ == "__main__":
    # Get Google Drive credentials
    google_drive_credentials = get_google_drive_credentials()

    # Run the service here using the Google Drive credentials
    found_files = get_list_files_by_pattern(
        credentials=google_drive_credentials,
        query=f"name contains 'test' and trashed = false",
        fields="id, name, modifiedTime",
        sort_by_recent=False,
        maximum_files=10
    )

    print("Found files:", found_files)