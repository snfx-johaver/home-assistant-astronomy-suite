# 🔭 Home Assistant Astronomy Space Suite (ASS)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=snfx-johaver&repository=home-assistant-astronomy-suite&category=integration)

The most complete astronomy and space dashboard for Home Assistant. Yes, we know what the acronym spells — and no, we're not changing it. The universe has a sense of humor, and so do we. 🍑🚀

Fully isolated — does not modify any existing dashboards, integrations, or resources.

## Features

- **APOD** — Astronomy Picture of the Day with full metadata
- **NeoWs** — Near Earth Object tracking with threat indicators
- **DONKI** — Space weather: CMEs, Solar Flares, Geomagnetic Storms
- **EONET** — Earth Observatory Natural Event Tracker
- **TechTransfer** — NASA patent/technology transfer data
- **Rocket Launch Live** — Next 5 upcoming launches with countdown timers
- **ISS Tracker** — Real-time position on world map + live video stream
- **Planetary KP Index** — Real-time aurora/geomagnetic activity from NOAA
- **7 Satellite Cameras** — APOD, EPIC Earth, GOES-16, GOES-18, Himawari-8, SDO Sun, SOHO Sun
- **9 Custom Lovelace Cards** — All prefixed "ASS" for easy finding in the card picker
- **Solar System Orrery** — Real-time planet positions from orbital mechanics
- **Built-in Horizon & Lunar Phase cards** — No external card dependencies required
- **Works alongside** — ApexCharts, Mushroom, ISS, Moon, Sun, Season, Aurora

## Installation

### 1. Custom Integration

Copy the `custom_components/nasa_astronomy/` folder to your HA config:

```
<your-ha-config>/custom_components/nasa_astronomy/
```

### 2. Custom Cards

Copy `www/community/astronomy-cards/` to your HA config:

```
<your-ha-config>/www/community/astronomy-cards/
```

### 3. Dashboard

Copy `lovelace/astronomy-dashboard.yaml` to your HA config:

```
<your-ha-config>/lovelace/astronomy-dashboard.yaml
```

### 4. Configuration

Add to your `configuration.yaml`:

```yaml
# Register the astronomy dashboard
lovelace:
  mode: storage
  dashboards:
    astronomy:
      mode: yaml
      title: "🔭 Astronomy"
      icon: mdi:telescope
      show_in_sidebar: true
      filename: lovelace/astronomy-dashboard.yaml
  resources:
    - url: /local/community/astronomy-cards/astronomy-cards.js
      type: module
```

### 5. Add Integration

1. Restart Home Assistant
2. Go to **Settings → Devices & Services → Add Integration**
3. Search for **NASA Astronomy Suite**
4. Enter your NASA API key (get one free at https://api.nasa.gov/)

## Repository Structure

```
home-assistant-astronomy-suite/
├── custom_components/
│   └── nasa_astronomy/
│       ├── __init__.py          # Integration setup
│       ├── const.py             # Constants & URLs
│       ├── manifest.json        # HA integration manifest
│       ├── config_flow.py       # Config flow UI
│       ├── strings.json         # Translations
│       ├── coordinator.py       # Data update coordinator
│       ├── sensor.py            # Sensor platform (11 sensors)
│       └── camera.py            # Camera platform (APOD image)
├── www/
│   └── community/
│       └── astronomy-cards/
│           ├── astronomy-cards.js    # Pre-built card bundle (USE THIS)
│           ├── apod-card.ts          # APOD card source
│           ├── neo-threat-card.ts    # NEO card source
│           ├── solar-activity-card.ts # Solar card source
│           ├── index.ts             # Bundle entry point
│           ├── package.json         # NPM config
│           ├── tsconfig.json        # TypeScript config
│           ├── rollup.config.mjs    # Build config
│           └── hacs.json            # HACS frontend metadata
├── lovelace/
│   └── astronomy-dashboard.yaml     # Complete dashboard (6 views)
├── hacs.json                        # HACS integration metadata
└── README.md                        # This file
```

## Entities Created

| Entity ID | Type | Description |
|-----------|------|-------------|
| `sensor.nasa_astronomy_suite_apod` | Sensor | APOD title + full attributes |
| `sensor.nasa_astronomy_suite_neo_count_today` | Sensor | Number of NEOs today |
| `sensor.nasa_astronomy_suite_closest_neo` | Sensor | Closest NEO distance |
| `sensor.nasa_astronomy_suite_fastest_neo` | Sensor | Fastest NEO speed |
| `sensor.nasa_astronomy_suite_largest_neo` | Sensor | Largest NEO diameter |
| `sensor.nasa_astronomy_suite_coronal_mass_ejections` | Sensor | CME count (7d) |
| `sensor.nasa_astronomy_suite_solar_flares` | Sensor | Solar flare count (7d) |
| `sensor.nasa_astronomy_suite_geomagnetic_storms` | Sensor | Geomagnetic storm count (30d) |
| `sensor.nasa_astronomy_suite_active_earth_events` | Sensor | EONET active events |
| `sensor.nasa_astronomy_suite_tech_transfer_patents` | Sensor | Tech transfer count |
| `camera.nasa_astronomy_suite_apod_image` | Camera | APOD as camera entity |

## Custom Cards

### `<apod-card>`
```yaml
type: custom:apod-card
entity: sensor.nasa_astronomy_suite_apod
show_explanation: true
show_copyright: true
```

### `<neo-threat-card>`
```yaml
type: custom:neo-threat-card
entity: sensor.nasa_astronomy_suite_neo_count_today
max_items: 8
```

### `<solar-activity-card>`
```yaml
type: custom:solar-activity-card
cme_entity: sensor.nasa_astronomy_suite_coronal_mass_ejections
flare_entity: sensor.nasa_astronomy_suite_solar_flares
storm_entity: sensor.nasa_astronomy_suite_geomagnetic_storms
show_timeline: true
```

## Isolation Guarantees

- ✅ All entity IDs namespaced under `nasa_astronomy_suite_`
- ✅ Dashboard is a separate YAML-mode dashboard (not modifying default)
- ✅ Custom cards use unique element names that won't conflict
- ✅ All CSS is scoped inside Shadow DOM (no global styles)
- ✅ Integration uses its own `DOMAIN` — no shared state
- ✅ Resources loaded from dedicated `/local/community/astronomy-cards/` path
- ✅ No modifications to existing configuration required beyond additive entries

## HACS Installation (Alternative)

Add this repository as a custom repository in HACS:
1. HACS → Integrations → ⋮ → Custom repositories
2. URL: `https://github.com/your-username/home-assistant-astronomy-suite`
3. Category: Integration
4. For the cards: HACS → Frontend → Custom repositories → same URL → Category: Lovelace

## License

MIT
