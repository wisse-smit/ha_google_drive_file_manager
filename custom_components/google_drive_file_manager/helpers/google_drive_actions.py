from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from datetime import datetime, timezone, timedelta
import logging
from ..const import DOMAIN


_LOGGER = logging.getLogger(__name__)

#region List mp4 files
def get_list_video_mp4_files(credentials) -> dict:
    """Standard blocking function to get mp4 files from Google Drive.

    Args:
        credentials: The credentials object to access Google Drive.

    Returns:
        dict: The response from the Google Drive API containing the list of mp4 files.
    """
    drive_service = build("drive", "v3", credentials=credentials)
    return drive_service.files().list(
        q="mimeType='video/mp4'",
        fields="files(name)"
    ).execute()

async def async_get_list_video_mp4_files(hass, credentials) -> None:
    """Async function to get mp4 files from Google Drive and log results."""

    try:
        # Offload the blocking call to the executor
        results = await hass.async_add_executor_job(
            get_list_video_mp4_files, credentials
        )

        files = results.get("files", [])
        if files:
            names = ", ".join(f["name"] for f in files)
            _LOGGER.warning("Found %d MP4 file(s): %s", len(files), names)
        else:
            _LOGGER.warning("No MP4 files found in Google Drive.")

    except Exception as e:
        _LOGGER.error("Error retrieving MP4 files from Google Drive: %s", e, exc_info=True)
#endregion

#region List files by pattern
def get_list_files_by_pattern(credentials, query: str, fields: str = "files(name)") -> dict:
    """Standard blocking function to get files from Google Drive matching a pattern.

    Args:
        credentials: The credentials object to access Google Drive.
        pattern (str): The pattern to filter filenames.

    Returns:
        dict: The response from the Google Drive API containing the list of files matching the pattern.
    """
    drive_service = build("drive", "v3", credentials=credentials)
    return drive_service.files().list(
        q=query,
        fields=fields
    ).execute()

async def async_get_list_files_by_pattern(hass, credentials, query: str, fields: str) -> None:
    """Async function to get mp4 files from Google Drive and log results."""

    try:
        # Offload the blocking call to the executor
        results = await hass.async_add_executor_job(
            get_list_files_by_pattern, credentials, query, fields
        )

        files = results.get("files", [])
        if files:
            names = ", ".join(f["name"] for f in files)
            _LOGGER.warning("Found %d MP4 file(s): %s", len(files), names)
        else:
            _LOGGER.warning("No MP4 files found in Google Drive.")

    except Exception as e:
        _LOGGER.error("Error retrieving MP4 files from Google Drive: %s", e, exc_info=True)
#endregion

#region Upload media file
def extract_folder_id_from_path(hass, credentials, folder_remote_path: str):
    """Based on a folder path, extract the folder ID from Google Drive.
    It will check the availability of a folder ID in the Home Assistant integration data and return that.
    If not available, it will search for the folder in Google Drive and return the ID.
    If the folder is not found, it will create the folder with the given name and do that until the full path is created.
    Any new folder IDs will be stored in the Home Assistant integration data for future use.

    Args:
        credentials (_type_): Credentials object to access Google Drive.
        folder_remote_path (_type_): A string representing the folder path in Google Drive. Formatted with '/' as a separator.
    """

    drive = build("drive", "v3", credentials=credentials)

    # initialize cache
    cache = hass.data.setdefault(DOMAIN, {})
    folder_cache = cache.setdefault("folder_ids", {})

    # if we've already resolved this full path, return it
    if folder_remote_path in folder_cache:
        return folder_cache[folder_remote_path]

    parent_id = "root"
    segments = folder_remote_path.strip("/").split("/")

    for i, segment in enumerate(segments, start=1):
        subpath = "/".join(segments[:i])
        if subpath in folder_cache:
            parent_id = folder_cache[subpath]
            continue

        # look for an existing folder with this name under parent_id
        q = (
            "mimeType = 'application/vnd.google-apps.folder' and "
            f"name = '{segment.replace('\"', '\\\"')}' and "
            f"'{parent_id}' in parents and trashed = false"
        )
        resp = drive.files().list(q=q, fields="files(id,name)", pageSize=1).execute()
        files = resp.get("files", [])

        if files:
            folder_id = files[0]["id"]
            _LOGGER.debug("Found folder %s → %s", subpath, folder_id)
        else:
            # create the folder
            meta = {
                "name": segment,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            }
            created = drive.files().create(body=meta, fields="id").execute()
            folder_id = created["id"]
            _LOGGER.info("Created folder %s → %s", subpath, folder_id)

        # cache and step into it
        folder_cache[subpath] = folder_id
        parent_id = folder_id

    # return the ID for the full path
    return folder_cache[folder_remote_path]

