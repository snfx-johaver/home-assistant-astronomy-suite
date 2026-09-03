/**
 * Regression tests for the v1.10.2 card rendering fixes.
 *
 * Run with: node --test tests/
 * These exercise the pure rendering logic of the bundles. They cannot verify
 * visual layout in a real browser.
 */

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import { BUNDLES, loadBundle, makeHass, makeState, stubCanvasShadowRoot } from "./harness.mjs";

const deepsky = loadBundle(BUNDLES.deepsky, [
  "dskObjectName",
  "dskResolveLabelCollisions",
  "dskTextWidth",
  "NightSkyHighlights2Card",
  "DsoTonightTableCard",
  "DsoPanoramaCard",
  "DsoDomeCard",
]);

const astronomy = loadBundle(BUNDLES.astronomy, [
  "parseDate",
  "formatCountdown",
  "RocketLaunchCard",
]);

const BEST_TONIGHT = "sensor.nasa_astronomy_deepsky_best_tonight";

// Verbatim shape of the owner's live `top_objects[0]`.
const LIVE_TOP_OBJECT = {
  name: "M31",
  score: 94,
  altitude: 77.8,
  type: "Galaxy",
  constellation: "Andromeda",
};

function bestTonightCard(stateObj) {
  const card = new deepsky.NightSkyHighlights2Card();
  card.setConfig({});
  card._hass = makeHass({ [BEST_TONIGHT]: stateObj });
  return card;
}

// ── BUG 1: night-sky-highlights-2-card rendered "[object Object]" ────────────

test("BUG 1: Best DSO tile uses top_objects[0].name, not the object itself", () => {
  const card = bestTonightCard(makeState(BEST_TONIGHT, "15 objects visible — best: M31 (94%)", {
    top_objects: [LIVE_TOP_OBJECT],
    count_visible: 15,
  }));

  const dso = card._getBestDso();
  assert.equal(dso.name, "M31");
  assert.notEqual(dso.name, "[object Object]");
  assert.equal(String(dso.name).includes("[object"), false);
});

test("BUG 1: Best DSO score comes from top_objects[0].score", () => {
  const card = bestTonightCard(makeState(BEST_TONIGHT, "15 objects visible — best: M31 (94%)", {
    top_objects: [LIVE_TOP_OBJECT],
    count_visible: 15,
  }));

  // The sensor has no top-level `score` attribute, which is why the badge was missing.
  assert.equal(card._hass.states[BEST_TONIGHT].attributes.score, undefined);
  assert.equal(card._getBestDso().score, 94);
});

test("BUG 1: rendered markup contains the designation and the score badge", () => {
  const card = bestTonightCard(makeState(BEST_TONIGHT, "15 objects visible — best: M31 (94%)", {
    top_objects: [LIVE_TOP_OBJECT],
    count_visible: 15,
  }));

  card._render();
  const html = card.shadowRoot.innerHTML;
  assert.equal(html.includes("[object Object]"), false);
  assert.match(html, /M31 — 15 objects visible/);
  assert.match(html, /94%<\/span>/);
});

test("BUG 1: falls back to the sensor state when top_objects is empty", () => {
  const state = "15 objects visible — best: M31 (94%)";
  const card = bestTonightCard(makeState(BEST_TONIGHT, state, { top_objects: [], count_visible: 15 }));

  const dso = card._getBestDso();
  assert.equal(dso.name, state);
  assert.equal(dso.score, null);
});

test("BUG 1: tolerates a legacy list of plain strings", () => {
  const card = bestTonightCard(makeState(BEST_TONIGHT, "fallback", {
    top_objects: ["M31"],
    count_visible: 3,
  }));
  assert.equal(card._getBestDso().name, "M31");
});

// ── BUG 2: dso-tonight-table-card prefixed rows with the device name ─────────

test("BUG 2: object_name attribute wins over friendly_name", () => {
  const stateObj = makeState("sensor.nasa_astronomy_deepsky_m31_altitude", "77.8", {
    object_name: "M31",
    friendly_name: "Astronomy Space Suite Deep Sky M31 Altitude",
  });
  assert.equal(deepsky.dskObjectName(stateObj, "m31"), "M31");
});

