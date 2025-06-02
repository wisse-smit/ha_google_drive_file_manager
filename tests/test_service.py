# Import the necessary new service here
from custom_components.google_drive_file_manager.helpers.google_drive_actions import (
    upload_media_file, cleanup_older_files_by_pattern
)
from tests.get_google_credentials import get_google_drive_credentials

class HassDummy:
    def __init__(self):
        self.data = {}

hass_dummy = HassDummy()

if __name__ == "__main__":
    
    # Get Google Drive credentials
    google_drive_credentials = get_google_drive_credentials()

    # test_file_path_to = "tests"
    # test_file_file_name_local = "test_file"
    # full_file_path = f"{test_file_path_to}/{test_file_file_name_local}_0.txt"
        
    # # Write a test file
    # with open(full_file_path, "wb") as f:
    #     f.write(b"Test content")

    # # Upload a media file to Google Drive
    # response = upload_media_file(
    #     credentials=google_drive_credentials,
    #     hass=hass_dummy,
    #     local_file_path=full_file_path,
    #     fields="id, name, mimeType, size, modifiedTime",
    #     remote_file_name=full_file_path.split("/")[-1].split(".")[0],
    #     remote_folder_path="",
    #     append_ymd_path=True
    # )

    # print("Uploaded file:", response)

    deleted_files = cleanup_older_files_by_pattern(
        credentials=google_drive_credentials,
        pattern="name contains 'E1 Outdoor_' or name contains 'E1 Indoor_'",
        days_ago=30,
        preview=True,
        fields="id, name, mimeType, size, modifiedTime",
    )
