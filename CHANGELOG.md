# Changelog

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
