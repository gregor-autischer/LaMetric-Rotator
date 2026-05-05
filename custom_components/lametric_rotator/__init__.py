"""LaMetric Rotator: rotate a list of entities through a LaMetric Time."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CONF_ATTRIBUTE,
    CONF_DECIMALS,
    CONF_ENTITY_ID,
    CONF_ICON,
    CONF_ICON_THRESHOLDS,
    CONF_ITEMS,
    CONF_LAMETRIC_ENTRY_ID,
    CONF_PREFIX,
    CONF_SCALE,
    CONF_SUFFIX,
    CYCLE_SECONDS,
    DOMAIN,
    parse_icon_thresholds,
    resolve_icon,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    rotator = LaMetricRotator(hass, entry)
    await rotator.async_start()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = rotator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    rotator: LaMetricRotator | None = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if rotator is not None:
        rotator.async_stop()
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when items are edited via the options flow."""
    await hass.config_entries.async_reload(entry.entry_id)


class LaMetricRotator:
    """Owns the periodic timer and dispatches LaMetric service calls."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._unsub: callback | None = None
        self._index = 0

    async def async_start(self) -> None:
        self._index = 0
        # Send the first item immediately so the user sees activity right
        # after setup; subsequent ticks are scheduled CYCLE_SECONDS apart.
        await self._tick()
        self._unsub = async_track_time_interval(
            self.hass, self._handle_tick, timedelta(seconds=CYCLE_SECONDS)
        )

    @callback
    def async_stop(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    async def _handle_tick(self, _now) -> None:
        await self._tick()

    async def _tick(self) -> None:
        items: list[dict[str, Any]] = list(self.entry.options.get(CONF_ITEMS, []))
        if not items:
            return
        item = items[self._index % len(items)]
        self._index = (self._index + 1) % len(items)
        await self._send(item)

    async def _send(self, item: dict[str, Any]) -> None:
        device_id = self._lametric_device_id()
        if device_id is None:
            _LOGGER.warning(
                "LaMetric Rotator: linked LaMetric entry %s has no device — skipping",
                self.entry.data.get(CONF_LAMETRIC_ENTRY_ID),
            )
            return

        formatted = self._format_value(item)
        if formatted is None:
            return  # entity unavailable; skip this tick
        message, numeric_value = formatted
        try:
            thresholds = parse_icon_thresholds(item.get(CONF_ICON_THRESHOLDS))
        except ValueError:
            thresholds = []
        icon = resolve_icon(
            str(item.get(CONF_ICON, "")), thresholds, numeric_value
        )

        try:
            await self.hass.services.async_call(
                "lametric",
                "message",
                {
                    "device_id": device_id,
                    "message": message,
                    "icon": icon,
                    "priority": "info",
                    "icon_type": "none",
                    "cycles": 1,
                },
                blocking=False,
            )
        except Exception:  # pragma: no cover
            _LOGGER.exception("LaMetric Rotator: failed to send message")

    def _format_value(
        self, item: dict[str, Any]
    ) -> tuple[str, float | None] | None:
        """Return ``(formatted_message, numeric_value_or_none)`` or ``None``
        if the entity isn't ready. The numeric value (post-scale) is used by
        the caller for threshold-based icon resolution.
        """
        entity_id = item.get(CONF_ENTITY_ID)
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, None, ""):
            return None

        attribute = item.get(CONF_ATTRIBUTE)
        if attribute:
            raw_value = state.attributes.get(attribute)
            if raw_value in (None, "", STATE_UNAVAILABLE, STATE_UNKNOWN):
                return None
        else:
            raw_value = state.state

        prefix = item.get(CONF_PREFIX, "")
        suffix = item.get(CONF_SUFFIX, "")
        decimals = int(item.get(CONF_DECIMALS, 0) or 0)
        scale = float(item.get(CONF_SCALE, 1.0) or 1.0)

        numeric: float | None = None
        try:
            numeric = float(raw_value) * scale
            value_str = f"{numeric:.{decimals}f}"
        except (TypeError, ValueError):
            value_str = str(raw_value)

        return f"{prefix}{value_str}{suffix}", numeric

    def _lametric_device_id(self) -> str | None:
        """Resolve the device_id of the linked LaMetric ``ConfigEntry``."""
        target_entry_id: str | None = self.entry.data.get(CONF_LAMETRIC_ENTRY_ID)
        if not target_entry_id:
            return None
        dev_reg = async_get_device_registry(self.hass)
        for device in dev_reg.devices.values():
            if target_entry_id in device.config_entries:
                return device.id
        return None
