"""Bridge Bank integration for Home Assistant."""

import logging
from datetime import timedelta

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

DOMAIN = "bridge_bank"
PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Bridge Bank from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bridge Bank from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    bridge_bank_url = entry.data["bridge_bank_url"].rstrip("/")

    # Register OAuth callback view
    hass.http.register_view(BridgeBankCallbackView(bridge_bank_url))

    # Set up data coordinator to poll Bridge Bank health/status
    coordinator = BridgeBankCoordinator(hass, bridge_bank_url)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "url": bridge_bank_url,
        "coordinator": coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


class BridgeBankCoordinator(DataUpdateCoordinator):
    """Fetch health data from the Bridge Bank instance."""

    def __init__(self, hass: HomeAssistant, url: str) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self._url = url

    async def _async_update_data(self) -> dict:
        """Fetch data from Bridge Bank /health endpoint."""
        import aiohttp

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._url}/health", timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200 or resp.status == 503:
                        return await resp.json()
                    return {"status": "unreachable"}
        except Exception:
            return {"status": "unreachable"}


class BridgeBankCallbackView(HomeAssistantView):
    """Handle the OAuth callback by proxying to Bridge Bank server-side."""

    url = "/api/bridge_bank/callback"
    name = "api:bridge_bank:callback"
    requires_auth = False

    def __init__(self, bridge_bank_url: str) -> None:
        """Initialize with the internal Bridge Bank URL."""
        self._bridge_bank_url = bridge_bank_url.rstrip("/")

    async def get(self, request: web.Request) -> web.Response:
        """Proxy the callback to Bridge Bank internally, then redirect browser to Ingress."""
        import aiohttp
        from yarl import URL

        query_string = request.query_string
        target = f"{self._bridge_bank_url}/callback"
        if query_string:
            target = f"{target}?{query_string}"

        _LOGGER.info("Proxying OAuth callback to %s", target)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    target,
                    allow_redirects=False,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    _LOGGER.info("Bridge Bank callback returned status %s", resp.status)
        except Exception as e:
            _LOGGER.error("Failed to proxy callback to Bridge Bank: %s", e)
            return web.Response(text=f"Callback failed: {e}", status=502)

        # Redirect browser back to the add-on Ingress panel using the same
        # host the user originally accessed (local vs Nabu Casa).
        ingress_path = "/hassio/ingress/local_bridge_bank"
        host = request.headers.get("Host", "")
        scheme = request.headers.get("X-Forwarded-Proto", request.scheme or "http")
        if host:
            redirect_url = f"{scheme}://{host}{ingress_path}"
        else:
            redirect_url = ingress_path
        raise web.HTTPFound(location=redirect_url)
