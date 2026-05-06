"""Config flow for Bridge Bank OAuth redirect."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

DOMAIN = "bridge_bank"

# Internal Docker hostname for the add-on on the HA network.
# Local add-ons: "local-<slug>", community/repo add-ons: "<repo_slug>-<addon_slug>"
ADDON_URL = "http://local-bridge-bank:3000"


class BridgeBankConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bridge Bank."""

    VERSION = 1

    async def async_step_hassio(self, discovery_info: dict | None = None):
        """Auto-configure when the Bridge Bank add-on is running — no user action needed."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="Bridge Bank",
            data={"bridge_bank_url": ADDON_URL},
        )

    async def async_step_user(self, user_input=None):
        """Handle the manual step."""
        errors = {}

        if user_input is not None:
            url = user_input["bridge_bank_url"].rstrip("/")
            if not url.startswith("http"):
                errors["bridge_bank_url"] = "invalid_url"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Bridge Bank",
                    data={"bridge_bank_url": url},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "bridge_bank_url",
                        default=ADDON_URL,
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "description": "Enter the local URL of your Bridge Bank instance."
            },
        )
