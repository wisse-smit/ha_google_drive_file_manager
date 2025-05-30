from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from homeassistant.exceptions import HomeAssistantError

from .create_sensor import async_create_or_update_drive_files_sensor

import os
from datetime import datetime, timezone, timedelta
import mimetypes
import logging

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

def generate_full_fields_filter(fields: str, mandatory_fields: list = []) -> str:
    """Generate a full fields filter for Google Drive API requests including mandatory parameters.
    Args:
        fields (str): The fields to include in the response from the Google Drive API.
        mandatory_id (bool): If True, ensures that the 'id' field is always included in the fields.
    Returns:
        str: A string representing the full fields filter for the Google Drive API.
    """

    # Check if the id field is mandatory
    if mandatory_fields:

        # Extract the currently provided fields
        fields_list = [field.strip() for field in fields.split(",")]

        # If the mandatory field is not in the fields, add it
        for mandatory_field in mandatory_fields:
            if mandatory_field not in fields_list:
                fields_list.append(mandatory_field)

        # Join the fields back into a string
        fields = ",".join(fields_list)

    return fields

#region List files by pattern
def get_list_files_by_pattern(credentials, query: str, fields: str, sort_by_recent: bool, maximum_files: int) -> dict:
    """Standard blocking function to get files from Google Drive matching a pattern.

    Args:
        credentials: The credentials object to access Google Drive.
        pattern (str): The pattern to filter filenames.

    Returns:
        dict: The response from the Google Drive API containing the list of files matching the pattern.
    """
    drive_service = build("drive", "v3", credentials=credentials)

    # Parse the fields to include in the response
    fields = generate_full_fields_filter(fields)

    # Set the response fields, including nextPageToken to handle pagination
    response_fields = f"nextPageToken, files({fields})"

    all_files = []
    page_token = None

    while True:
        # Prepare request parameters
        request_params = {
            'q': query,
            'fields': response_fields,
            'pageToken': page_token
        }

        # If sort_by_recent is True, order by modifiedTime descending
        if sort_by_recent:
            request_params['orderBy'] = 'modifiedTime desc'

        # If maximum_files is specified, limit the number of items returned
        if maximum_files:
            # Use pageSize to avoid fetching too many items at once
            # Google Drive API max pageSize is 1000
            page_size = min(maximum_files, 1000)
            request_params['pageSize'] = page_size

        request = drive_service.files().list(**request_params)
        response = request.execute()

        files = response.get('files', [])

        # If max items is set, check how many files we already have and still have to get
        if maximum_files:
            remaining = maximum_files - len(all_files)
            all_files.extend(files[:remaining])
        # If max items is not set, just extend the list with all files
        else:
            all_files.extend(files)

        # Stop if we've collected enough or no more pages
        if maximum_files and len(all_files) >= maximum_files:
            break
        page_token = response.get('nextPageToken')
        if not page_token:
            break

    return {'files': all_files}

async def async_get_list_files_by_pattern(
    hass, 
    credentials, 
    query: str, 
    fields: str, 
    sensor_name: str,
    sort_by_recent: bool,
    maximum_files: int) -> None:
    """Async function to get mp4 files from Google Drive and log results."""

    try:
        # Offload the blocking call to the executor
        results = await hass.async_add_executor_job(
            get_list_files_by_pattern, credentials, query, fields, sort_by_recent, maximum_files
        )

        files = results.get("files", [])
        if files:
            _LOGGER.warning(f"Found {len(files)} matching file(s)")
        else:
            _LOGGER.warning("No matching files found in Google Drive.")

        # Create or update the sensor with the list of files

        # Set the state to the number of files.
        state = len(files)

        # Set the attributes for the sensor.
        attributes = {
            "files": files,
            "friendly_name": sensor_name,
            "icon": "mdi:google-drive",
        }

        await async_create_or_update_drive_files_sensor(hass, sensor_name, state, attributes)
    
    except HomeAssistantError:
        raise  

    except Exception as e:
        _LOGGER.error("Error retrieving list of files from Google Drive: %s", e, exc_info=True)
        raise HomeAssistantError(f"List files failed: {e}") from e
#endregion

#region Upload media file
def verify_file_path_exists(file_path: str) -> None:
    
    # If the file path is empty, raise an error
    if not os.path.isfile(file_path):
        _LOGGER.error(
            f"upload_media_file: path '{file_path}' is not a valid file"
        )
        raise HomeAssistantError(
            f"Local file '{file_path}' does not exist or is not a file. "
            "Please check the path and try again."
        )
    
