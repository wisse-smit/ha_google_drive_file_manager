import logging
from yarl import URL
from homeassistant.components import http
from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2Implementation

from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN, SCOPES

_LOGGER = logging.getLogger(__name__)

class GoogleDriveOAuth2Implementation(LocalOAuth2Implementation):
    """Local OAuth2 implementation for Google Drive with configurable redirect and scope."""

    def __init__(self, hass, client_id, client_secret, use_my_redirect: bool = True):
        """Initialize with the given parameters."""
        super().__init__(
            hass,
            DOMAIN,
            client_id,
            client_secret,
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        )
        self.use_my_redirect = use_my_redirect

    @property
    def redirect_uri(self) -> str:
        """Return the redirect URI based on the chosen method."""
        if self.use_my_redirect:
            # Use the fixed redirect URI (make sure this is added in Google Cloud Console)
            return "https://my.home-assistant.io/redirect/oauth"
        req = http.current_request.get()
        if req is None:
            raise RuntimeError("No current request in context")
        ha_host = req.headers.get("HA-Frontend-Base")
        if ha_host is None:
            raise RuntimeError("No HA-Frontend-Base header in request")
        return f"{ha_host}/auth/external/callback"

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data appended to the authorize URL, including scopes."""
        return {
            "scope": " ".join(SCOPES),  # Space-separated list of scopes.
            "access_type": "offline",
            "prompt": "consent",
        }