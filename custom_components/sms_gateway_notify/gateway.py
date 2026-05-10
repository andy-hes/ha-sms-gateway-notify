from __future__ import annotations

import logging
from typing import Iterable

import aiohttp
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, CONF_BASE_URL, DEFAULT_TIMEOUT, SEND_PATH

_LOGGER = logging.getLogger(__name__)


def normalize_numbers(raw: Iterable[str] | str | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [raw]
    numbers: list[str] = []
    for item in raw:
        number = str(item).strip()
        if number and number not in numbers:
            numbers.append(number)
    return numbers


async def async_send_sms(
    base_url: str,
    api_key: str,
    numbers: Iterable[str] | str,
    message: str,
    title: str | None = None,
) -> None:
    targets = normalize_numbers(numbers)
    if not targets:
        raise ValueError("No recipients configured/provided for SMS message")

    text = f"{title}\n{message}".strip() if title else message.strip()
    if not text:
        raise ValueError("Message is empty")

    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
    failures: list[str] = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for number in targets:
            try:
                async with session.post(
                    f"{base_url.rstrip('/')}{SEND_PATH}",
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
        raise RuntimeError(", ".join(failures))
