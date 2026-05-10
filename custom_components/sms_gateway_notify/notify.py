from __future__ import annotations

import logging

from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_API_KEY, CONF_BASE_URL, CONF_RECIPIENTS, DOMAIN
from .gateway import async_send_sms, normalize_numbers

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    cfg = {**entry.data, **entry.options}
    recipients = normalize_numbers(cfg.get(CONF_RECIPIENTS))

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
        return normalize_numbers(cfg.get(CONF_RECIPIENTS))

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="SMS Gateway",
            manufacturer="TheCastle",
            model="SMS gateway",
        )

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        cfg = self._current_config()
        try:
            await async_send_sms(cfg[CONF_BASE_URL], cfg[CONF_API_KEY], self._recipients(), message, title)
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("SMS send failed: %s", err)
            return
        self._async_record_notification()
