from __future__ import annotations

import logging

import aiohttp
from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_API_KEY, CONF_BASE_URL, CONF_RECIPIENTS, DEFAULT_TIMEOUT, DOMAIN, SEND_PATH

_LOGGER = logging.getLogger(__name__)


def _normalize_recipients(raw: list[str] | str | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [raw]
    recipients: list[str] = []
    for item in raw:
        number = str(item).strip()
        if number and number not in recipients:
            recipients.append(number)
    return recipients


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    cfg = {**entry.data, **entry.options}
    recipients = _normalize_recipients(cfg.get(CONF_RECIPIENTS))

    entities: list[SmsGatewayNotifyEntity] = [
        SmsGatewayNotifyEntity(hass, entry.entry_id, name="Gateway", recipient=None)
    ]
    entities.extend(
        SmsGatewayNotifyEntity(hass, entry.entry_id, name=recipient, recipient=recipient)
        for recipient in recipients
    )
    async_add_entities(entities)


class SmsGatewayNotifyEntity(NotifyEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:message-text"

    def __init__(self, hass: HomeAssistant, entry_id: str, name: str, recipient: str | None) -> None:
        self._hass = hass
        self._entry_id = entry_id
        self._recipient = recipient
        self._attr_name = name
        suffix = "gateway" if recipient is None else f"recipient_{recipient}"
        self._attr_unique_id = f"{entry_id}_{suffix}"

    def _current_config(self) -> dict:
        entry = self._hass.config_entries.async_get_entry(self._entry_id)
        if entry is None:
            raise RuntimeError("config entry missing")
        return {**entry.data, **entry.options}

    def _recipients(self) -> list[str]:
        cfg = self._current_config()
        if self._recipient is not None:
            return [self._recipient]
        return _normalize_recipients(cfg.get(CONF_RECIPIENTS))

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="SMS Gateway",
            manufacturer="TheCastle",
            model="SMS gateway",
        )

    async def async_send_message(self, message: str, title: str | None = None, target=None, **kwargs) -> None:
        cfg = self._current_config()
        base = cfg[CONF_BASE_URL].rstrip("/")
        api_key = cfg[CONF_API_KEY]

        raw_targets = target or self._recipients()
        if isinstance(raw_targets, str):
            raw_targets = [raw_targets]

        targets: list[str] = []
        for value in raw_targets:
            number = str(value).strip()
            if number and number not in targets:
                targets.append(number)

        if not targets:
            _LOGGER.error("No recipients configured/provided for SMS message")
            return

        text = f"{title}\n{message}".strip() if title else message.strip()
        if not text:
            _LOGGER.error("Message is empty, skipping SMS send")
            return

        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        failures: list[str] = []

        async with aiohttp.ClientSession(timeout=timeout) as session:
            for number in targets:
                try:
                    async with session.post(
                        f"{base}{SEND_PATH}",
                        headers=headers,
                        json={"number": number, "text": text},
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
            return

        self._async_record_notification()
