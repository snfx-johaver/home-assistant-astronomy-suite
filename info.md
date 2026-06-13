# Astronomy Space Suite

A complete astronomy dashboard suite for Home Assistant powered by NASA APIs and other space data sources.

## Features

- **APOD** — NASA Astronomy Picture of the Day
- **Near-Earth Objects** — Real-time NEO tracking with threat assessment
- **Solar Activity** — CMEs, solar flares, geomagnetic storms, KP index
- **ISS Tracker** — Live position on a real world map with livestream link
- **Solar System Orrery** — Interactive heliocentric planet visualization with zoom
- **Rocket Launches** — Upcoming launch schedule with countdown
- **Earth Observation** — EPIC, GOES-16, SDO, SOHO camera feeds
- **Sun Horizon Arc** — Sun position with Dawn/Noon/Dusk labels
- **Lunar Phase** — Moon phase visualization

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

## Requirements

- Home Assistant 2024.1+
- NASA API key (free at https://api.nasa.gov)
- Existing integrations: Sun, Moon

## Installation

1. Install via HACS
2. Restart Home Assistant
3. Add integration: Settings → Devices & Services → Add Integration → "Astronomy Space Suite"
4. Enter your NASA API key
5. Cards and dashboard are auto-configured
