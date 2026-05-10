from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_RECIPIENTS,
    DEFAULT_NAME,
    DEFAULT_TIMEOUT,
    DOMAIN,
    STATUS_PATH,
)


def _normalize_recipients(raw: str) -> list[str]:
    return [n.strip() for n in raw.replace(";", ",").split(",") if n.strip()]


async def _validate_gateway(base_url: str, api_key: str) -> str | None:
    headers = {"X-API-Key": api_key}
    try:
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{base_url}{STATUS_PATH}", headers=headers) as resp:
                if resp.status == 200:
                    return None
                if resp.status == 401:
                    return "invalid_auth"
                if resp.status == 403:
                    return "insufficient_scope"
                return "cannot_connect"
    except Exception:
        return "cannot_connect"


class SmsGatewayNotifyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].strip().rstrip("/")
            api_key = user_input[CONF_API_KEY].strip()
            recipients = _normalize_recipients(user_input.get(CONF_RECIPIENTS, ""))

            if not base_url.startswith(("http://", "https://")):
                errors[CONF_BASE_URL] = "invalid_url"
            elif not api_key:
                errors[CONF_API_KEY] = "required"
            else:
                err = await _validate_gateway(base_url, api_key)
                if err:
                    errors["base"] = err
                else:
                    await self.async_set_unique_id(base_url)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input.get("name") or DEFAULT_NAME,
                        data={
                            CONF_BASE_URL: base_url,
                            CONF_API_KEY: api_key,
                            CONF_RECIPIENTS: recipients,
                        },
                    )

        schema = vol.Schema(
            {
                vol.Optional("name", default=DEFAULT_NAME): str,
                vol.Required(CONF_BASE_URL, default="http://192.168.200.52:8091"): str,
                vol.Required(CONF_API_KEY): str,
                vol.Optional(CONF_RECIPIENTS, default=""): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)



@callback
def async_get_options_flow(config_entry):
    return SmsGatewayNotifyOptionsFlow(config_entry)


class SmsGatewayNotifyOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].strip().rstrip("/")
            api_key = user_input[CONF_API_KEY].strip()
            recipients = _normalize_recipients(user_input.get(CONF_RECIPIENTS, ""))
            if not base_url.startswith(("http://", "https://")):
                errors[CONF_BASE_URL] = "invalid_url"
            elif not api_key:
                errors[CONF_API_KEY] = "required"
            else:
                err = await _validate_gateway(base_url, api_key)
                if err:
                    errors["base"] = err
                else:
                    return self.async_create_entry(
                        title="",
                        data={
                            CONF_BASE_URL: base_url,
                            CONF_API_KEY: api_key,
                            CONF_RECIPIENTS: recipients,
                        },
                    )

        current = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=current.get(CONF_BASE_URL, "")): str,
                vol.Required(CONF_API_KEY, default=current.get(CONF_API_KEY, "")): str,
                vol.Optional(
                    CONF_RECIPIENTS,
                    default=", ".join(current.get(CONF_RECIPIENTS, [])),
                ): str,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
