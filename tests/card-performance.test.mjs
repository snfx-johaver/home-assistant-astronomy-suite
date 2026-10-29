import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLES, makeSandbox, evaluateBundleInto } from "./harness.mjs";
import { makePerformanceHass } from "./performance-fixture.mjs";

function loadCards() {
  const sandbox = makeSandbox();
  sandbox.Date = class extends Date { static now() { return 1793232000000; } };
  evaluateBundleInto(sandbox, BUNDLES.astronomy);
  evaluateBundleInto(sandbox, BUNDLES.deepsky);
  return sandbox;
}

const registry = loadCards();
const cases = {
  "apod-card": "sensor.astronomy_space_suite_apod",
  "neo-threat-card": "sensor.astronomy_space_suite_neo_count_today",
  "solar-activity-card": "sensor.astronomy_space_suite_solar_flares",
  "astro-horizon-card": "sun.sun",
  "astro-lunar-card": "sensor.moon_phase",
  "solar-system-card": null,
  "rocket-launch-card": "sensor.astronomy_space_suite_rocket_launch_1",
  "iss-tracker-card": "sensor.astronomy_space_suite_iss_position",
  "earth-observation-card": "camera.astronomy_space_suite_goes_18_earth",
  "night-sky-highlights-card": "sensor.nasa_astronomy_ephemeris_moon_illumination_pct",
  "night-sky-highlights-2-card": "sensor.astronomy_space_suite_iss_position",
  "dso-tonight-table-card": "sensor.nasa_astronomy_deepsky_test_0_altitude",
  "dso-yard-map-card": "sensor.nasa_astronomy_deepsky_test_0_azimuth",
  "dso-panorama-card": "sensor.nasa_astronomy_ephemeris_mars_azimuth",
  "dso-dome-card": "sensor.nasa_astronomy_deepsky_test_0_altitude",
};

test("performance coverage includes every registered card, without live picker previews", () => {
  assert.deepEqual(registry.customCards.map(({ type }) => type).sort(), Object.keys(cases).sort());
  for (const card of registry.customCards) assert.equal(card.preview, false, card.type);
});

for (const [type, dependency] of Object.entries(cases)) {
  test(`${type}: unrelated state updates do not render, but dependencies and configuration do`, () => {
    const ctor = registry.customElements.get(type);
    const card = new ctor();
    const config = ctor.getStubConfig();
    card.setConfig(config);
    let renders = 0;
    card._render = () => { renders++; };
    const hass = makePerformanceHass(100, 4);
    card.hass = hass;
    assert.equal(renders, 1, "initial render");
    const unrelated = { ...hass, states: { ...hass.states, "sensor.unrelated_0": { state: "changed" } } };
    card.hass = unrelated;
    assert.equal(card._hass, unrelated, "retain the latest HA context even when rendering is skipped");
    assert.equal(renders, 1, "do not rebuild for unrelated states");
    let latest = unrelated;
    if (dependency) {
      latest = {
        ...unrelated,
        states: {
          ...unrelated.states,
          [dependency]: { ...unrelated.states[dependency], attributes: { ...unrelated.states[dependency].attributes, description: "changed attributes" } },
        },
      };
      card.hass = latest;
      assert.equal(renders, 2, "attribute-only changes with unchanged timestamps must render");
    }
    const previous = renders;
    card.setConfig({ ...config, title: "Edited title" });
    card.hass = latest;
    assert.equal(renders, previous + 1, "configuration changes must render");
    card.hass = { ...latest, locale: { language: "nl" } };
    assert.equal(renders, previous + 2, "locale changes must render");
    card.hass = { ...latest, themes: { darkMode: true } };
    assert.equal(renders, previous + 3, "theme changes must render");
  });
}

