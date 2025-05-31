from custom_components.google_drive_file_manager.helpers.google_drive_actions import (
    get_list_files_by_pattern,
)
from custom_components.tests.get_google_credentials import get_google_drive_credentials


if __name__ == "__main__":

    # Get the credentials
    credentials = get_google_drive_credentials()

    # Get list of files by pattern from Google Drive
    found_files = get_list_files_by_pattern(
        credentials=credentials,
        query="name contains 'test'",
        fields="id, name, mimeType, size, modifiedTime",
        sort_by_recent=True,
        maximum_files=10
    )

    print(f"Found files: {found_files}")