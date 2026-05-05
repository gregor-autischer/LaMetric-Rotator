"""Constants and the curated LaMetric icon catalog."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "lametric_rotator"

# Hard-coded display interval. The same item is re-shown every CYCLE_SECONDS.
CYCLE_SECONDS = 10

CONF_LAMETRIC_ENTRY_ID = "lametric_entry_id"
CONF_ITEMS = "items"
CONF_ENTITY_ID = "entity_id"
CONF_ICON = "icon"
CONF_PREFIX = "prefix"
CONF_SUFFIX = "suffix"
CONF_DECIMALS = "decimals"
CONF_SCALE = "scale"

MAX_ITEMS = 10


@dataclass(frozen=True)
class IconPreset:
    """One curated entry for the icon dropdown."""

    icon_id: str
    label: str


# Curated list shown in the icon dropdown. The selector also accepts a custom
# numeric ID, so users can paste any LaMetric icon from
# https://developer.lametric.com/icons.
ICON_CATALOG: tuple[IconPreset, ...] = (
    IconPreset("27283", "Sonne / Solar"),
    IconPreset("7589", "Sonne hell"),
    IconPreset("21408", "Sonne lachend"),
    IconPreset("2741", "Akku 75–100 %"),
    IconPreset("2740", "Akku 50–75 %"),
    IconPreset("2739", "Akku 25–50 %"),
    IconPreset("2738", "Akku 0–25 %"),
    IconPreset("58195", "Blitz / Strom"),
    IconPreset("23537", "Blitz alternativ"),
    IconPreset("437", "Steckdose"),
    IconPreset("118", "Haus"),
    IconPreset("9505", "Haus alternativ"),
    IconPreset("12604", "Auto"),
    IconPreset("7591", "Elektroauto / EV"),
    IconPreset("12090", "Thermometer"),
    IconPreset("7676", "Feuer / Heizung"),
    IconPreset("7575", "Schneeflocke / Kühlung"),
    IconPreset("2236", "Wolke"),
    IconPreset("41054", "Wassertropfen"),
    IconPreset("55", "Uhr / Zeit"),
)
