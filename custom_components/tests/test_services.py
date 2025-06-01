from custom_components.google_drive_file_manager.helpers.google_drive_actions import (
    get_list_files_by_pattern,
    upload_media_file,
    cleanup_older_files_by_pattern
)
from custom_components.tests.get_google_credentials import get_google_drive_credentials


if __name__ == "__main__":

    # Get the credentials
    google_drive_credentials = get_google_drive_credentials()

    # Mock the Home Assistant object so the code doesnt crash
    class hass_object:
        def __init__(self):
            self.data = {}
    
    # Write a temp file to simulate a media file
    test_file_path_to = "custom_components/tests"
    test_file_file_name_local = "test_file"
    test_file_base_name_drive = "f8fasd89faw4rjl32fkjwjlfasdfjklasf"

    # Define the number of test files to create
    test_file_n = 3

    # Clean up older files by pattern
    response = cleanup_older_files_by_pattern(
        credentials=google_drive_credentials,
        pattern=f"name contains '{test_file_base_name_drive}' and trashed = false",
        days_ago=0,
        preview=False,
        fields="id, name, mimeType",
    )

    # Create three files
    for i in range(test_file_n):
        # Set the full file path
        full_file_path = f"{test_file_path_to}/{test_file_file_name_local}_{i}.txt"
        
        # Write a test file
        with open(full_file_path, "wb") as f:
            f.write(b"Test video content")

        # Upload a media file to Google Drive
        response = upload_media_file(
            credentials=google_drive_credentials,
            hass=hass_object(),
            local_file_path=full_file_path,
            fields="id, name, mimeType, size, modifiedTime",
            remote_file_name=f"{test_file_base_name_drive}-{i}.txt",
            remote_folder_path="pytest"
        )

        assert response is not None, "Upload failed"

        # Run the tests for the uploads
        assert response.get("id") is not None, "Response does not contain file ID"
        assert response.get("name") == f"{test_file_base_name_drive}-{i}.txt", "File name does not match"
        assert response.get("mimeType") == "text/plain", "MIME type does not match"
        assert response.get("size") == "18", "Response does not contain file size"

    # Get list of files by pattern from Google Drive

    # Sorted by recent files
    found_files_sort_by_recent = get_list_files_by_pattern(
        credentials=google_drive_credentials,
        query=f"name contains '{test_file_base_name_drive}' and trashed = false",
        fields="id, name, modifiedTime",
        sort_by_recent=True,
        maximum_files=10
    )
    found_files_sorted_by_recent = found_files_sort_by_recent.get("files", [])

    # Sorted by name
    found_files_sort_by_name = get_list_files_by_pattern(
        credentials=google_drive_credentials,
        query=f"name contains '{test_file_base_name_drive}' and trashed = false",
        fields="id, name, modifiedTime",
        sort_by_recent=False,
        maximum_files=10
    )
    found_files_sorted_by_name = found_files_sort_by_name.get("files", [])

    assert len(found_files_sorted_by_recent) == test_file_n, "Did not find the expected number of files sorted by recent"
    assert len(found_files_sorted_by_name) == test_file_n, "Did not find the expected number of files sorted by name"
    assert found_files_sorted_by_name != found_files_sorted_by_recent, "Files sorted by name and recent should not be the same"

    # Delete the files created

    # First test if the preview option still works
    preview_response = cleanup_older_files_by_pattern(
        credentials=google_drive_credentials,
        pattern=f"name contains '{test_file_base_name_drive}' and trashed = false",
        days_ago=0,
        preview=True,
        fields="id, name, mimeType",
    )
    assert type(preview_response) is list, "Preview failed"

    # Check if the files are still there
    found_files = get_list_files_by_pattern(
        credentials=google_drive_credentials,
        query=f"name contains '{test_file_base_name_drive}' and trashed = false",
        fields="id, name, modifiedTime",
        sort_by_recent=False,
        maximum_files=10
    )

    assert len(preview_response) == test_file_n, "Preview did not return the expected number of files"
    assert len(found_files.get("files", [])) == test_file_n, "Did not find the expected number of files, preview failed"
    
    # Clean up older files by pattern - should not remove anything (files are not older than 1 day)
    delete_response = cleanup_older_files_by_pattern(
        credentials=google_drive_credentials,
        pattern=f"name contains '{test_file_base_name_drive}' and trashed = false",
        days_ago=1,
        preview=False,
        fields="id, name, mimeType",
    )

    assert type(delete_response) is list, "Cleanup failed"
    assert len(delete_response) == 0, "Deleted files, even though it shouldn't have"



    # Clean up test files by pattern (days_ago=0)
    delete_response = cleanup_older_files_by_pattern(
        credentials=google_drive_credentials,
        pattern=f"name contains '{test_file_base_name_drive}' and trashed = false",
        days_ago=0,
        preview=False,
        fields="id, name, mimeType",
    )

    assert type(delete_response) is list, "Cleanup failed"
    assert len(delete_response) == test_file_n, "Did not delete the expected number of files"

    # Check if the files are deleted
    found_files = get_list_files_by_pattern(
        credentials=google_drive_credentials,
        query=f"name contains '{test_file_base_name_drive}' and trashed = false",
        fields="id, name, modifiedTime",
        sort_by_recent=False,
        maximum_files=10
    )

    assert len(found_files.get("files", [])) == 0, "Files were not deleted"