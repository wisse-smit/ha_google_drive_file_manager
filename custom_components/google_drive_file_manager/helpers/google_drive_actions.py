from googleapiclient.discovery import build
import logging

_LOGGER = logging.getLogger(__name__)

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