def get_mime_type_from_path(file_path: str) -> str:
    """Return a MIME type suitable for Drive uploads.

    Falls back to application/octet-stream if the type is unknown.
    """
    mime, _ = mimetypes.guess_type(file_path, strict=False)
    return mime or "application/octet-stream"

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
                    fields: str,
                    mime_type: str = None, 
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
        fields: (str): The fields to include in the response from the Google Drive API.


    Returns:
        dict: The response from the Google Drive API after the upload.
    """

    # Verify the local file path exists - Exit if not
    verify_file_path_exists(local_file_path)

    drive_service = build("drive", "v3", credentials=credentials)

    # If no MIME type is provided, try to guess it based on the file extension
    if not mime_type:
        mime_type = get_mime_type_from_path(local_file_path)
        
    # Set up the media file upload
    media = MediaFileUpload(local_file_path, mimetype=mime_type, resumable=True)

    file_metadata = {}
    
    # Set the remote (Drive) filename is provided (should always be the case)
    if remote_file_name:
        file_metadata["name"] = remote_file_name

    # Extract the remote folder based on the folder path
    if remote_folder_path:
        folder_id = extract_folder_id_from_path(hass, credentials, remote_folder_path)

        # Set the folder ID in the metadata so the file is uploaded to the correct folder
        file_metadata["parents"] = [folder_id]

    # fields to include in the response
    fields = generate_full_fields_filter(fields)

    # Initiate the file upload request
    request = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields=fields
    )

    # Execute the upload iteratively until complete
    response = None

    while response is None:
        _, response = request.next_chunk()
    
    return response

async def async_upload_media_file(hass, 
                                  credentials, 
                                  local_file_path: str, 
                                  mime_type: str, 
                                  remote_file_name: str, 
                                  remote_folder_path: str,
                                  save_to_sensor: bool,
                                  sensor_name: str,
                                  fields: str
                                  ) -> None:
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
        save_to_sensor (bool): Whether to save the uploaded file information to a sensor.
        sensor_name (str): The name of the sensor to save the uploaded file information.
        fields (str): The fields to include in the response from the Google Drive API.

    Returns:
        None: This function does not return a value. It logs the result of the 
        upload operation.
    """
    
    try:

        # If no remote file name is provided, use the local file name as the remote file name
        if not remote_file_name:
            # Extract the file name from the local file path including the file extension
            remote_file_name_with_extension = local_file_path.split("/")[-1]
            # Remove the file extension from the remote file name
            remote_file_name = remote_file_name_with_extension.split(".")[0]


        # Offload the blocking call to the executor
        response = await hass.async_add_executor_job(
            upload_media_file, 
            hass, 
            credentials, 
            local_file_path,
            fields, 
            mime_type, 
            remote_file_name, 
            remote_folder_path
            )

        _LOGGER.info("File uploaded successfully")

        # Check if the results should be written to a sensor
        if save_to_sensor:
            
            # Set the state to the name of the remote file
            state = remote_file_name

            # Create or update the sensor with the uploaded file information
            await async_create_or_update_drive_files_sensor(
                hass, 
                sensor_name, 
                state,
                response
            )


    except HomeAssistantError:
        # already user-friendly (verify_file_path_exists or get_mime_type_from_path)
        raise  

    except Exception as e:
        _LOGGER.error("Error uploading file to Google Drive: %s", e, exc_info=True)
        raise HomeAssistantError(f"Drive upload failed: {e}") from e

#endregion

#region Cleanup Drive files
def cleanup_older_files_by_pattern(credentials, pattern: str, days_ago: int, preview: bool, fields: str) -> list[str]:
    """Delete files in Drive whose name matches `pattern` and are older than `days_ago`.

    Args:
        credentials: Authorized Google credentials.
        pattern (str): Substring to match in file names (uses Drive `name contains` query).
        days_ago (int): Maximum file age in days; any file created before now-days_ago will be deleted.
        preview (bool): If True, only log the files that would be deleted without actually deleting them.
        fields (str): The fields to include in the response from the Google Drive API.

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

    # Generate the full fields filter, ensuring 'id' is always included
    fields = generate_full_fields_filter(fields, mandatory_fields=["id", "name"])

    while True:
        response = drive.files().list(
            q=query,
            fields=f"nextPageToken, files({fields})",
            pageToken=page_token,
        ).execute()

        # Get the files from the Google Drive response
        files = response.get("files", [])

        # Iterate over the files and process them
        for file in files:
            # Check if the preview parameter is set to False, in that case execute deletion
            if not preview:
                drive.files().delete(fileId=file["id"]).execute()

            deleted.append(file["name"])

        # check if there is a next page token, if not, break the loop
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return deleted

async def async_cleanup_older_files_by_pattern(
        hass, 
        credentials, 
        pattern: str, 
        days_ago: int, 
        preview: bool, 
        save_to_sensor: bool, 
        sensor_name: str, 
        fields: str) -> None:
    """Async wrapper to delete old Drive files and log the outcome.

    Usage: await async_cleanup_older_files_by_pattern(hass, creds, "camera", 30)
    """
    try:
        deleted = await hass.async_add_executor_job(
            cleanup_older_files_by_pattern, credentials, pattern, days_ago, preview, fields
        )
        if deleted:
            names = ", ".join(deleted)
            _LOGGER.warning(
                "Deleted %d Drive file(s) older than %d days matching '%s': %s",
                len(deleted), days_ago, pattern, names
            )
        else:
            _LOGGER.info("No Drive files older than %d days matching '%s' found.", days_ago, pattern)

        # Check if the results should be written to a sensor
        if save_to_sensor:
            
            # Set the state to the number of deleted files
            state = len(deleted)

            # Set the attributes for the sensor.
            attributes = {
                "files": deleted,
                "friendly_name": sensor_name,
                "icon": "mdi:google-drive",
            }

            # Create or update the sensor with the uploaded file information
            await async_create_or_update_drive_files_sensor(
                hass, 
                sensor_name, 
                state,
                attributes
            )
    
    except HomeAssistantError:
        raise  

    except Exception as e:
        _LOGGER.error(
                    "Error cleaning up Drive files older than %d days matching '%s': %s",
                    days_ago, pattern, e, exc_info=True
                )        
        raise HomeAssistantError(f"Cleaning older files failed: {e}") from e
#endregion