test("BUG 2: device-name prefixed friendly_name is stripped when no attribute exists", () => {
  for (const [friendly, key, expected] of [
    ["Astronomy Space Suite Deep Sky M31 Altitude", "m31", "M31"],
    ["Astronomy Space Suite Deep Sky NGC 7000 Altitude", "ngc_7000", "NGC 7000"],
    ["Deep Sky NGC 7000 Altitude", "ngc_7000", "NGC 7000"],
    ["Deep Sky Ring Nebula Azimuth", "ring_nebula", "Ring Nebula"],
  ]) {
    const stateObj = makeState(`sensor.nasa_astronomy_deepsky_${key}_altitude`, "10", { friendly_name: friendly });
    assert.equal(deepsky.dskObjectName(stateObj, key), expected, friendly);
  }
});

test("BUG 2: falls back to the entity key when nothing else is available", () => {
  assert.equal(deepsky.dskObjectName(makeState("x", "1", {}), "ngc_7000"), "NGC 7000");
});

test("BUG 2: the friendly_name fallback survives a user device rename", () => {
  // has_entity_name = False means HA composes "<device name> <entity name>", so
  // renaming the device changes the prefix. The regex is unanchored for this.
  for (const device of ["Astronomy Space Suite", "Sky Stuff", "Jorises Telescoop", ""]) {
    const friendly = `${device} Deep Sky M31 Altitude`.trim();
    const stateObj = makeState("sensor.x", "10", { friendly_name: friendly });
    assert.equal(deepsky.dskObjectName(stateObj, "m31"), "M31", friendly);
  }
});

test("BUG 2: table rows render bare designations", () => {
  const states = {};
  for (const [key, name] of [["m31", "M31"], ["ngc_7000", "NGC 7000"]]) {
    states[`sensor.nasa_astronomy_deepsky_${key}_altitude`] = makeState(
      `sensor.nasa_astronomy_deepsky_${key}_altitude`,
      "60.0",
      {
        object_name: name,
        friendly_name: `Astronomy Space Suite Deep Sky ${name} Altitude`,
        score: 90,
        type: "Galaxy",
        constellation: "Andromeda",
      },
    );
    states[`sensor.nasa_astronomy_deepsky_${key}_azimuth`] = makeState("az", "120.0", {});
    states[`sensor.nasa_astronomy_deepsky_${key}_visible`] = makeState("vis", "Yes", {});
    states[`sensor.nasa_astronomy_deepsky_${key}_transit_time`] = makeState("tt", "23:41", {});
  }
  states[BEST_TONIGHT] = makeState(BEST_TONIGHT, "2 objects visible", { count_visible: 2, top_objects: [] });

  const card = new deepsky.DsoTonightTableCard();
  card.setConfig({ entity: BEST_TONIGHT });
  card.hass = makeHass(states);

  const html = card.shadowRoot.innerHTML;
  assert.equal(html.includes("Astronomy Space Suite"), false);
  assert.match(html, /<strong>M31<\/strong>/);
  assert.match(html, /<strong>NGC 7000<\/strong>/);
});

// ── BUG 3: rocket-launch-card showed impossible dates ────────────────────────

test("BUG 3: the legacy parser really did fabricate those dates", () => {
  // Documents the root cause: these are the exact strings the entity state held.
  assert.equal(new Date("EOS-05 (ISRO)").getFullYear(), 2001);
  assert.equal(new Date("Progress MS-35 (Roscosmos)").getFullYear(), 2035);
});

test("BUG 3: parseDate rejects mission names and other free-form text", () => {
  for (const value of [
    "EOS-05 (ISRO)",
    "Progress MS-35 (Roscosmos)",
    "Starlink Group 11-9 (SpaceX)",
    "Sep 03",
    "TBD",
    "",
    null,
    undefined,
    "unknown",
  ]) {
    assert.equal(astronomy.parseDate(value), null, `expected null for ${JSON.stringify(value)}`);
  }
});

test("BUG 3: parseDate still accepts every real timestamp shape in use", () => {
  const cases = [
    ["2026-09-03T21:25Z", "2026-09-03T21:25:00.000Z"],           // RocketLaunch.Live t0
    ["2026-09-03T01:16:53.808000+00:00", "2026-09-03T01:16:53.808Z"], // HA last_updated
    ["2026-06-16", "2026-06-16T00:00:00.000Z"],                   // APOD date
  ];
  for (const [input, expected] of cases) {
    assert.equal(astronomy.parseDate(input).toISOString(), expected, input);
  }
  // NASA NeoWs close_approach_date_full is not ISO but must still parse.
  assert.equal(astronomy.parseDate("2026-Sep-03 14:22").getFullYear(), 2026);
  // Open Notify publishes epoch seconds; treating them as milliseconds gave 1970.
  assert.equal(astronomy.parseDate(1788470700).toISOString(), "2026-09-03T21:25:00.000Z");
  assert.equal(astronomy.parseDate(1788470700000).toISOString(), "2026-09-03T21:25:00.000Z");
});

