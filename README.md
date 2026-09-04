# 🔭 Home Assistant Astronomy Space Suite (ASS)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=snfx-johaver&repository=home-assistant-astronomy-suite&category=integration)

The most complete astronomy and space dashboard for Home Assistant. Yes, I know what the acronym spells — and no, I'm not changing it. The universe has a sense of humor, and so do I 🍑🚀

Fully isolated — does not modify any existing dashboards, integrations, or resources.

---

## ✨ Features

### 🛰️ Sensors (17+ NASA + 120+ Ephemeris + 121 Deep-Sky)
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
| **Deep-Sky Objects** (30 DSOs × 4 sensors each + Best Tonight) | Local calc | None |

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

### 🃏 Custom Lovelace Cards (15)
All cards are prefixed **"ASS"** in the card picker for easy discovery.

| Card | Bundle | Description |
|------|--------|-------------|
| `apod-card` | astronomy-cards.js | Astronomy Picture of the Day with metadata |
| `neo-threat-card` | astronomy-cards.js | Near Earth Object tracker with threat levels |
| `solar-activity-card` | astronomy-cards.js | CME/Flare/Storm monitor + KP gauge + live Sun |
| `astro-horizon-card` | astronomy-cards.js | Sun arc horizon visualization |
| `astro-lunar-card` | astronomy-cards.js | Moon phase visualization |
| `solar-system-card` | astronomy-cards.js | Real-time heliocentric orrery (orbital mechanics) |
| `rocket-launch-card` | astronomy-cards.js | Next 5 launches with countdown timers |
| `iss-tracker-card` | astronomy-cards.js | SVG world map with ISS + orbital path + live stream |
| `earth-observation-card` | astronomy-cards.js | Multi-source satellite imagery (EPIC, GOES, SDO, SOHO) |
| `night-sky-highlights-card` | astronomy-cards.js | Best visible planets tonight with ephemeris data |
| `night-sky-highlights-2-card` | deepsky-cards.js | Auto-detecting highlights tile grid (planets, DSO, NEO, ISS, KP, flares) |
| `dso-tonight-table-card` | deepsky-cards.js | Sortable table of visible deep-sky objects |
| `dso-yard-map-card` | deepsky-cards.js | Polar projection sky map (SVG) |
| `dso-panorama-card` | deepsky-cards.js | 360° horizon strip panorama |
| `dso-dome-card` | deepsky-cards.js | Interactive 3D sky dome (drag to rotate) |

### 🛡️ Isolation Guarantees
- ✅ All entity IDs namespaced under `astronomy_space_suite_` / `nasa_astronomy_`
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
9. Configure Ephemeris (enabled by default — uses your HA location)
10. Configure Deep-Sky Objects (enabled by default — 30 curated DSO targets)

