# Changelog

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
