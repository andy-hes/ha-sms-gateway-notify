from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

from .const import CONF_API_KEY, CONF_BASE_URL, DEFAULT_TIMEOUT, DOMAIN, STATUS_PATH


class SmsGatewayDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self.hass = hass
        self._entry_id = entry_id
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

    def _current_config(self) -> dict:
        entry = self.hass.config_entries.async_get_entry(self._entry_id)
        if entry is None:
            raise UpdateFailed("config entry missing")
        return {**entry.data, **entry.options}

    async def _async_update_data(self) -> dict:
        cfg = self._current_config()
        base = cfg[CONF_BASE_URL].rstrip("/")
        api_key = cfg[CONF_API_KEY]
        headers = {"X-API-Key": api_key}
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{base}{STATUS_PATH}", headers=headers) as resp:
                    if resp.status == 401:
                        raise UpdateFailed("invalid API key")
                    if resp.status == 403:
                        raise UpdateFailed("API key lacks modem_status scope")
                    if resp.status >= 400:
                        raise UpdateFailed(f"gateway returned HTTP {resp.status}")
                    payload = await resp.json()
                    if not payload.get("ok", True):
                        raise UpdateFailed(payload.get("error", "gateway status unavailable"))
                    return payload.get("modem", {})
        except UpdateFailed:
            raise
        except Exception as exc:
            raise UpdateFailed(str(exc)) from exc