function parseLaunch(attributes, state = "EOS-05 (ISRO)", unitSystem) {
  const card = new astronomy.RocketLaunchCard();
  card.setConfig({});
  card._hass = makeHass({}, unitSystem);
  return card._parseLaunch(makeState("sensor.astronomy_space_suite_rocket_launch_1", state, attributes), "Launch 1");
}

test("BUG 3: a real launch payload yields the published T-0", () => {
  const launch = parseLaunch({
    name: "EOS-05",
    provider: "ISRO",
    vehicle: "GSLV-II",
    launch_target: "2026-09-03T21:25Z",
    t0: "2026-09-03T21:25Z",
    date_str: "Sep 03",
    launch_pad: "Satish Dhawan Space Centre (SLP)",
    launch_location: "India",
  });

  assert.equal(launch.launchDate.toISOString(), "2026-09-03T21:25:00.000Z");
  assert.equal(launch.padLocation, "Satish Dhawan Space Centre (SLP)");
  assert.notEqual(launch.padLocation, "Location TBD");
  assert.equal(launch.dateLabel.includes("2001"), false);
  assert.equal(launch.dateLabel.includes("2035"), false);
});

test("BUG 3: a missing T-0 degrades to TBD instead of a fabricated date", () => {
  const launch = parseLaunch({
    name: "Progress MS-35",
    provider: "Roscosmos",
    launch_target: "TBD",
    t0: "",
    win_open: "",
    date_str: "Dec 2026",
  });

  assert.equal(launch.launchDate, null);
  assert.equal(launch.countdown, "Date TBD");
  assert.equal(launch.dateLabel, "Dec 2026 (estimated)");
  assert.equal(launch.within24h, false);
});

test("BUG 3: with neither T-0 nor an estimate the label is Date TBD", () => {
  const launch = parseLaunch({ name: "Mystery", launch_target: "TBD" });
  assert.equal(launch.dateLabel, "Date TBD");
  assert.equal(launch.countdown, "Date TBD");
});

test("BUG 3: an empty pad string does not leak '()' into the card", () => {
  const launch = parseLaunch({ name: "X", launch_pad: "()", pad_name: "", location_name: "" });
  assert.equal(launch.padLocation, "Location TBD");
});

test("BUG 3: temperature is always rendered with a unit", () => {
  const attrs = {
    name: "EOS-05",
    weather_condition: "Drizzle",
    weather_temp_f: 79,
    weather_temp_c: 26.1,
    weather_wind_mph: 3.2,
    weather_wind_kph: 5.1,
  };

  const metric = parseLaunch(attrs, "EOS-05 (ISRO)", { temperature: "\u00b0C" });
  assert.equal(metric.weather, "Drizzle \u00b7 26 \u00b0C \u00b7 Wind 5 km/h");

  const imperial = parseLaunch(attrs, "EOS-05 (ISRO)", { temperature: "\u00b0F" });
  assert.equal(imperial.weather, "Drizzle \u00b7 79 \u00b0F \u00b7 Wind 3 mph");

  for (const rendered of [metric.weather, imperial.weather]) {
    assert.equal(/\d(?!\s*(?:\u00b0|km|mph))\s*$/.test(rendered), false, rendered);
  }
});

test("BUG 3: a unit-less legacy weather_summary is suppressed rather than shown bare", () => {
  const legacy = parseLaunch({ name: "EOS-05", weather_summary: "Drizzle, Temp: 79, Wind: 3" });
  assert.equal(legacy.weather, "");

  const usable = parseLaunch({ name: "EOS-05", weather_summary: "Clear, 21 \u00b0C" });
  assert.equal(usable.weather, "Clear, 21 \u00b0C");
});

// ── BUG 4: overlapping labels in the panorama and dome cards ─────────────────

function overlapping(labels, lineHeight = 9, padX = 2) {
  const clashes = [];
  for (let i = 0; i < labels.length; i += 1) {
    for (let j = i + 1; j < labels.length; j += 1) {
      const a = labels[i];
      const b = labels[j];
      if (Math.abs(a.y - b.y) < lineHeight
        && a.x < b.x + b.width + padX
        && b.x < a.x + a.width + padX) {
        clashes.push([a.text, b.text]);
      }
    }
  }
  return clashes;
}

