import logging
from homeassistant.components import http
from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2Implementation

from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN, SCOPES

_LOGGER = logging.getLogger(__name__)

class GoogleDriveOAuth2Implementation(LocalOAuth2Implementation):
    """Local OAuth2 implementation for Google Drive with configurable redirect and scope."""

    def __init__(self, hass, client_id, client_secret):
        """Initialize with the given parameters."""
        super().__init__(
            hass,
            DOMAIN,
            client_id,
            client_secret,
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        )

    @property
    def redirect_uri(self) -> str:
        """Return the set redirect URI."""
        return "https://my.home-assistant.io/redirect/oauth"

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data appended to the authorize URL, including scopes."""
        return {
            "scope": " ".join(SCOPES),  # Space-separated list of scopes.
            "access_type": "offline",
            "prompt": "consent",
        }