def upload_media_file(hass, 
                    credentials, 
                    local_file_path: str, 
                    mime_type: str, 
                    remote_file_name: str = None, 
                    remote_folder_path: str = None) -> dict:
    """Uploads a large media file to Google Drive.

    Args:
        hass: The Home Assistant instance used to run the asynchronous task and store the folder ID cache.
        credentials: The credentials object to access Google Drive.
        local_file_path (str): The local path to the media file.
        mime_type (str): The MIME type of the file.
        remote_filename (str): (optional) The desired name for the file in Google Drive.
        remote_folder_path (str): (optional) A filepath in Google Drive to upload the file to.


    Returns:
        dict: The response from the Google Drive API after the upload.
    """

    drive_service = build("drive", "v3", credentials=credentials)

    media = MediaFileUpload(local_file_path, mimetype=mime_type, resumable=True)

    file_metadata = {}
    
    # Set the remote (Drive) filename is provided
    if remote_file_name:
        file_metadata["name"] = remote_file_name

    # Extract the remote folder based on the folder path
    if remote_folder_path:
        folder_id = extract_folder_id_from_path(hass, credentials, remote_folder_path)

        # Set the folder ID in the metadata so the file is uploaded to the correct folder
        file_metadata["parents"] = [folder_id]

    try:
        request = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        )
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                _LOGGER.info("Upload progress: %d%%", int(status.progress() * 100))
        _LOGGER.info("File uploaded successfully, File ID: %s", response.get("id"))
        return response
    except Exception as e:
        _LOGGER.error("Error uploading media file to Google Drive: %s", e, exc_info=True)
        raise

async def async_upload_media_file(hass, 
                                  credentials, 
                                  local_file_path: str, 
                                  mime_type: str, 
                                  remote_file_name: str, 
                                  remote_folder_path: str) -> None:
    """
    Async function to upload a large media file to Google Drive and log results.
    This function offloads the blocking upload operation to an executor and 
    handles the response from the Google Drive API. It logs the success or 
    failure of the upload operation.
    Args:
        hass: The Home Assistant instance used to run the asynchronous task.
        credentials: The credentials object to access Google Drive.
        local_file_path (str): The local path to the media file.
        mime_type (str): The MIME type of the file.
        remote_file_name (str): The desired name for the file in Google Drive.
        remote_folder_path (str): (optional) A filepath in Google Drive to upload the file to.

    Returns:
        None: This function does not return a value. It logs the result of the 
        upload operation.
    """
    
    try:
        # Offload the blocking call to the executor
        response = await hass.async_add_executor_job(
            upload_media_file, hass, credentials, local_file_path, mime_type, remote_file_name, remote_folder_path)

        file_id = response.get("id")
        if file_id:
            _LOGGER.info("File uploaded successfully, File ID: %s", file_id)
        else:
            _LOGGER.warning("File upload completed but no File ID was returned.")

    except Exception as e:
        _LOGGER.error("Error uploading file to Google Drive: %s", e, exc_info=True)
#endregion

#region Cleanup Drive files
def cleanup_drive_files(credentials, pattern: str, days_ago: int, preview: bool = False) -> list[str]:
    """Delete files in Drive whose name matches `pattern` and are older than `days_ago`.

    Args:
        credentials: Authorized Google credentials.
        pattern (str): Substring to match in file names (uses Drive `name contains` query).
        days_ago (int): Maximum file age in days; any file created before now-days_ago will be deleted.
        preview (optional) (bool): If True, only log the files that would be deleted without actually deleting them.

    Returns:
        List of filenames that were deleted.
    """
    drive = build("drive", "v3", credentials=credentials)
    # Compute RFC3339 timestamp threshold
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()

    # Build query: name contains pattern from user, createdTime older than cutoff, not trashed
    query = [
            pattern,
            f"createdTime < '{cutoff}'",
            f"trashed = false"
    ]

    # Remove empty parts from query and join with " and " to create a valid query string
    query = " and ".join([part for part in query if part])

    deleted = []
    page_token = None
    while True:
        response = drive.files().list(
            q=query,
            fields="nextPageToken, files(id, name)",
            pageToken=page_token,
        ).execute()
        files = response.get("files", [])
        for f in files:
            try:
                # Check if the preview parameter is set to False, in that case execute deletion
                if not preview:
                    drive.files().delete(fileId=f["id"]).execute()

                deleted.append(f["name"])
            except HttpError as err:
                _LOGGER.error("Failed to delete '%s' (%s): %s", f["name"], f["id"], err)
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return deleted

async def async_cleanup_drive_files(hass, credentials, pattern: str, days_ago: int, preview: bool = False) -> None:
    """Async wrapper to delete old Drive files and log the outcome.

    Usage: await async_cleanup_drive_files(hass, creds, "camera", 30)
    """
    try:
        deleted = await hass.async_add_executor_job(
            cleanup_drive_files, credentials, pattern, days_ago, preview
        )
        if deleted:
            names = ", ".join(deleted)
            _LOGGER.warning(
                "Deleted %d Drive file(s) older than %d days matching '%s': %s",
                len(deleted), days_ago, pattern, names
            )
        else:
            _LOGGER.info("No Drive files older than %d days matching '%s' found.", days_ago, pattern)
    except Exception as e:
        _LOGGER.error(
            "Error cleaning up Drive files older than %d days matching '%s': %s",
            days_ago, pattern, e, exc_info=True
        )
#endregion