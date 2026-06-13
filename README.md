# 🔭 Home Assistant Astronomy Space Suite (ASS)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=snfx-johaver&repository=home-assistant-astronomy-suite&category=integration)

The most complete astronomy and space dashboard for Home Assistant. Yes, we know what the acronym spells — and no, we're not changing it. The universe has a sense of humor, and so do we. 🍑🚀

Fully isolated — does not modify any existing dashboards, integrations, or resources.

---

## ✨ Features

### 🛰️ Sensors (17+ NASA + 120+ Ephemeris)
| Sensor | Source | Auth |
|--------|--------|------|
| Astronomy Picture of the Day (APOD) | NASA | API key |
| Near Earth Objects (count, closest, fastest, largest) | NASA NeoWs | API key |
| Coronal Mass Ejections (7-day) | NASA DONKI | API key |
| Solar Flares (7-day) | NASA DONKI | API key |
| Geomagnetic Storms (30-day) | NASA DONKI | API key |
| Earth Events (EONET) | NASA | API key |
| Tech Transfer Patents | NASA | API key |
| Rocket Launch 1–5 | RocketLaunch.Live | Optional |
| ISS Position (lat/lon) | Open Notify | None |
| Planetary KP Index (aurora) | NOAA SWPC | None |
| **Ephemeris: Sun** (alt, az, RA, dec, twilight times) | Local calc | None |
| **Ephemeris: Moon** (alt, az, phase, illumination) | Local calc | None |
| **Ephemeris: Planets** (Mercury–Neptune positions) | Local calc | None |
| **Sky Conditions** (twilight phase, sidereal time, day length) | Local calc | None |

### 📷 Cameras (7)
| Camera | Source | Auth |
|--------|--------|------|
| APOD Image | NASA | API key |
| EPIC Earth (full-disk natural color) | NASA | None |
| GOES-16 Earth (Americas) | NOAA | None |
| GOES-18 Earth (Pacific) | NOAA | None |
| Himawari-8 Earth (Asia/Pacific) | NICT Japan | None |
| SDO Sun (171Å corona, extreme UV) | NASA | None |
| SOHO Sun (LASCO C3 coronagraph) | ESA/NASA | None |

### 🃏 Custom Lovelace Cards (10)
All cards are prefixed **"ASS"** in the card picker for easy discovery.

| Card | Description |
|------|-------------|
| `apod-card` | Astronomy Picture of the Day with metadata |
| `neo-threat-card` | Near Earth Object tracker with threat levels |
| `solar-activity-card` | CME/Flare/Storm monitor + optional KP gauge + live Sun thumbnails |
| `astro-horizon-card` | Sun arc horizon visualization |
| `astro-lunar-card` | Moon phase visualization |
| `solar-system-card` | Real-time heliocentric orrery (orbital mechanics) |
| `rocket-launch-card` | Next 5 launches with countdown timers |
| `iss-tracker-card` | SVG world map with ISS position, orbital path + live stream button |
| `earth-observation-card` | Multi-source satellite imagery (EPIC, GOES, Himawari, SDO, SOHO) |
| `night-sky-highlights-card` | Best visible planets tonight with ephemeris data |

### 🛡️ Isolation Guarantees
- ✅ All entity IDs namespaced under `nasa_astronomy_suite_`
- ✅ Custom cards use unique Shadow DOM elements (no global CSS)
- ✅ Does NOT modify any existing dashboards or resources
- ✅ Cards JS auto-deployed and auto-registered on setup
- ✅ Separate integration domain — no shared state

---

## 📦 Installation

### Via HACS (Recommended)

1. Open HACS in your Home Assistant
2. Click the button above, or manually add as a custom repository:
   - URL: `https://github.com/snfx-johaver/home-assistant-astronomy-suite`
   - Category: **Integration**
