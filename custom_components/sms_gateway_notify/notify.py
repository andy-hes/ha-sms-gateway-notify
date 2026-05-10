from __future__ import annotations

import logging

import aiohttp
from homeassistant.components.notify import ATTR_TARGET, BaseNotificationService
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, CONF_BASE_URL, CONF_RECIPIENTS

_LOGGER = logging.getLogger(__name__)


async def async_get_service(hass: HomeAssistant, config, discovery_info=None):
    """Return notify service for this integration."""
    entry_id = discovery_info.get("entry_id") if discovery_info else None
    if not entry_id:
        return None

    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None:
        return None

    merged = {**entry.data, **entry.options}
    return SmsGatewayNotificationService(merged)


class SmsGatewayNotificationService(BaseNotificationService):
    def __init__(self, cfg: dict) -> None:
        self._base = cfg[CONF_BASE_URL].rstrip("/")
        self._api_key = cfg[CONF_API_KEY]
        self._recipients = cfg.get(CONF_RECIPIENTS, [])

    async def async_send_message(self, message: str = "", **kwargs) -> None:
        targets = kwargs.get(ATTR_TARGET) or self._recipients
        if isinstance(targets, str):
            targets = [targets]

        if not targets:
            _LOGGER.error("No recipients configured/provided for SMS message")
            return

        headers = {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            for number in targets:
                payload = {"number": number, "text": message}
                try:
                    async with session.post(
                        f"{self._base}/api/external/send",
                        headers=headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=15),
                    ) as resp:
                        if resp.status >= 400:
                            body = await resp.text()
                            _LOGGER.error("SMS send failed to %s (%s): %s", number, resp.status, body)
                except Exception as err:  # noqa: BLE001
                    _LOGGER.error("SMS send exception to %s: %s", number, err)

    @property
    def targets(self):
        return {n: n for n in self._recipients}
