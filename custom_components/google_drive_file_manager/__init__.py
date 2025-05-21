import logging
from functools import partial

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.config_entry_oauth2_flow import (
    async_get_config_entry_implementation,
    async_register_implementation,
    OAuth2Session,
)
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from .oauth2_impl import GoogleDriveOAuth2Implementation
from .helpers.authentication_services import async_get_google_drive_credentials
from .helpers.google_drive_actions import (
    async_get_list_video_mp4_files,
    async_get_list_files_by_pattern,
    async_upload_large_media_file,
    async_cleanup_drive_files,
    )

from .const import DOMAIN, SCOPES, OAUTH2_TOKEN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up Google Drive integration from a config entry."""
    # Re‑instantiate and register our OAuth2 implementation so HA can find it on restart
    implementation = GoogleDriveOAuth2Implementation(
        hass,
        client_id=entry.data["client_id"],
        client_secret=entry.data["client_secret"],
        use_my_redirect=entry.data.get("use_my_redirect", True),
    )
    async_register_implementation(hass, DOMAIN, implementation)

    # Create the OAuth2Session (handles token refresh & storage)
    session = OAuth2Session(hass, entry, implementation)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = session

    async def list_mp4_files(call: ServiceCall) -> None:
        """Service to list mp4 files in Google Drive."""

        # Get valid credentials (auto‑refresh if needed)
        credentials = await async_get_google_drive_credentials(hass, entry)
        # Fetch & log MP4 list
        await async_get_list_video_mp4_files(hass, credentials)

    async def upload_large_media_file(call: ServiceCall) -> None:
        """Service to upload a large media file to Google Drive."""
        # Get valid credentials (auto‑refresh if needed)
        credentials = await async_get_google_drive_credentials(hass, entry)
        # Upload the file
        await async_upload_large_media_file(
            hass,
            credentials,
            call.data["file_path"],
            call.data["mime_type"],
            call.data["folder_id"],
        )

    async def cleanup_drive_files(call: ServiceCall) -> None:
        """Service to clean up files in Google Drive."""
        # Get valid credentials (auto‑refresh if needed)
        credentials = await async_get_google_drive_credentials(hass, entry)
        # Clean up the files
        await async_cleanup_drive_files(
            hass,
            credentials,
            call.data["folder_id"],
            call.data["file_name"],
        )

    async def list_files_by_pattern(call: ServiceCall) -> None:
        """Service to list files by pattern in Google Drive."""
        # Get valid credentials (auto‑refresh if needed)
        credentials = await async_get_google_drive_credentials(hass, entry)
        # List files by pattern
        await async_get_list_files_by_pattern(
            hass,
            credentials,
            call.data["query"],
            call.data["fields"],
        )

    hass.services.async_register(DOMAIN, "list_mp4_files", list_mp4_files)
    hass.services.async_register(DOMAIN, "upload_large_media_file", upload_large_media_file)
    hass.services.async_register(DOMAIN, "cleanup_drive_files", cleanup_drive_files)
    hass.services.async_register(DOMAIN, "list_files_by_pattern", list_files_by_pattern)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload Google Drive integration."""
    hass.services.async_remove(DOMAIN, "list_mp4_files")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