3. Click **Download**
4. **Restart Home Assistant**
5. Go to **Settings → Devices & Services → Add Integration**
6. Search for **Astronomy Space Suite**
7. Enter your NASA API key (get one free at [api.nasa.gov](https://api.nasa.gov/))
8. Optionally enter your RocketLaunch.Live API key (or leave blank for free tier)

**That's it!** The integration automatically:
- Deploys the custom cards JS to your `www/` folder
- Registers the cards as a Lovelace resource
- Creates all sensors and cameras

No manual file copying. No YAML editing. Just install, restart, configure.

### Manual Installation (Advanced)

If you don't use HACS:
1. Download the [latest release](https://github.com/snfx-johaver/home-assistant-astronomy-suite/releases)
2. Copy the `custom_components/nasa_astronomy/` folder to your HA config directory
3. Restart Home Assistant
4. Add the integration via Settings → Devices & Services

The integration handles everything else (card deployment + resource registration) automatically on first setup.

---

## 🃏 Card Configuration Examples

All cards are configurable via the visual editor (no YAML needed). Just add a card and search for "ASS".

### ASS APOD Card
```yaml
type: custom:apod-card
entity: sensor.nasa_astronomy_suite_apod
show_explanation: true
show_copyright: true
```

### ASS NEO Threat Card
```yaml
type: custom:neo-threat-card
entity: sensor.nasa_astronomy_suite_neo_count_today
max_items: 8          # UI configurable: 1-20
show_hazardous_only: false
```

### ASS Solar Activity Card
```yaml
type: custom:solar-activity-card
cme_entity: sensor.nasa_astronomy_suite_coronal_mass_ejections
flare_entity: sensor.nasa_astronomy_suite_solar_flares
storm_entity: sensor.nasa_astronomy_suite_geomagnetic_storms
kp_entity: sensor.nasa_astronomy_suite_planetary_kp_index
sdo_entity: camera.nasa_astronomy_suite_sdo_sun
soho_entity: camera.nasa_astronomy_suite_soho_sun
```

### ASS Solar System Card
```yaml
type: custom:solar-system-card
title: Solar System
show_jupiter: true
show_saturn: true
```

### ASS Rocket Launch Card
```yaml
type: custom:rocket-launch-card
entity_prefix: sensor.nasa_astronomy_suite_rocket_launch
max_launches: 5       # UI configurable: 1-5
show_countdown: true
```

### ASS ISS Tracker Card
```yaml
type: custom:iss-tracker-card
entity: sensor.nasa_astronomy_suite_iss_position
show_map: true
show_trail: true
show_stream_button: true
```

### ASS Earth Observation Card
Earth sources are grouped on the first row; Sun sources on the second row.
```yaml
type: custom:earth-observation-card
epic_entity: camera.nasa_astronomy_suite_epic_earth
goes_entity: camera.nasa_astronomy_suite_goes_16_earth
goes18_entity: camera.nasa_astronomy_suite_goes_18_earth
himawari_entity: camera.nasa_astronomy_suite_himawari_8_earth
sdo_entity: camera.nasa_astronomy_suite_sdo_sun
soho_entity: camera.nasa_astronomy_suite_soho_sun
```

---

## 🏗️ Architecture

```
home-assistant-astronomy-suite/
├── custom_components/nasa_astronomy/
│   ├── __init__.py          # Auto-deploys cards, registers resources
│   ├── manifest.json        # HA integration manifest
│   ├── config_flow.py       # Config flow (NASA + Rocket API keys)
│   ├── coordinator.py       # Concurrent data fetching (asyncio.gather)
│   ├── sensor.py            # 17+ sensor entities
│   ├── camera.py            # 7 camera entities
│   ├── const.py             # URLs and constants
│   ├── strings.json         # UI strings
│   ├── astronomy-cards.js   # Bundled card JS (auto-deployed to www/)
│   ├── icon.png             # Integration icon
│   └── logo.png             # Integration logo
├── www/community/astronomy-cards/
│   └── astronomy-cards.js   # Card source (development copy)
├── hacs.json                # HACS metadata
├── icon.png                 # Repository icon
├── logo.png                 # Repository logo
└── README.md
```

---

## 📡 Data Sources

| Source | URL | Auth | Update |
|--------|-----|------|--------|
| NASA APOD | api.nasa.gov/planetary/apod | API key | 10 min |
| NASA NeoWs | api.nasa.gov/neo/rest/v1/feed | API key | 10 min |
| NASA DONKI | api.nasa.gov/DONKI/ | API key | 10 min |
| NASA EONET | eonet.gsfc.nasa.gov/api/v3 | None | 10 min |
| NASA EPIC | epic.gsfc.nasa.gov/api/natural | None | 10 min |
| RocketLaunch.Live | fdo.rocketlaunch.live | Optional | 10 min |
| ISS Position | api.open-notify.org/iss-now.json | None | 10 min |
| NOAA SWPC KP | services.swpc.noaa.gov | None | 10 min |
| GOES-16 | cdn.star.nesdis.noaa.gov | None | Camera |
| GOES-18 | cdn.star.nesdis.noaa.gov | None | Camera |
| Himawari-8 | himawari8.nict.go.jp | None | Camera |
| NASA SDO | sdo.gsfc.nasa.gov | None | Camera |
| ESA/NASA SOHO | soho.nascom.nasa.gov | None | Camera |

---

## 🔑 API Keys

| Key | Required | Where to get it |
|-----|----------|----------------|
| NASA API Key | ✅ Yes | [api.nasa.gov](https://api.nasa.gov/) — free, instant |
| RocketLaunch.Live | ❌ Optional | [rocketlaunch.live](https://www.rocketlaunch.live/) — free tier works without key |

---

## 📋 Required Home Assistant Integrations

The following built-in HA integrations are recommended for full dashboard functionality:

| Integration | Purpose | Link |
|-------------|---------|------|
| **Sun** | Sun position for horizon card | [Sun integration](https://www.home-assistant.io/integrations/sun/) |
| **Moon** | Moon phase data for lunar card | [Moon integration](https://www.home-assistant.io/integrations/moon/) |
| **Season** | Season sensor for dashboard context | [Season integration](https://www.home-assistant.io/integrations/season/) |

Optional but recommended:
| Integration | Purpose | Link |
|-------------|---------|------|
| **Aurora** | Aurora KP forecast (supplements NOAA KP sensor) | [Aurora integration](https://www.home-assistant.io/integrations/aurora/) |

These are standard HA integrations — just enable them in Settings → Devices & Services if not already active.

---

## 🐛 Troubleshooting

**Cards not showing?** → Restart HA after install. The integration auto-registers cards on first setup.

**"Custom element doesn't exist"?** → Go to Settings → Dashboards → ⋮ → Resources and verify `/local/community/astronomy-cards/astronomy-cards.js` is listed as a module.

**Integration not loading?** → Check HA logs. Most common issue is NASA API returning 503 (temporary outage).

**Sensors show "unavailable"?** → Data sources may be temporarily down. The integration retries every 10 minutes.

---

## 📜 License

MIT

---

## 📋 Changelog

### v1.8.1
- **ISS Card**: Fixed "last updated" showing 1970 date (Unix timestamp conversion)
- **ISS Card**: Added orbital path line connecting trail points on the map
- **Night Sky Highlights Card**: Removed dark background — matches other cards' style
- **Night Sky Highlights Card**: Removed twilight phase section (cleaner UI)
- **Night Sky Highlights Card**: Card title now editable via UI editor
- **Ephemeris**: Fixed Neptune sensors showing unavailable (throttle was too low)
- **Ephemeris**: All sensors now grouped under "Astronomy Space Suite" device
- **Ephemeris**: Fixed time sensors causing ValueError (removed numeric units from time fields)
- **Ephemeris**: Fixed entity_id property error preventing sensor registration

### v1.8.0
- **NEW: OpenAstronomy Ephemeris Provider** — local planetary position calculations (VSOP87/Meeus)
- **NEW: Night Sky Highlights Card** — shows best visible objects tonight
- **NEW: 120+ ephemeris sensors** — Sun, Moon, Mercury through Neptune (altitude, azimuth, RA, dec, rise/set, visibility)
- **NEW: Sky condition sensors** — twilight phase, day/night length, sidereal time, Julian date
- Options flow with API Keys + Ephemeris configuration
- All new features enabled by default on fresh install
- Fully backward-compatible — no existing sensors affected

### v1.7.7
- All cards: title editable through UI editor
- Horizon card: full-width SVG, improved time label layout
- APOD card: localStorage caching, never shows empty

### v1.7.6
- Fixed aggressive browser caching with `?v=VERSION` cache-bust on resource URL

### v1.7.5
- NEO card: 4th stat "Largest" with colored icons
- Solar Activity card: fixed SDO/SOHO image flickering
- APOD card: state hash check to prevent unnecessary re-renders

### v1.7.4
- Solar System card: per-planet toggles, zoom button, all planet stats
- Horizon card: visible Dawn/Noon/Dusk labels, configurable title
