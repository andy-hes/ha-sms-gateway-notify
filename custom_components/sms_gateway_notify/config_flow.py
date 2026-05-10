from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

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


def _config_schema(current: dict | None = None) -> vol.Schema:
    current = current or {}
    return vol.Schema(
        {
            vol.Optional("name", default=current.get("name", DEFAULT_NAME)): str,
            vol.Required(CONF_BASE_URL, default=current.get(CONF_BASE_URL, "http://192.168.200.52:8091")): str,
            vol.Required(CONF_API_KEY, default=current.get(CONF_API_KEY, "")): str,
            vol.Optional(
                CONF_RECIPIENTS,
                default=", ".join(current.get(CONF_RECIPIENTS, [])),
            ): str,
        }
    )


def _parsed_data(user_input: dict) -> dict:
    return {
        CONF_BASE_URL: user_input[CONF_BASE_URL].strip().rstrip("/"),
        CONF_API_KEY: user_input[CONF_API_KEY].strip(),
        CONF_RECIPIENTS: _normalize_recipients(user_input.get(CONF_RECIPIENTS, "")),
    }


class SmsGatewayNotifyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors = {}
        if user_input is not None:
            data = _parsed_data(user_input)
            if not data[CONF_BASE_URL].startswith(("http://", "https://")):
                errors[CONF_BASE_URL] = "invalid_url"
            elif not data[CONF_API_KEY]:
                errors[CONF_API_KEY] = "required"
            else:
                err = await _validate_gateway(data[CONF_BASE_URL], data[CONF_API_KEY])
                if err:
                    errors["base"] = err
                else:
                    await self.async_set_unique_id(data[CONF_BASE_URL])
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=user_input.get("name") or DEFAULT_NAME, data=data)

        return self.async_show_form(step_id="user", data_schema=_config_schema(), errors=errors)

    async def async_step_reconfigure(self, user_input: dict | None = None) -> FlowResult:
        reconfigure_entry = self._get_reconfigure_entry()
        errors = {}
        if user_input is not None:
            data = _parsed_data(user_input)
            if not data[CONF_BASE_URL].startswith(("http://", "https://")):
                errors[CONF_BASE_URL] = "invalid_url"
            elif not data[CONF_API_KEY]:
                errors[CONF_API_KEY] = "required"
            else:
                err = await _validate_gateway(data[CONF_BASE_URL], data[CONF_API_KEY])
                if err:
                    errors["base"] = err
                else:
                    await self.async_set_unique_id(reconfigure_entry.unique_id)
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        data_updates={"name": user_input.get("name") or DEFAULT_NAME, **data},
                    )

        current = {**reconfigure_entry.data, **reconfigure_entry.options}
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_config_schema(current),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmsGatewayNotifyOptionsFlow(config_entry)


class SmsGatewayNotifyOptionsFlow(config_entries.OptionsFlowWithReload):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        errors = {}
        if user_input is not None:
            data = _parsed_data(user_input)
            if not data[CONF_BASE_URL].startswith(("http://", "https://")):
                errors[CONF_BASE_URL] = "invalid_url"
            elif not data[CONF_API_KEY]:
                errors[CONF_API_KEY] = "required"
            else:
                err = await _validate_gateway(data[CONF_BASE_URL], data[CONF_API_KEY])
                if err:
                    errors["base"] = err
                else:
                    return self.async_create_entry(title="", data={"name": user_input.get("name") or DEFAULT_NAME, **data})

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_config_schema(current), errors=errors)
