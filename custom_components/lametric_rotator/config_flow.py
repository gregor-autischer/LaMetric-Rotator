"""Config + options flows for the LaMetric Rotator integration.

Initial setup picks the LaMetric ``ConfigEntry`` that messages will be sent
to. The list of display items lives in ``entry.options`` and is managed via
the options flow (a recursive menu — add / edit / delete one item at a time
so the form stays trivial).
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    DOMAIN,
    ICON_CATALOG,
    MAX_ITEMS,
    parse_icon_thresholds,
)


def _icon_selector() -> selector.SelectSelector:
    """Dropdown of curated icons that also accepts a custom numeric ID."""
    options = [
        selector.SelectOptionDict(value=p.icon_id, label=f"{p.icon_id} — {p.label}")
        for p in ICON_CATALOG
    ]
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options,
            mode=selector.SelectSelectorMode.DROPDOWN,
            custom_value=True,
        )
    )


def _item_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Schema for a single display item."""
    defaults = defaults or {}
    entity_marker = (
        vol.Required(CONF_ENTITY_ID, default=defaults[CONF_ENTITY_ID])
        if CONF_ENTITY_ID in defaults
        else vol.Required(CONF_ENTITY_ID)
    )
    icon_marker = (
        vol.Required(CONF_ICON, default=defaults[CONF_ICON])
        if CONF_ICON in defaults
        else vol.Required(CONF_ICON)
    )
    return vol.Schema(
        {
            entity_marker: selector.EntitySelector(),
            vol.Optional(
                CONF_ATTRIBUTE,
                default=defaults.get(CONF_ATTRIBUTE, ""),
            ): selector.TextSelector(),
            icon_marker: _icon_selector(),
            vol.Optional(
                CONF_ICON_THRESHOLDS,
                default=defaults.get(CONF_ICON_THRESHOLDS, ""),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_PREFIX,
                default=defaults.get(CONF_PREFIX, ""),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_SUFFIX,
                default=defaults.get(CONF_SUFFIX, ""),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_DECIMALS,
                default=defaults.get(CONF_DECIMALS, 0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=4, step=1, mode="box")
            ),
            vol.Optional(
                CONF_SCALE,
                default=defaults.get(CONF_SCALE, 1.0),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.001, max=1000, step=0.001, mode="box"
                )
            ),
        }
    )


# ---------------------------------------------------------------------------
# Initial setup
# ---------------------------------------------------------------------------


class LaMetricRotatorConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        lametric_entries = self.hass.config_entries.async_entries("lametric")
        if not lametric_entries:
            return self.async_abort(reason="no_lametric")

        if user_input is None:
            options = {e.entry_id: e.title for e in lametric_entries}
            schema = vol.Schema(
                {
                    vol.Required(CONF_LAMETRIC_ENTRY_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=eid, label=title)
                                for eid, title in options.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            )
            return self.async_show_form(step_id="user", data_schema=schema)

        target_entry = self.hass.config_entries.async_get_entry(
            user_input[CONF_LAMETRIC_ENTRY_ID]
        )
        title = (
            f"LaMetric Rotator: {target_entry.title}" if target_entry else "LaMetric Rotator"
        )
        await self.async_set_unique_id(
            f"{DOMAIN}_{user_input[CONF_LAMETRIC_ENTRY_ID]}"
        )
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=title,
            data={CONF_LAMETRIC_ENTRY_ID: user_input[CONF_LAMETRIC_ENTRY_ID]},
            options={CONF_ITEMS: []},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return LaMetricRotatorOptionsFlow(entry)


# ---------------------------------------------------------------------------
# Options flow — manage the list of items
# ---------------------------------------------------------------------------


class LaMetricRotatorOptionsFlow(OptionsFlow):
    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._items: list[dict[str, Any]] = list(
            entry.options.get(CONF_ITEMS, [])
        )
        self._editing_index: int | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_menu()

    async def async_step_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        menu: dict[str, str] = {}
        if len(self._items) < MAX_ITEMS:
            menu["add_item"] = "➕ Add new item"
        for idx, item in enumerate(self._items):
            menu[f"edit_{idx}"] = (
                f"✏️ {idx + 1}. {item.get(CONF_ENTITY_ID, '?')} "
                f"(icon {item.get(CONF_ICON, '?')})"
            )
        menu["save"] = "💾 Save and exit"
        return self.async_show_menu(
            step_id="menu",
            menu_options=menu,
            description_placeholders={
                "summary": _format_items(self._items) or "—",
            },
        )

    async def async_step_save(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return self.async_create_entry(
            title="", data={CONF_ITEMS: self._items}
        )

    async def async_step_add_item(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                cleaned = _clean_item(user_input)
            except ValueError:
                errors[CONF_ICON_THRESHOLDS] = "bad_thresholds"
            else:
                self._items.append(cleaned)
                return await self.async_step_menu()
        return self.async_show_form(
            step_id="add_item",
            data_schema=_item_schema(user_input or {}),
            errors=errors,
        )

    # Edit/delete steps are dispatched dynamically from the menu options.
    # We catch them via __getattr__-style lookup because HA's flow manager
    # calls async_step_<step_id>, where step_id is the chosen menu key.
    async def _async_step_edit(
        self, idx: int, user_input: dict[str, Any] | None
    ) -> ConfigFlowResult:
        if idx >= len(self._items):
            return await self.async_step_menu()

        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input.get("_delete"):
                del self._items[idx]
                return await self.async_step_menu()
            try:
                cleaned = _clean_item(user_input)
            except ValueError:
                errors[CONF_ICON_THRESHOLDS] = "bad_thresholds"
            else:
                self._items[idx] = cleaned
                return await self.async_step_menu()

        defaults = {**(user_input or self._items[idx])}
        schema = _item_schema(defaults).extend(
            {vol.Optional("_delete", default=False): selector.BooleanSelector()}
        )
        return self.async_show_form(
            step_id=f"edit_{idx}",
            data_schema=schema,
            errors=errors,
        )

    def __getattr__(self, name: str):  # type: ignore[override]
        if name.startswith("async_step_edit_"):
            try:
                idx = int(name.removeprefix("async_step_edit_"))
            except ValueError:
                raise AttributeError(name)

            async def _step(user_input: dict[str, Any] | None = None):
                return await self._async_step_edit(idx, user_input)

            return _step
        raise AttributeError(name)


def _clean_item(raw: dict[str, Any]) -> dict[str, Any]:
    """Strip empty optional fields and coerce types.

    Raises ``ValueError`` if the threshold rule input is malformed so the
    config flow can highlight the offending field.
    """
    item = {
        CONF_ENTITY_ID: raw[CONF_ENTITY_ID],
        CONF_ICON: str(raw[CONF_ICON]).strip(),
    }
    attribute = (raw.get(CONF_ATTRIBUTE) or "").strip()
    if attribute:
        item[CONF_ATTRIBUTE] = attribute
    thresholds_raw = (raw.get(CONF_ICON_THRESHOLDS) or "").strip()
    if thresholds_raw:
        # Validates eagerly; will raise on bad input.
        parse_icon_thresholds(thresholds_raw)
        item[CONF_ICON_THRESHOLDS] = thresholds_raw
    for key in (CONF_PREFIX, CONF_SUFFIX):
        value = (raw.get(key) or "").strip()
        if value:
            item[key] = value
    decimals = int(raw.get(CONF_DECIMALS, 0) or 0)
    if decimals:
        item[CONF_DECIMALS] = decimals
    scale = float(raw.get(CONF_SCALE, 1.0) or 1.0)
    if scale != 1.0:
        item[CONF_SCALE] = scale
    return item


def _format_items(items: list[dict[str, Any]]) -> str:
    if not items:
        return ""
    lines = []
    for idx, it in enumerate(items, start=1):
        prefix = it.get(CONF_PREFIX, "")
        suffix = it.get(CONF_SUFFIX, "")
        lines.append(
            f"{idx}. {it.get(CONF_ENTITY_ID, '?')}  "
            f"icon={it.get(CONF_ICON, '?')}  "
            f"format='{prefix}<value>{suffix}'"
        )
    return "\n".join(lines)
