from __future__ import annotations

import logging

import aiohttp
from homeassistant.components.notify import ATTR_TARGET, BaseNotificationService
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, CONF_BASE_URL, CONF_RECIPIENTS, DEFAULT_TIMEOUT, SEND_PATH

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
        self._recipients = [str(n).strip() for n in cfg.get(CONF_RECIPIENTS, []) if str(n).strip()]

    async def async_send_message(self, message: str = "", **kwargs) -> None:
        raw_targets = kwargs.get(ATTR_TARGET) or self._recipients
        if isinstance(raw_targets, str):
            raw_targets = [raw_targets]

        targets: list[str] = []
        for target in raw_targets:
            number = str(target).strip()
            if number and number not in targets:
                targets.append(number)

        if not targets:
            _LOGGER.error("No recipients configured/provided for SMS message")
            return

        if not message:
            _LOGGER.error("Message is empty, skipping SMS send")
            return

        headers = {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
        }

        failures: list[str] = []
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for number in targets:
                payload = {"number": number, "text": message}
                try:
                    async with session.post(
                        f"{self._base}{SEND_PATH}",
                        headers=headers,
                        json=payload,
                    ) as resp:
                        if resp.status >= 400:
                            body = await resp.text()
                            failures.append(f"{number} ({resp.status})")
                            _LOGGER.error("SMS send failed to %s (%s): %s", number, resp.status, body)
                except Exception as err:  # noqa: BLE001
                    failures.append(f"{number} (exception)")
                    _LOGGER.error("SMS send exception to %s: %s", number, err)

        if failures:
            _LOGGER.warning("SMS send completed with failures: %s", ", ".join(failures))

    @property
    def targets(self):
        return {n: n for n in self._recipients}
