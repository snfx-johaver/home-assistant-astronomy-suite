/** Immutable HA-style states for repeatable rendering benchmarks and regressions. */
export function makePerformanceHass(unrelatedEntities = 10000, deepSkyObjects = 100) {
  const states = {};
  const add = (id, state, attributes = {}) => {
    states[id] = { entity_id: id, state: String(state), attributes, last_updated: "2026-10-28T20:00:00Z" };
  };
  for (let index = 0; index < unrelatedEntities; index++) add(`sensor.unrelated_${index}`, index);
  const image = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8'/%3E";
  add("sensor.astronomy_space_suite_apod", "Test APOD", { url: image, title: "Test APOD", media_type: "image" });
  add("sensor.astronomy_space_suite_neo_count_today", 6, { neo_list: [] });
  add("sensor.astronomy_space_suite_largest_neo", "Test asteroid");
  add("sensor.astronomy_space_suite_coronal_mass_ejections", 0, { events: [] });
  add("sensor.astronomy_space_suite_solar_flares", 0, { events: [] });
  add("sensor.astronomy_space_suite_geomagnetic_storms", 0, { events: [] });
  add("sensor.astronomy_space_suite_planetary_kp_index", 2);
  add("sensor.astronomy_space_suite_iss_position", "52, 4", { latitude: 52, longitude: 4, timestamp: "2026-10-28T20:00:00Z" });
  add("sun.sun", "above_horizon", { elevation: 25, azimuth: 180 });
  add("sensor.moon_phase", "full_moon", { illumination: 100 });
  for (const name of ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"]) {
    for (const [suffix, value] of Object.entries({ altitude: 45, azimuth: 180, illumination_pct: 80, phase_angle: 20, visibility_start: "20:00", visibility_end: "23:00" })) {
      add(`sensor.nasa_astronomy_ephemeris_${name}_${suffix}`, value);
    }
  }
  add("sensor.nasa_astronomy_ephemeris_sky_twilight_phase", "Night");
  for (const name of ["epic_earth", "goes_16_earth", "goes_18_earth", "himawari_8_earth", "meteosat_12_earth", "sdo_sun", "soho_sun"]) {
    add(`camera.astronomy_space_suite_${name}`, "idle", { entity_picture: image });
  }
  for (let index = 1; index <= 5; index++) {
    add(`sensor.astronomy_space_suite_rocket_launch_${index}`, `Launch ${index}`, { name: `Launch ${index}`, t0: "2026-11-02T20:00:00Z", provider: "Test provider", vehicle: "Test vehicle" });
  }
  for (let index = 0; index < deepSkyObjects; index++) {
    const prefix = `sensor.nasa_astronomy_deepsky_test_${index}`;
    add(`${prefix}_altitude`, 20 + index % 65, { object_name: `DSO ${index}`, score: 80, magnitude: 5, type: "Galaxy", constellation: "Test" });
    add(`${prefix}_azimuth`, index * 3.6);
    add(`${prefix}_visible`, "Yes");
    add(`${prefix}_transit_time`, "23:00");
  }
  add("sensor.nasa_astronomy_deepsky_best_tonight", `${deepSkyObjects} objects`, { count_visible: deepSkyObjects, top_objects: [{ name: "DSO 0", score: 80 }] });
  return {
    states,
    config: { latitude: 52, longitude: 4, unit_system: { temperature: "\u00b0C" } },
    themes: {},
    locale: { language: "en" },
  };
}
