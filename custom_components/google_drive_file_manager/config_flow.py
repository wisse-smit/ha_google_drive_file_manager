import logging
import voluptuous as vol

from homeassistant.helpers.config_entry_oauth2_flow import (
    AbstractOAuth2FlowHandler,
    async_register_implementation,
)
from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN, SCOPES
from .oauth2_impl import GoogleDriveOAuth2Implementation

_LOGGER = logging.getLogger(__name__)


class GoogleDriveConfigFlowHandler(
    AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Handle a config flow for Google Drive using OAuth2."""

    # Must set this or AbstractOAuth2FlowHandler.__init__ will error
    DOMAIN = DOMAIN  
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        # Validates DOMAIN != ""
        super().__init__()
        self.client_id: str | None = None
        self.client_secret: str | None = None

    @property
    def logger(self) -> logging.Logger:
        return _LOGGER

    @property
    def extra_authorize_data(self) -> dict:
        """Request offline access so we get a refresh token and force consent."""
        return {"access_type": "offline", "prompt": "consent"}

    @property
    def authorize_url(self) -> str:
        return OAUTH2_AUTHORIZE

    @property
    def request_token_url(self) -> str:
        return OAUTH2_TOKEN

    async def async_step_user(self, user_input: dict | None = None):
        """Ask the user for client_id / client_secret / redirect preference."""
        if user_input is not None:
            self.client_id = user_input["client_id"]
            self.client_secret = user_input["client_secret"]
            return await self.async_step_auth()

        data_schema = vol.Schema({
            vol.Required("client_id"): str,
            vol.Required("client_secret"): str,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_auth(self, user_input: dict | None = None):
        """Register our OAuth2 implementation and kick off the standard flow."""
        implementation = GoogleDriveOAuth2Implementation(
            self.hass, self.client_id, self.client_secret, self.use_my_redirect
        )
        async_register_implementation(self.hass, DOMAIN, implementation)  # correct helper :contentReference[oaicite:0]{index=0}
        self.flow_impl = implementation
        return await super().async_step_auth(user_input)

    async def async_oauth_create_entry(self, data: dict):
        """Finish and store the config entry once we have tokens."""
        # data comes in as {"auth_implementation": "<impl>", "token": {...}}
        token = data["token"]
        return self.async_create_entry(
            title="Google Drive",
            data={
                "token": token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_implementation": self.flow_impl.domain,
            }
        )
