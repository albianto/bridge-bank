"""Config flow for Bridge Bank OAuth redirect."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant

DOMAIN = "bridge_bank"


class BridgeBankConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bridge Bank."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            url = user_input["bridge_bank_url"].rstrip("/")
            if not url.startswith("http"):
                errors["bridge_bank_url"] = "invalid_url"
            else:
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
                        default="http://192.168.1.100:3002",
                    ): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "description": "Enter the local URL of your Bridge Bank instance."
            },
        )
