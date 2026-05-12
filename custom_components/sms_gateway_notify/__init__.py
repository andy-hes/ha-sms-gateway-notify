from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, CONF_BASE_URL, CONF_RECIPIENTS, DOMAIN
from .gateway import async_send_sms, normalize_numbers
from .coordinator import SmsGatewayDataUpdateCoordinator

PLATFORMS = ["notify", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    async def handle_send_sms(call) -> None:
        entries = list(hass.data.get(DOMAIN, {}).items())
        if not entries:
            return

        # Use the first loaded entry
        entry_id, data = entries[0]

        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None:
            return
        cfg = {**entry.data, **entry.options}
        number = call.data.get("number")
        numbers = call.data.get("numbers")
        if numbers and isinstance(numbers, str):
            numbers = [n.strip() for n in numbers.replace(";", ",").split(",") if n.strip()]
        targets = numbers or number or normalize_numbers(cfg.get(CONF_RECIPIENTS))
        await async_send_sms(cfg[CONF_BASE_URL], cfg[CONF_API_KEY], targets, call.data["message"], call.data.get("title"))

    hass.services.async_register(DOMAIN, "send_sms", handle_send_sms)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = SmsGatewayDataUpdateCoordinator(hass, entry.entry_id)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"coordinator": coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