test("BUG 4: NGC 869 / NGC 884 stop overlapping (panorama, same azimuth)", () => {
  const width = deepsky.dskTextWidth("NGC 869", 7);
  const input = [
    { x: 104 - width / 2, y: 40, width, text: "NGC 869" },
    { x: 104 - width / 2, y: 40, width, text: "NGC 884" },
  ];
  assert.equal(overlapping(input).length, 1, "precondition: the raw labels collide");

  const placed = deepsky.dskResolveLabelCollisions(input, { lineHeight: 9, minY: 7, maxY: 106 });
  assert.deepEqual(overlapping(placed), []);
  assert.deepEqual(placed.map((label) => label.text), ["NGC 869", "NGC 884"], "input order preserved");
});

test("BUG 4: M81 / M82 stop overlapping (panorama, 0.4° apart)", () => {
  const width = deepsky.dskTextWidth("M81", 7);
  const input = [
    { x: 23.3 - width / 2, y: 30, width, text: "M81" },
    { x: 22.7 - width / 2, y: 31, width, text: "M82" },
  ];
  assert.equal(overlapping(input).length, 1);
  assert.deepEqual(overlapping(deepsky.dskResolveLabelCollisions(input, { lineHeight: 9 })), []);
});

test("BUG 4: NGC 6992 / M27 stop overlapping (dome)", () => {
  const input = [
    { x: 210, y: 90, width: deepsky.dskTextWidth("NGC 6992", 8), text: "NGC 6992" },
    { x: 238, y: 92, width: deepsky.dskTextWidth("M27", 8), text: "M27" },
  ];
  assert.equal(overlapping(input, 10).length, 1);
  assert.deepEqual(overlapping(deepsky.dskResolveLabelCollisions(input, { lineHeight: 10 }), 10), []);
});

test("BUG 4: a dense cluster is fully separated and stays in bounds", () => {
  const input = Array.from({ length: 6 }, (_, i) => ({
    x: 100 + i,
    y: 60,
    width: 24,
    text: `OBJ${i}`,
  }));
  const placed = deepsky.dskResolveLabelCollisions(input, { lineHeight: 9, minY: 7, maxY: 106 });
  assert.deepEqual(overlapping(placed), []);
  for (const label of placed) {
    assert.ok(label.y >= 7 && label.y <= 106, `y=${label.y} out of bounds`);
  }
});

test("BUG 4: non-colliding labels are left exactly where they were", () => {
  const input = [
    { x: 10, y: 20, width: 20, text: "A" },
    { x: 200, y: 80, width: 20, text: "B" },
  ];
  const placed = deepsky.dskResolveLabelCollisions(input, { lineHeight: 9 });
  assert.deepEqual(placed.map((l) => [l.text, l.y, l.offset]), [["A", 20, 0], ["B", 80, 0]]);
});

/** The owner's reported colliding pairs, as real deep-sky sensor states. */
function collidingSkyStates() {
  const states = {};
  const add = (key, name, alt, az, type) => {
    states[`sensor.nasa_astronomy_deepsky_${key}_altitude`] = makeState(
      `sensor.nasa_astronomy_deepsky_${key}_altitude`,
      String(alt),
      { object_name: name, type },
    );
    states[`sensor.nasa_astronomy_deepsky_${key}_azimuth`] = makeState("az", String(az), {});
  };
  add("ngc_869", "NGC 869", 62.5, 62.5, "Cluster");
  add("ngc_884", "NGC 884", 62.4, 62.5, "Cluster");
  add("m81", "M81", 55.0, 14.0, "Galaxy");
  add("m82", "M82", 55.2, 13.6, "Galaxy");
  return states;
}

test("BUG 4: panorama renders NGC 869/884 and M81/82 as four separate labels", () => {
  const card = new deepsky.DsoPanoramaCard();
  card.setConfig({});
  card.hass = makeHass(collidingSkyStates());

  const html = card.shadowRoot.innerHTML;
  const labels = [...html.matchAll(/<text x="([\d.-]+)" y="([\d.-]+)"[^>]*>([^<]+)<\/text>/g)]
    .map(([, x, y, text]) => ({ x: Number(x), y: Number(y), text }));

  assert.deepEqual(
    labels.map((l) => l.text).sort(),
    ["M81", "M82", "NGC 869", "NGC 884"],
    "all four objects should still be labelled",
  );

  // Text is middle-anchored, so build the real boxes before checking overlap.
  const boxes = labels.map((l) => {
    const width = deepsky.dskTextWidth(l.text, 7);
    return { ...l, x: l.x - width / 2, width };
  });
  assert.deepEqual(overlapping(boxes, 9), []);

  // Displaced labels get a leader line back to their marker.
  assert.match(html, /<line [^>]*stroke-width="0.5"/);
});

