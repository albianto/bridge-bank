"""Bridge Bank OAuth redirect component for Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "bridge_bank"
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Bridge Bank from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bridge Bank from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    hass.http.register_view(BridgeBankCallbackView(entry.data["bridge_bank_url"]))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True


from aiohttp import web
from homeassistant.components.http import HomeAssistantView


class BridgeBankCallbackView(HomeAssistantView):
    """Handle the OAuth callback and redirect to Bridge Bank."""

    url = "/api/bridge_bank/callback"
    name = "api:bridge_bank:callback"
    requires_auth = False

    def __init__(self, bridge_bank_url: str) -> None:
        """Initialize with the local Bridge Bank URL."""
        self._bridge_bank_url = bridge_bank_url.rstrip("/")

    async def get(self, request: web.Request) -> web.Response:
        """Redirect the OAuth callback to the local Bridge Bank instance."""
        query_string = request.query_string
        target = f"{self._bridge_bank_url}/callback"
        if query_string:
            target = f"{target}?{query_string}"
        _LOGGER.info("Redirecting OAuth callback to %s", self._bridge_bank_url)
        raise web.HTTPFound(location=target)
