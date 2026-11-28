# Changelog

## Unreleased - private preview

- Add an optional observing planner with a 48-hour darkness and weather ribbon,
  separate stargazing/deep-sky/imaging scores, best windows and local targets.
- Extend Night Sky Highlights with a bounded local celestial-event timeline,
  meteor showers, seasons, oppositions, elongations and close full Moons.
  Reuse the existing eclipse calculations and sensors.
- Extend the Moon card and illumination attributes with accurate phase times,
  lunar age, distance, apparent diameter, apsides and next rise/transit/set.
- Extend Solar Activity with optional NOAA Kp forecasts, flare probabilities,
  severity scales, monthly solar trends and location-based aurora guidance.
- Add optional selected-satellite passes from cached CelesTrak elements and
  local SGP4 propagation; preserve ISS entities, native map and YAML settings.
- Add options, secret-safe provider diagnostics and complete dashboard examples.
- Keep version 1.19.1 unchanged. This preview is not a published release.

## 1.19.1

- Fix missing Uranus and Neptune in the solar-system orrery, including their
  visual-editor toggles and existing YAML options.
- Compress orbital spacing when either outer planet is displayed, keeping
  inner planets readable while preserving calculated AU distances.

## 1.19.0

- Add locally calculated solar and lunar eclipse sensors using Astronomy Engine,
  with an 18-month search window and local horizon visibility filtering.
- Add schematic eclipse graphics, coverage badges and compact timings to
  Night Sky Highlights, with expandable details and a visual-editor toggle.
- Cache eclipse predictions daily and after an event ends; no automations or
  additional API keys are required.

## 1.18.1

- Correct lunar perturbation signs, planetary orbital inclination and node
  rotations, and Sun/planet coordinates to the equinox of date.
- Calculate lunar illumination from the actual Moon-Sun separation and use
  consistent solar coordinates for the equation of time.
- Fix planetary visibility windows across midnight UTC, including
  circumpolar objects and polar daylight/darkness.
- Label the NEO feed's current UTC calendar-day range and approach times;
  explain NASA's potentially hazardous classification and list selection.
- Add NEO sorting options (closest, soonest, largest, fastest), align
  statistics with hazardous-only filtering, and improve narrow-card layouts.

## 1.18.0

- Replace unsupported `mdi:planet` and `mdi:galaxy` dashboard heading icons
  with `mdi:earth` and `mdi:star-four-points`.
- Keep Meteosat-12 refresh failures at debug level when a cached image can be
  served, while retaining warnings when no image is available.
- Include the exception type in Meteosat-12 network failure messages so
  timeouts no longer produce an empty error description.

## 1.17.0

- Fixed the Himawari-8/9 camera by resolving NICT's latest image timestamp
  dynamically and downloading the current full-disk PNG.
- Added PNG validation, ten-minute refresh, concurrent-download coalescing, and
  last-success fallback for the Himawari camera.

## 1.16.0

- Added the `camera.astronomy_space_suite_meteosat_12_earth` EUMETSAT
  Meteosat-12 Europe/Africa GeoColour RGB full-disc feed.
- Added asynchronous ten-minute refresh, PNG validation, concurrent-download
  coalescing, and last-success fallback for the Meteosat camera.
- Added optional `meteosat_entity` support to the Earth Observation card,
  including its editor, defaults, tab, attribution, and uncropped square view.
- Added Meteosat coverage to the comprehensive bundled dashboard and release
  regression suites.
