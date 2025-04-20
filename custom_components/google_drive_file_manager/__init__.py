import logging
from functools import partial

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.config_entry_oauth2_flow import (
    async_get_config_entry_implementation,
    OAuth2Session,
)
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from .const import DOMAIN, SCOPES, OAUTH2_TOKEN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    """Set up Google Drive integration from a config entry."""
    # Create OAuth2 session (refresh & storage handled for us)
    implementation = await async_get_config_entry_implementation(hass, entry)
    session = OAuth2Session(hass, entry, implementation)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = session

    async def list_mp4_files(call: ServiceCall) -> None:
        """Service to list mp4 files in Google Drive."""
        session: OAuth2Session = hass.data[DOMAIN][entry.entry_id]

        # Ensure the OAuth2 token is valid (refresh if needed)
        await session.async_ensure_token_valid()  # non-blocking :contentReference[oaicite:1]{index=1}
        token_data = session.token

        # Prepare Google Credentials
        creds = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri=OAUTH2_TOKEN,
            client_id=entry.data.get("client_id"),
            client_secret=entry.data.get("client_secret"),
            scopes=SCOPES,
        )

        # Define the blocking Drive API call
        def _blocking_drive_query() -> dict:
            # Build the Drive service (this uses httplib2 under the hood)
            drive_service = build("drive", "v3", credentials=creds)
            # Execute a blocking HTTP request
            return drive_service.files().list(
                q="mimeType='video/mp4'",
                fields="files(name)"
            ).execute()

        try:
            # Offload the blocking call to Home Assistant’s executor
            results = await hass.async_add_executor_job(_blocking_drive_query)  # runs in thread pool :contentReference[oaicite:2]{index=2}

            files = results.get("files", [])
            _LOGGER.info("MP4 files in Google Drive: %s", files)
            file_names = ", ".join(file["name"] for file in files) if files else "No mp4 files found."
            hass.components.persistent_notification.async_create(
                f"MP4 files: {file_names}",
                title="Google Drive MP4 Files"
            )
        except Exception as e:
            _LOGGER.error("Error retrieving mp4 files: %s", e)
            hass.components.persistent_notification.async_create(
                f"Error retrieving mp4 files: {e}",
                title="Google Drive MP4 Files Error"
            )

    hass.services.async_register(DOMAIN, "list_mp4_files", list_mp4_files)
    return True


async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload Google Drive integration."""
    hass.services.async_remove(DOMAIN, "list_mp4_files")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
