# Astronomy Space Suite

A complete astronomy dashboard suite for Home Assistant powered by NASA APIs and other space data sources.

## Features

- **APOD** — NASA Astronomy Picture of the Day
- **Near-Earth Objects** — Real-time NEO tracking with threat assessment
- **Solar Activity** — CMEs, solar flares, geomagnetic storms, KP index
- **ISS Tracker** — Live position and history trail on Home Assistant's native map, with last-known fallback and livestream link
- **Solar System Orrery** — Interactive heliocentric planet visualization with zoom
- **Rocket Launches** — Upcoming launch schedule with countdown
- **Earth Observation** — EPIC, GOES-16/18, Himawari-8, Meteosat-12, SDO, and SOHO camera feeds
- **Sun Horizon Arc** — Sun position with Dawn/Noon/Dusk labels
- **Lunar Phase** — Moon phase visualization
- **Night Sky Highlights** — Planet and observing-condition summaries
- **Deep-Sky Toolkit** — Tonight table, Sky Map, panorama, and interactive 3D dome

## Custom Cards Included

All cards are bundled and auto-deployed:
- custom:apod-card
- custom:neo-threat-card
- custom:solar-activity-card
- custom:solar-system-card
- custom:iss-tracker-card
- custom:rocket-launch-card
- custom:earth-observation-card
- custom:astro-horizon-card
- custom:astro-lunar-card
- custom:night-sky-highlights-card
- custom:night-sky-highlights-2-card
- custom:dso-tonight-table-card
- custom:dso-yard-map-card
- custom:dso-panorama-card
- custom:dso-dome-card

The current appearance remains the default. Add `glass_mode: true` to any
Astronomy Space Suite card for an optional translucent glass treatment.

## Requirements

- Home Assistant 2024.1+
- NASA API key (free at https://api.nasa.gov)
- Optional built-in integrations for the Horizon and Lunar cards: Sun, Moon

## Installation

1. Install via HACS
2. Restart Home Assistant
3. Add integration: Settings → Devices & Services → Add Integration → "Astronomy Space Suite"
4. Enter your NASA API key
5. The card resources are auto-configured
6. Optionally import `lovelace/astronomy-dashboard.yaml` as a separate dashboard
