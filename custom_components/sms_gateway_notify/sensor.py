from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .coordinator import SmsGatewayDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmsGatewayDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([SmsGatewayStatusSensor(coordinator, entry)])


class SmsGatewayStatusSensor(CoordinatorEntity[SmsGatewayDataUpdateCoordinator], SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Gateway status"
    _attr_unique_id = None

    def __init__(self, coordinator: SmsGatewayDataUpdateCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_gateway_status"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            config_entry_id=self._entry.entry_id,
            name="SMS Gateway",
            manufacturer="TheCastle",
            model="SMS gateway",
        )

    @property
    def native_value(self):
        return self.coordinator.data.get("state") if self.coordinator.data else None

    @property
    def extra_state_attributes(self):
        return self.coordinator.data or {}
