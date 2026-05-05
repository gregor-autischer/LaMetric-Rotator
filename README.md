# 📺 LaMetric Rotator

A small Home Assistant custom integration that rotates a list of entity values across a [LaMetric Time](https://lametric.com/) display — every 10 seconds, one item, in order, on loop.

It's the "no-Node-RED" replacement for the typical pattern where users wire up a 10-second-trigger automation that hand-formats messages and pushes them via `lametric.message`. Here you fill out a form, pick an icon from a dropdown, done.

## What it does

- Pick **one LaMetric Time** per integration entry (you can have multiple entries if you have multiple devices).
- Configure up to **10 items**. Each item has:
  - an HA **entity** (any sensor, number, input_number, weather, …)
  - optional **attribute** — read a state attribute instead of the main state, useful for `weather` entities whose temperature, humidity and wind values live in attributes (see below)
  - a **LaMetric icon** — choose from a curated dropdown (battery levels, sun, lightning, house, EV, thermometer, clock, …) **or** paste any numeric icon ID from <https://developer.lametric.com/icons>
  - optional **icon thresholds** to switch the icon based on the value (see below)
  - optional **prefix** (e.g. `🔋 `)
  - optional **suffix** (e.g. ` W`, ` %`, ` kWh`)
  - optional **decimal places** (0–4)
  - optional **scale factor** (e.g. `0.001` to convert W → kW)
- Cycle interval: **fixed at 10 seconds** — matches the LaMetric Time's default per-app rotation. With 1 item it's just re-pushed every 10 s; with 10 items the full loop is 100 s.
- All items live in the integration's options — change them via *Settings → Devices & Services → LaMetric Rotator → Configure* whenever you like; no restart needed.

### Reading weather entities (and other attribute-only data)

Home Assistant's `weather` domain stores numeric values as **attributes** on a single entity (e.g. `weather.forecast_home`) — the entity's main state is just the *condition* (`"partlycloudy"`, `"sunny"`, …). Same goes for some other integrations.

Set the optional **Attribute** field on an item to read one of those attributes instead of the main state. For Met.no / most weather providers:

| Attribute | What it is |
| :-- | :-- |
| `temperature` | Current temperature |
| `humidity` | Relative humidity (%) |
| `wind_speed` | Wind speed |
| `wind_bearing` | Wind direction (degrees) |
| `pressure` | Air pressure |
| `visibility` | Visibility |

Example: an item with entity `weather.forecast_home`, attribute `temperature`, suffix `°C`, decimals `1`, icon `12090` (thermometer).

### Icon thresholds

Sometimes you want the icon to follow the value — battery icon goes from empty to full as the percentage rises, "consumer" vs. "exporter" icon flips around zero on a grid sensor, etc.

Each item has an optional **Icon thresholds** field. Format:

```
value=icon_id,value=icon_id,…
```

The smallest threshold the value is **≤** wins. If the value is above every threshold (or the entity isn't numeric), the default icon is used.

Example for a `sensor.battery_charge` (percent):

```
25=2738,50=2739,75=2740,100=2741
```

- `≤ 25 %` → icon `2738` (almost-empty)
- `≤ 50 %` → icon `2739`
- `≤ 75 %` → icon `2740`
- `≤ 100 %` → icon `2741` (full)
- otherwise → the default icon you picked above

## Requirements

- Home Assistant **2024.6** or newer.
- The built-in **LaMetric** integration set up and your device paired (this integration depends on it).

## Installation (HACS)

1. **HACS → ⋮ → Custom repositories**
2. Add `https://github.com/gregor-autischer/LaMetric-Rotator`, category *Integration*
3. Install **LaMetric Rotator**, restart Home Assistant.
4. **Settings → Devices & Services → Add Integration → LaMetric Rotator**.
5. Pick your LaMetric, click *Configure*, add items.

## Why a separate integration instead of a Node-RED flow?

Because most people don't run Node-RED. And even those who do shouldn't have to maintain six function nodes and a bunch of api-call-service blocks just to display three sensor values on a $200 display.

You could absolutely replicate this with a HA automation that triggers every 10 seconds and runs Jinja templates on a chosen entity — and that's fine. This integration just takes the same idea, removes the YAML/Jinja, and gives you a UI.

## License

[PolyForm Noncommercial 1.0.0](LICENSE).
