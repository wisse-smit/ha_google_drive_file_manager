from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.config_entry_oauth2_flow import (
    async_get_config_entry_implementation,
    OAuth2Session,
)
from google.oauth2.credentials import Credentials

from ..const import DOMAIN, SCOPES, OAUTH2_TOKEN

async def async_get_google_drive_credentials(hass, entry):

    """Service to list mp4 files in Google Drive."""
    session: OAuth2Session = hass.data[DOMAIN][entry.entry_id]

    # Ensure the OAuth2 token is valid (refresh if needed)
    await session.async_ensure_token_valid() # non-blocking
    token_data = session.token

    # Prepare Google Credentials
    credentials = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=OAUTH2_TOKEN,
        client_id=entry.data.get("client_id"),
        client_secret=entry.data.get("client_secret"),
        scopes=SCOPES,
    )

    return credentials