test("deep-sky discovery is shared, detects additions/removals, and supports a custom table entity", () => {
  const hass = makePerformanceHass(100, 2);
  let scans = 0;
  hass.states = new Proxy(hass.states, { ownKeys(target) { scans++; return Reflect.ownKeys(target); } });
  const cards = ["dso-tonight-table-card", "dso-yard-map-card", "dso-panorama-card", "dso-dome-card"]
    .map((type) => {
      const ctor = registry.customElements.get(type);
      const card = new ctor();
      card.setConfig(ctor.getStubConfig());
      card._render = () => {};
      card.hass = hass;
      return card;
    });
  assert.equal(scans, 1, "only one scan of HA states across the four views");
  const card = cards[0];
  let renders = 0;
  card._render = () => { renders++; };
  card.setConfig({ entity: "sensor.custom_best" });
  const custom = { state: "one", attributes: {} };
  card.hass = { ...hass, states: { ...hass.states, "sensor.custom_best": custom } };
  card.hass = { ...hass, states: { ...hass.states, "sensor.custom_best": { ...custom, state: "two" } } };
  assert.equal(renders, 2);
  const added = { ...hass.states, "sensor.nasa_astronomy_deepsky_new_altitude": { state: "50" } };
  card.hass = { ...hass, states: added };
  delete added["sensor.nasa_astronomy_deepsky_test_0_altitude"];
  card.hass = { ...hass, states: { ...added } };
  assert.equal(renders, 4);
});

test("time-dependent cards still update when the minute changes", () => {
  const sandbox = makeSandbox();
  let now = 0;
  sandbox.Date = class extends Date { static now() { return now; } };
  evaluateBundleInto(sandbox, BUNDLES.astronomy);
  for (const type of ["solar-system-card", "rocket-launch-card", "solar-activity-card"]) {
    const ctor = sandbox.customElements.get(type);
    const card = new ctor();
    card.setConfig(ctor.getStubConfig());
    let renders = 0;
    card._render = () => { renders++; };
    const hass = makePerformanceHass(0, 0);
    card.hass = hass;
    card.hass = { ...hass };
    assert.equal(renders, 1);
    now += 60000;
    card.hass = { ...hass };
    assert.equal(renders, 2, type);
  }
});

test("astronomy editors propagate HA once and do not resync text fields on state updates", () => {
  const ctor = registry.customElements.get("earth-observation-card-editor");
  const editor = new ctor();
  const picker = { _hass: null, assignments: 0, get hass() { return this._hass; }, set hass(value) { this._hass = value; this.assignments++; } };
  const title = { value: "draft title" };
  editor.shadowRoot.querySelectorAll = () => [picker];
  const getElementById = editor.shadowRoot.getElementById;
  editor.shadowRoot.getElementById = (id) => id === "epic_entity" ? picker : id === "title" ? title : getElementById(id);
  picker.addEventListener = () => {};
  title.addEventListener = () => {};
  editor.setConfig({ title: "Saved title" });
  title.value = "unsaved typing";
  const hass = makePerformanceHass(0, 0);
  editor.hass = hass;
  editor.hass = hass;
  assert.equal(picker.assignments, 1);
  assert.equal(title.value, "unsaved typing");
  let events = 0;
  editor.dispatchEvent = () => { events++; };
  editor._setValue("title", "new title");
  editor._setValue("title", "new title");
  assert.equal(events, 1, "input followed by change must not emit duplicate edits");
});

test("deep-sky editors keep their controls when HA echoes an edit", () => {
  for (const type of Object.keys(cases).filter((value) => value.startsWith("dso-") || value === "night-sky-highlights-2-card")) {
    const editor = new (registry.customElements.get(`${type}-editor`))();
    let renders = 0;
    editor._render = () => { renders++; };
    editor.setConfig({ title: "Title" });
    editor.setConfig({ title: "Title" });
    editor._config.title = "Typed title";
    editor.setConfig({ title: "Typed title" });
    assert.equal(renders, 1, type);
    editor.setConfig({ title: "External change" });
    assert.equal(renders, 2, type);
  }
});

test("ISS native map still receives HA updates without rebuilding the card", () => {
  const ctor = registry.customElements.get("iss-tracker-card");
  const card = new ctor();
  card.setConfig(ctor.getStubConfig());
  card._render = () => {};
  const hass = makePerformanceHass(0, 0);
  card.hass = hass;
  card._nativeMap = {};
  card._displayPosition = { latitude: 52, longitude: 4 };
  card._mapIsStale = false;
  const next = { ...hass };
  card.hass = next;
  assert.equal(card._nativeMap.hass, next);
});

test("night sky editor uses the shared editor controls instead of an unused Lit template", () => {
  const editor = new (registry.customElements.get("night-sky-highlights-card-editor"))();
  editor.setConfig({ title: "Test", telescope_mode: true });
  assert.match(editor.shadowRoot.innerHTML, /id="title"/);
  assert.match(editor.shadowRoot.innerHTML, /id="telescope_mode"/);
});
