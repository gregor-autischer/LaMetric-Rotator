# 📺 LaMetric Rotator

A small Home Assistant custom integration that rotates a list of entity values across a [LaMetric Time](https://lametric.com/) display — every 10 seconds, one item, in order, on loop.

It's the "no-Node-RED" replacement for the typical pattern where users wire up a 10-second-trigger automation that hand-formats messages and pushes them via `lametric.message`. Here you fill out a form, pick an icon from a dropdown, done.

## What it does

- Pick **one LaMetric Time** per integration entry (you can have multiple entries if you have multiple devices).
- Configure up to **10 items**. Each item has:
  - an HA **entity** (any sensor, number, input_number, …)
  - a **LaMetric icon** — choose from a curated dropdown (battery levels, sun, lightning, house, EV, thermometer, clock, …) **or** paste any numeric icon ID from <https://developer.lametric.com/icons>
  - optional **prefix** (e.g. `🔋 `)
  - optional **suffix** (e.g. ` W`, ` %`, ` kWh`)
  - optional **decimal places** (0–4)
  - optional **scale factor** (e.g. `0.001` to convert W → kW)
- Cycle interval: **fixed at 10 seconds** — matches the LaMetric Time's default per-app rotation. With 1 item it's just re-pushed every 10 s; with 10 items the full loop is 100 s.
- All items live in the integration's options — change them via *Settings → Devices & Services → LaMetric Rotator → Configure* whenever you like; no restart needed.

## What it does **not** do

- ❌ No threshold-based icon switching (the "show full battery icon at >75 %, half at >25 %" trick from typical Node-RED flows). Currently each item has one fixed icon. If you want this, vote with thumbs-up on the relevant issue or send a PR.
- ❌ No custom timing — the cycle is hardcoded to 10 seconds. (The LaMetric hardware decides per-message display time anyway, so making this configurable in HA wouldn't really help.)
- ❌ No notifications, alerts, priority handling, or interactive elements. The integration only does a one-way fire-and-forget `lametric.message` call per tick.
- ❌ Doesn't talk to LaMetric directly — it depends on Home Assistant's built-in [LaMetric integration](https://www.home-assistant.io/integrations/lametric/) being set up first. This integration just *uses* it.

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
