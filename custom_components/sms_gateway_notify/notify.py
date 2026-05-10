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

    return SmsGatewayNotificationService(hass, entry_id)


class SmsGatewayNotificationService(BaseNotificationService):
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._entry_id = entry_id

    def _current_config(self) -> dict:
        entry = self._hass.config_entries.async_get_entry(self._entry_id)
        if entry is None:
            raise RuntimeError("config entry missing")
        return {**entry.data, **entry.options}

    def _recipients(self) -> list[str]:
        cfg = self._current_config()
        return [str(n).strip() for n in cfg.get(CONF_RECIPIENTS, []) if str(n).strip()]

    async def async_send_message(self, message: str = "", **kwargs) -> None:
        cfg = self._current_config()
        base = cfg[CONF_BASE_URL].rstrip("/")
        api_key = cfg[CONF_API_KEY]
        raw_targets = kwargs.get(ATTR_TARGET) or self._recipients()
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
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }

        failures: list[str] = []
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for number in targets:
                payload = {"number": number, "text": message}
                try:
                    async with session.post(
                        f"{base}{SEND_PATH}",
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
        return {n: n for n in self._recipients()}