**That's it!** The integration automatically:
- Deploys both card bundles (`astronomy-cards.js` + `deepsky-cards.js`) to your `www/` folder
- Registers both bundles as Lovelace resources
- Creates all sensors, cameras, and deep-sky entities

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
entity: sensor.astronomy_space_suite_apod
show_explanation: true
show_copyright: true
```

### ASS NEO Threat Card
```yaml
type: custom:neo-threat-card
entity: sensor.astronomy_space_suite_neo_count_today
largest_entity: sensor.astronomy_space_suite_largest_neo
max_items: 10
show_hazardous_only: false
```

### ASS Solar Activity Card
```yaml
type: custom:solar-activity-card
cme_entity: sensor.astronomy_space_suite_coronal_mass_ejections
flare_entity: sensor.astronomy_space_suite_solar_flares
storm_entity: sensor.astronomy_space_suite_geomagnetic_storms
kp_entity: sensor.astronomy_space_suite_planetary_kp_index
sdo_entity: camera.astronomy_space_suite_sdo_sun
soho_entity: camera.astronomy_space_suite_soho_sun
```

### ASS Solar System Card
```yaml
type: custom:solar-system-card
title: Solar System
show_jupiter: true
show_saturn: true
show_orbits: true
```

### ASS Rocket Launch Card
```yaml
type: custom:rocket-launch-card
entity_prefix: sensor.astronomy_space_suite_rocket_launch
max_launches: 5
show_countdown: true
```

### ASS ISS Tracker Card
```yaml
type: custom:iss-tracker-card
entity: sensor.astronomy_space_suite_iss_position
show_map: true
show_trail: true
show_stream_button: true
```

### ASS Earth Observation Card
```yaml
type: custom:earth-observation-card
epic_entity: camera.astronomy_space_suite_epic_earth
goes_entity: camera.astronomy_space_suite_goes_16_earth
goes18_entity: camera.astronomy_space_suite_goes_18_earth
himawari_entity: camera.astronomy_space_suite_himawari_8_earth
sdo_entity: camera.astronomy_space_suite_sdo_sun
soho_entity: camera.astronomy_space_suite_soho_sun
```

### ASS Night Sky Highlights 2 Card
```yaml
type: custom:night-sky-highlights-2-card
title: Night Sky Highlights 2
```
No entity configuration needed — auto-detects all Astronomy Space Suite sensors.

### ASS Deep Sky Tonight Table
```yaml
type: custom:dso-tonight-table-card
title: Deep Sky Tonight
entity: sensor.nasa_astronomy_deepsky_best_tonight
```

### ASS Sky Map (Polar Projection)
```yaml
type: custom:dso-yard-map-card
title: Sky Map
```

### ASS Horizon Panorama
```yaml
type: custom:dso-panorama-card
title: Horizon Panorama
```

### ASS 3D Sky Dome
```yaml
type: custom:dso-dome-card
title: 3D Sky Dome
```

---

## 🏗️ Architecture

```
home-assistant-astronomy-suite/
├── custom_components/nasa_astronomy/
│   ├── __init__.py            # Auto-deploys cards, registers resources
│   ├── manifest.json          # HA integration manifest
│   ├── config_flow.py         # Config flow (API keys + Ephemeris + Deep-Sky)
│   ├── coordinator.py         # Concurrent data fetching (asyncio.gather)
│   ├── sensor.py              # 17+ sensor entities
│   ├── sensor_ephemeris.py    # 120+ local ephemeris sensors
│   ├── sensor_deepsky.py      # 121 deep-sky object sensors
│   ├── camera.py              # 7 camera entities
│   ├── const.py               # URLs and constants
│   ├── strings.json           # UI strings
│   ├── astronomy-cards.js     # Main card bundle (auto-deployed to www/)
│   ├── deepsky-cards.js       # Deep-sky card bundle (auto-deployed to www/)
│   ├── world-map.png          # ISS tracker base map
│   ├── providers/             # Ephemeris calculation engine
│   └── translations/en.json   # English translations
├── www/community/astronomy-cards/
│   ├── astronomy-cards.js     # Card source (development copy)
│   └── deepsky-cards.js       # Deep-sky cards source (development copy)
├── lovelace/
│   └── astronomy-dashboard.yaml  # Example dashboard
├── hacs.json                  # HACS metadata
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
| GOES-16/18 | cdn.star.nesdis.noaa.gov | None | Camera |
| Himawari-8 | himawari8.nict.go.jp | None | Camera |
| NASA SDO | sdo.gsfc.nasa.gov | None | Camera |
| ESA/NASA SOHO | soho.nascom.nasa.gov | None | Camera |
| Deep-Sky Objects | Local calculation (no API) | None | 5 min |
| Ephemeris | Local calculation (no API) | None | Configurable |

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

**Cards not showing in picker?** → Hard refresh browser (Ctrl+Shift+R). Check DevTools console for JS errors. Verify resources at Settings → Dashboards → ⋮ → Resources.

**"Custom element doesn't exist"?** → Go to Settings → Dashboards → ⋮ → Resources and verify both are listed:
- `/local/community/astronomy-cards/astronomy-cards.js` (module)
- `/local/community/astronomy-cards/deepsky-cards.js` (module)

**Integration not loading?** → Check HA logs. Most common issue is NASA API returning 503 (temporary outage).