test("BUG 4: dome draws its colliding pair without overlapping fillText calls", () => {
  // The dome only renders the front hemisphere, so use the southerly pair the
  // owner reported overlapping: NGC 6992 (Cygnus) and M27 (Vulpecula).
  const states = {};
  const add = (key, name, alt, az, type) => {
    states[`sensor.nasa_astronomy_deepsky_${key}_altitude`] = makeState(
      `sensor.nasa_astronomy_deepsky_${key}_altitude`,
      String(alt),
      { object_name: name, type },
    );
    states[`sensor.nasa_astronomy_deepsky_${key}_azimuth`] = makeState("az", String(az), {});
  };
  add("ngc_6992", "NGC 6992", 60.0, 175.0, "Nebula");
  add("m27", "M27", 62.0, 182.0, "Nebula");

  const card = new deepsky.DsoDomeCard();
  card.setConfig({});
  const canvas = stubCanvasShadowRoot(card);
  card.hass = makeHass(states);

  const drawn = canvas.fillText.filter((c) => !["N", "E", "S", "W"].includes(c.text));
  assert.deepEqual(drawn.map((c) => c.text).sort(), ["M27", "NGC 6992"]);

  const boxes = drawn.map((c) => ({ ...c, width: c.text.length * 0.55 * 8 }));
  assert.deepEqual(overlapping(boxes, 10), []);
  assert.ok(canvas.lines > 0, "the displaced dome label should get a leader line");
});

// ── BUG 5: earth-observation-card left a large empty band ────────────────────

test("BUG 5: the image frame no longer forces a fixed aspect ratio", () => {
  const source = readFileSync(BUNDLES.astronomy, "utf8");
  const rule = source.match(/\.earth-frame img \{[^}]*\}/);
  assert.ok(rule, ".earth-frame img rule not found");
  assert.equal(/aspect-ratio/.test(rule[0]), false, rule[0]);
  assert.equal(/object-fit/.test(rule[0]), false, rule[0]);
  assert.match(rule[0], /height:\s*auto/);
  assert.equal(/\.earth-frame\.sun img \{/.test(source), false, "sun-specific object-fit override should be gone");
});

// Class-level guard. A fixed ratio on square full-disc imagery either crops the
// disc or leaves a dead band, so every rule painting a solar/planetary disc must
// size itself to its image. The Earth card was fixed first; the Live Sun grid
// carried the identical defect and cropped ~25% of the disc.
test("BUG 5: no disc-image rule forces a fixed aspect ratio", () => {
  const source = readFileSync(BUNDLES.astronomy, "utf8");
  const discRules = [
    [".earth-frame img", /\.earth-frame img \{[^}]*\}/],
    [".live-sun-card img", /\.live-sun-card img \{[^}]*\}/],
  ];
  for (const [selector, pattern] of discRules) {
    const rule = source.match(pattern);
    assert.ok(rule, `${selector} rule not found`);
    assert.equal(/aspect-ratio/.test(rule[0]), false, `${selector} must not force a ratio: ${rule[0]}`);
    assert.equal(/object-fit/.test(rule[0]), false, `${selector} must not crop the disc: ${rule[0]}`);
    assert.match(rule[0], /height:\s*auto/, `${selector} must size to its image: ${rule[0]}`);
  }
});

test("BUG 5: APOD cropping is a deliberate exclusion, not the same defect", () => {
  const source = readFileSync(BUNDLES.astronomy, "utf8");
  const rule = source.match(/\.apod-media img,\s*\.apod-video iframe \{[^}]*\}/);
  assert.ok(rule, ".apod-media img rule not found");
  // APOD is arbitrary photography, not a disc on a black field, so cropping to
  // fill the hero area is a design choice rather than the BUG 5 defect. This
  // assertion exists to stop an over-correction sweep from "fixing" it too.
  // Changing it on purpose is fine — update this test when you do.
  assert.match(rule[0], /object-fit/, "APOD cropping is intentional; see comment above");
});

// ── Bundle sync guarantee ───────────────────────────────────────────────────

test("the custom_components and www card bundles are byte-identical", () => {
  for (const [a, b] of [
    [BUNDLES.astronomy, BUNDLES.astronomyWww],
    [BUNDLES.deepsky, BUNDLES.deepskyWww],
  ]) {
    assert.equal(readFileSync(a, "utf8"), readFileSync(b, "utf8"), `${a} != ${b}`);
  }
});