**Sensors show "unavailable"?** → Data sources may be temporarily down. The integration retries every 10 minutes.

**Deep-sky sensors unavailable?** → Reconfigure the integration (Settings → Devices & Services → Astronomy Space Suite → Configure) and ensure "Deep-Sky Objects" is enabled.

---

## 📜 License

MIT

---

## 📋 Changelog

### v1.10.4
- **FIX: Solar Activity Monitor** — the "Live Sun" thumbnail grid forced a 4:3 box around SDO/SOHO square full-disc imagery with `object-fit: cover`, slicing roughly 25% off the top and bottom of the Sun; the tiles now size to the image. This is the same defect fixed for the Earth Observation card in v1.10.3 — that sweep corrected the Earth frame but missed this second instance
- **Internal** — added a class-level regression test asserting that no disc-image rule forces a fixed aspect ratio, so this cannot recur a third time. `.apod-media` is deliberately excluded and covered by its own test: APOD is arbitrary photography rather than a disc on a black field, so cropping to fill the hero area is a design choice, not the same defect

### v1.10.3
- **FIX: Night Sky Highlights 2** — Best DSO tile rendered the literal `[object Object]`; it now reads `top_objects[0].name`, and the score badge reads `top_objects[0].score` instead of a non-existent top-level `score` attribute
- **FIX: Tonight Table** — object names were prefixed with the device name ("Astronomy Space Suite M31"); deep-sky sensors now expose a dedicated `object_name` attribute that the cards read instead of parsing `friendly_name`
- **FIX: Rocket Launch Card** — showed impossible dates (May 2001, Jan 2035). The card fed the entity state (a mission name such as `EOS-05 (ISRO)`) into `new Date()`, which V8's lenient parser happily turned into a real date. `parseDate()` now rejects free-form text, and the card reads the published `t0`/`win_open` window and falls back to a TBD state
- **FIX: Rocket Launch Card** — "Location TBD" on every entry: the card read `pad_name`/`location_name` but the sensor only published `launch_pad`. The sensor now exposes `pad_name`, `location_name`, `t0`, `win_open` and `win_close`
- **FIX: Rocket Launch Card** — weather showed a unit-less "Temp: 79"; temperature and wind now carry units and follow the instance's unit system
- **FIX: Sky Panorama / 3D Dome / Sky Map** — labels of angularly close objects (NGC 869/884, M81/82, NGC 6992/M27) overlapped into unreadable text; labels are now nudged apart with a leader line back to their marker
- **FIX: Earth Observation Card** — the image frame forced a 16:9 box around square full-disc imagery, cropping the disc and leaving a large empty band; the frame now sizes to its content
- **FIX: Timestamp parsing** — epoch values in seconds (ISS) are no longer interpreted as milliseconds
- **Internal** — card bundles in `custom_components/` and `www/` re-synced (the `www/` copy still carried pre-rename entity IDs); `scripts/bump_version.py` patterns repaired after the bundle rename and extended to both copies; added a headless `node --test` suite covering all of the above

### v1.10.1
- **FIX: Card picker previews** — corrected default entity IDs in all card `getStubConfig()` methods
- **FIX: Night Sky Highlights 2** — now auto-detects sensors (no manual entity config needed)
- **FIX: Deepsky cards not loading** — removed duplicate custom element registration conflict
- **README** — updated to reflect 15 cards, 258+ entities, deep-sky feature

### v1.10.0 / v1.9.1
- **NEW: Deep-Sky Objects** — 30-object curated DSO catalog (Messier/NGC targets)
- **NEW: 121 deep-sky sensors** — altitude, azimuth, transit time, visibility per object + Best Tonight summary
- **NEW: 5 deep-sky cards** — Night Sky Highlights 2, Tonight Table, Sky Map, Panorama, 3D Dome
- **NEW: Config flow step 3** — Deep-Sky Objects (enable/disable, min altitude, max objects)
- All calculations done locally — no API key needed
- Resolves [Issue #2](https://github.com/snfx-johaver/home-assistant-astronomy-suite/issues/2)

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
