console.info('deepsky-cards.js loading...'); /**
 * Deep Sky Cards Bundle
 * Version: 1.13.0
 *
 * Consolidated deep-sky observation cards for Astronomy Space Suite.
 * Includes: Night Sky Highlights 2, Tonight Table, Yard Map, Panorama, 3D Dome.
 * All Shadow DOM, no global CSS, auto-registered via window.customCards.
 */

const DEEPSKY_VERSION = "1.13.0";

// ═══════════════════════════════════════════════════════════════════════════════
// SHARED STYLES
// ═══════════════════════════════════════════════════════════════════════════════

const DSK_BASE_STYLES = `
  :host { display: block; }
  .dsk-card {
    padding: 16px;
    border-radius: var(--ha-card-border-radius, 12px);
    background: var(--ha-card-background, var(--card-background-color, #fff));
    box-shadow: var(--ha-card-box-shadow, none);
    color: var(--primary-text-color);
    font-family: var(--paper-font-body1_-_font-family, 'Roboto', sans-serif);
  }
  .dsk-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 14px;
  }
  .dsk-title { font-size: 1.15em; font-weight: 500; }
  .dsk-subtitle { font-size: 0.72em; color: var(--secondary-text-color); opacity: 0.7; }
  .dsk-badge {
    font-size: 0.65em; font-weight: 600; text-transform: uppercase;
    padding: 2px 7px; border-radius: 6px;
    background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
    color: var(--primary-color, #03a9f4); letter-spacing: 0.3px;
  }
  .dsk-vis-green { color: #4caf50; }
  .dsk-vis-yellow { color: #ff9800; }
  .dsk-vis-red { color: #f44336; }
  .dsk-empty { text-align: center; padding: 24px; color: var(--secondary-text-color); font-size: 0.9em; }
`;

function dskVisClass(score) {
  if (score == null || isNaN(score)) return "dsk-vis-yellow";
  if (score > 70) return "dsk-vis-green";
  if (score >= 40) return "dsk-vis-yellow";
  return "dsk-vis-red";
}

function dskGetState(hass, entityId) {
  if (!entityId || !hass) return null;
  const s = hass.states[entityId];
  if (!s || s.state === "unavailable" || s.state === "unknown") return null;
  return s;
}

const DSK_SENSOR_SUFFIXES = "Altitude|Azimuth|Transit Time|Visible|Score|Magnitude";

// Matches the "Deep Sky <object> <metric>" tail of a friendly_name.
//
// INTENTIONALLY UNANCHORED at the start — do not add a leading `^`. Home
// Assistant prepends the device name ("Astronomy Space Suite Deep Sky M31
// Altitude", see sensor_deepsky.py) and the user can rename that device at any
// time, so there is no fixed prefix to anchor against. Anchoring this would
// reintroduce BUG 2, where every table row rendered as "Astronomy Space Suite
// M31". The trailing `$` is deliberate and safe: the metric really is last.
const DSK_NAME_RE = new RegExp(`Deep Sky\\s+(.+?)\\s+(?:${DSK_SENSOR_SUFFIXES})$`, "i");

/**
 * Resolve the catalogue designation ("M31", "NGC 7000") for a deep-sky sensor.
 *
 * Prefers the dedicated `object_name` attribute exposed by sensor_deepsky.py.
 * Falls back to matching the "Deep Sky <name> <metric>" tail of friendly_name,
 * which drops any device-name prefix ("Astronomy Space Suite Deep Sky M31
 * Altitude") along with it. Last resort is the entity-id derived key.
 *
 * The prefix is HA working as designed, not a bug: the deep-sky sensors set
 * has_entity_name = False, which selects legacy naming, and legacy naming for a
 * device-attached entity composes "<device name> <entity name>". Because the
 * fallback is unanchored it also survives a device rename by the user.
 */
function dskObjectName(stateObj, objKey) {
  const attrs = stateObj?.attributes || {};
  if (typeof attrs.object_name === "string" && attrs.object_name.trim()) {
    return attrs.object_name.trim();
  }
  if (typeof attrs.friendly_name === "string") {
    const match = attrs.friendly_name.match(DSK_NAME_RE);
    if (match) return match[1].trim();
  }
  return String(objKey || "").replace(/_/g, " ").toUpperCase();
}

function dskEsc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[ch]));
}

/** Rough advance width for a short uppercase/numeric label in a sans-serif face. */
function dskTextWidth(text, fontSize) {
  return String(text ?? "").length * fontSize * 0.6;
}

/**
 * Nudge overlapping text labels apart vertically.
 *
 * Each label is `{ x, y, width }` where `x` is the LEFT edge of the text box and
 * `y` its baseline. Labels are placed top-down; each one tries its natural
 * position first, then alternates above/below in `lineHeight` steps until it no
 * longer collides with an already-placed label. Candidates outside
 * `[minY, maxY]` are skipped so labels stay inside the drawing area.
 *
 * Returns a copy in the original input order with `y` adjusted and `offset` set
 * to the applied displacement (0 when the label did not need to move).
 */
function dskResolveLabelCollisions(labels, options = {}) {
  const { lineHeight = 9, padX = 2, maxSteps = 6, minY = -Infinity, maxY = Infinity } = options;
  const placed = [];
  const ordered = labels
    .map((label, index) => ({ ...label, index, offset: 0 }))
    .sort((a, b) => a.y - b.y || a.x - b.x);

  for (const label of ordered) {
    let offset = 0;
    for (let step = 0; step <= maxSteps; step += 1) {
      offset = step === 0
        ? 0
        : (step % 2 === 1 ? -1 : 1) * Math.ceil(step / 2) * lineHeight;
      const y = label.y + offset;
      if (y < minY || y > maxY) continue;
      const clash = placed.some((other) =>
        Math.abs(other.y - y) < lineHeight
        && label.x < other.x + other.width + padX
        && other.x < label.x + label.width + padX);
      if (!clash) break;
    }
    label.y += offset;
    label.offset = offset;
    placed.push(label);
  }

  return ordered.sort((a, b) => a.index - b.index);
}

/**
 * Render a set of SVG labels with collision avoidance.
 *
 * Input labels are `{ x, y, width, anchorX, anchorY, color, text, textAnchor? }`.
 * Returns `{ leaders, text }` so the caller can draw the leader lines beneath the
 * object markers and the text on top.
 */
function dskRenderSvgLabels(labels, options = {}) {
  const { fontSize = 8, opacity = 0.8, ...layoutOptions } = options;
  const placed = dskResolveLabelCollisions(labels, { lineHeight: fontSize + 2, ...layoutOptions });

  let leaders = "";
  let text = "";
  for (const label of placed) {
    const anchorX = label.anchorX ?? label.x;
    const anchorY = label.anchorY ?? label.y;
    const textX = label.textAnchor === "middle" ? anchorX : label.x;
    if (label.offset) {
      // Displaced label: tie it back to its marker so the pairing stays obvious.
      const endY = label.offset < 0 ? label.y + 1 : label.y - fontSize + 1;
      leaders += `<line x1="${anchorX}" y1="${anchorY}" x2="${textX}" y2="${endY}" stroke="${label.color}" stroke-width="0.5" opacity="0.35"/>`;
    }
    text += `<text x="${textX}" y="${label.y}"${label.textAnchor ? ` text-anchor="${label.textAnchor}"` : ""} fill="${label.color}" font-size="${fontSize}" opacity="${opacity}">${dskEsc(label.text)}</text>`;
  }
  return { leaders, text };
}

// ═══════════════════════════════════════════════════════════════════════════════
// CARD 1: NIGHT SKY HIGHLIGHTS 2
// ═══════════════════════════════════════════════════════════════════════════════

const NSH2_STYLES = `
  ${DSK_BASE_STYLES}
  .nsh2-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
  .nsh2-tile {
    padding: 12px; border-radius: 10px;
    background: var(--card-background-color, rgba(0,0,0,0.03));
    border: 1px solid var(--divider-color, rgba(0,0,0,0.08));
    transition: transform 0.15s ease;
  }
  .nsh2-tile:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
  .nsh2-tile-header { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }
  .nsh2-icon { font-size: 1.5em; width: 32px; text-align: center; }
  .nsh2-tile-title { font-size: 0.9em; font-weight: 500; flex: 1; }
  .nsh2-score { font-size: 0.7em; font-weight: 600; padding: 2px 8px; border-radius: 12px; background: rgba(0,0,0,0.05); }
  .nsh2-desc { font-size: 0.8em; color: var(--secondary-text-color); line-height: 1.4; }
  .nsh2-unavail { opacity: 0.4; }
  @media (max-width: 600px) { .nsh2-grid { grid-template-columns: 1fr; } }
`;

class NightSkyHighlights2Card extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); this._config = {}; }
  static getConfigElement() { return document.createElement("night-sky-highlights-2-card-editor"); }
  static getStubConfig() {
    return { title: "Night Sky Highlights 2" };
  }
  setConfig(config) {
    this._config = { title: config.title || "Night Sky Highlights 2", ...config };
  }
  set hass(hass) { this._hass = hass; this._render(); }

  _buildTile(icon, title, score, desc, unavail) {
    const cls = unavail ? " nsh2-unavail" : "";
    const scoreHtml = score != null ? `<span class="nsh2-score ${dskVisClass(score)}">${Math.round(score)}%</span>` : "";
    return `<div class="nsh2-tile${cls}"><div class="nsh2-tile-header"><span class="nsh2-icon">${icon}</span><span class="nsh2-tile-title">${title}</span>${scoreHtml}</div><div class="nsh2-desc">${desc}</div></div>`;
  }

  _getHighestPlanet() {
    const planets = ["venus", "jupiter", "saturn", "mars", "mercury"];
    let best = null, bestAlt = -90;
    for (const p of planets) {
      const s = this._hass.states[`sensor.nasa_astronomy_ephemeris_${p}_altitude`];
      if (s && !isNaN(parseFloat(s.state)) && parseFloat(s.state) > bestAlt) {
        bestAlt = parseFloat(s.state);
        best = { name: p.charAt(0).toUpperCase() + p.slice(1), alt: bestAlt };
      }
    }
    return best;
  }

  _getBestDso() {
    const s = dskGetState(this._hass, "sensor.nasa_astronomy_deepsky_best_tonight");
    if (!s) return null;
    // top_objects is a list of objects: {name, score, altitude, type, constellation}.
    // Reading the entry itself would stringify to "[object Object]".
    const top = Array.isArray(s.attributes?.top_objects) ? s.attributes.top_objects[0] : null;
    const topName = top && typeof top === "object" ? top.name : top;
    const topScore = top && typeof top === "object" ? Number(top.score) : NaN;
    return {
      name: (typeof topName === "string" && topName.trim()) ? topName.trim() : s.state,
      count: s.attributes?.count_visible || 0,
      score: Number.isFinite(topScore) ? topScore : null,
    };
  }

  _render() {
    if (!this._hass || !this._config) return;
    const tiles = [];

    // Best planet
    const planet = this._getHighestPlanet();
    if (planet && planet.alt > 0) {
      const score = Math.min(100, Math.round((planet.alt / 60) * 100));
      tiles.push(this._buildTile("🪐", planet.name, score, `${planet.alt.toFixed(1)}° altitude`, false));
    } else {
      tiles.push(this._buildTile("🪐", "Best Planet", null, "No planets above horizon", true));
    }

    // Best DSO
    const dso = this._getBestDso();
    if (dso) {
      tiles.push(this._buildTile("🌌", "Best DSO Tonight", dso.score, `${dso.name} — ${dso.count} objects visible`, false));
    } else {
      tiles.push(this._buildTile("🌌", "Best DSO Tonight", null, "Waiting for data...", true));
    }

    // NEO count
    const neo = dskGetState(this._hass, "sensor.astronomy_space_suite_neo_count_today");
    if (neo) {
      tiles.push(this._buildTile("☄️", "Near Earth Objects", null, `${neo.state} objects tracked today`, false));
    } else {
      tiles.push(this._buildTile("☄️", "Near Earth Objects", null, "Waiting for data...", true));
    }

    // ISS
    const iss = dskGetState(this._hass, "sensor.astronomy_space_suite_iss_position");
    if (iss) {
      const lat = iss.attributes?.latitude || "?";
      const lon = iss.attributes?.longitude || "?";
      tiles.push(this._buildTile("🛰️", "ISS Position", null, `Lat ${lat}° Lon ${lon}°`, false));
    } else {
      tiles.push(this._buildTile("🛰️", "ISS Position", null, "Waiting for data...", true));
    }

    // Solar activity (KP index)
    const kp = dskGetState(this._hass, "sensor.astronomy_space_suite_planetary_kp_index");
    if (kp) {
      const kpVal = parseFloat(kp.state);
      const score = isNaN(kpVal) ? null : Math.min(100, Math.round(kpVal * 12.5));
      tiles.push(this._buildTile("☀️", "Geomagnetic Activity", score, `Kp Index: ${kp.state}`, false));
    } else {
      tiles.push(this._buildTile("☀️", "Geomagnetic Activity", null, "Waiting for data...", true));
    }

    // Solar flares
    const flares = dskGetState(this._hass, "sensor.astronomy_space_suite_solar_flares");
    if (flares) {
      tiles.push(this._buildTile("🔭", "Solar Flares (7d)", null, `${flares.state} events`, false));
    } else {
      tiles.push(this._buildTile("🔭", "Solar Flares", null, "Waiting for data...", true));
    }

    this.shadowRoot.innerHTML = `<style>${NSH2_STYLES}</style><ha-card><div class="dsk-card"><div class="dsk-header"><div><div class="dsk-title">${this._config.title}</div><div class="dsk-subtitle">Updated ${new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</div></div></div><div class="nsh2-grid">${tiles.join("")}</div></div></ha-card>`;
  }
  getCardSize() { return 4; }
}

class NightSkyHighlights2CardEditor extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); this._config = {}; }
  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(h) { this._hass = h; }
  _render() {
    this.shadowRoot.innerHTML = `<style>.ed{padding:16px}.f{margin-bottom:10px}.f label{display:block;font-size:0.8em;color:var(--secondary-text-color);margin-bottom:3px}.f input{width:100%;padding:7px;border:1px solid var(--divider-color,#ccc);border-radius:6px;box-sizing:border-box;font-size:0.85em;background:var(--card-background-color);color:var(--primary-text-color)}.note{font-size:0.75em;color:var(--secondary-text-color);margin-top:8px}</style><div class="ed"><div class="f"><label>Title</label><input id="t" value="${this._config.title || "Night Sky Highlights 2"}"/></div><div class="note">This card auto-detects sensors from the Astronomy Space Suite integration. No entity configuration needed.</div></div>`;
    this.shadowRoot.getElementById("t").addEventListener("input", ev => { this._config.title = ev.target.value; this._fire(); });
  }
  _fire() { this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: {...this._config} }, bubbles: true, composed: true })); }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CARD 2: DSO TONIGHT TABLE
// ═══════════════════════════════════════════════════════════════════════════════

const DSO_TABLE_STYLES = `
  ${DSK_BASE_STYLES}
  .dso-table { width: 100%; border-collapse: collapse; font-size: 0.82em; }
  .dso-table th { text-align: left; padding: 6px 8px; border-bottom: 2px solid var(--divider-color, #ddd); font-weight: 600; color: var(--secondary-text-color); font-size: 0.85em; }
  .dso-table td { padding: 6px 8px; border-bottom: 1px solid var(--divider-color, rgba(0,0,0,0.05)); }
  .dso-table tr:hover td { background: rgba(var(--rgb-primary-color, 3,169,244), 0.04); }
  .dso-score-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; }
  .dso-type-badge { font-size: 0.75em; padding: 1px 5px; border-radius: 4px; background: rgba(0,0,0,0.06); }
`;

class DsoTonightTableCard extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); this._config = {}; }
  static getConfigElement() { return document.createElement("dso-tonight-table-card-editor"); }
  static getStubConfig() { return { title: "Deep Sky Tonight", entity: "sensor.nasa_astronomy_deepsky_best_tonight" }; }
  setConfig(config) { this._config = { title: config.title || "Deep Sky Tonight", entity: config.entity || "sensor.nasa_astronomy_deepsky_best_tonight", ...config }; }
  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;
    const state = dskGetState(this._hass, this._config.entity);
    if (!state) {
      this.shadowRoot.innerHTML = `<style>${DSO_TABLE_STYLES}</style><ha-card><div class="dsk-card"><div class="dsk-header"><div class="dsk-title">${this._config.title}</div></div><div class="dsk-empty">🔭 Waiting for deep-sky data...</div></div></ha-card>`;
      return;
    }

    const attrs = state.attributes || {};
    const topObjects = attrs.top_objects || [];
    const countVisible = attrs.count_visible || 0;

    // Also gather individual DSO sensors for the table
    const rows = [];
    const dsoStates = Object.entries(this._hass.states).filter(([id]) => id.startsWith("sensor.nasa_astronomy_deepsky_") && id.endsWith("_altitude"));

    for (const [id, s] of dsoStates) {
      const objKey = id.replace("sensor.nasa_astronomy_deepsky_", "").replace("_altitude", "");
      const alt = parseFloat(s.state);
      if (isNaN(alt)) continue;

      const azState = this._hass.states[`sensor.nasa_astronomy_deepsky_${objKey}_azimuth`];
      const visState = this._hass.states[`sensor.nasa_astronomy_deepsky_${objKey}_visible`];
      const transitState = this._hass.states[`sensor.nasa_astronomy_deepsky_${objKey}_transit_time`];

      const az = azState ? parseFloat(azState.state) : 0;
      const visible = visState ? visState.state === "Yes" : alt > 15;
      const transit = transitState ? transitState.state : "";
      const score = s.attributes?.score || 0;
      const type = s.attributes?.type || "";
      const name = dskObjectName(s, objKey);
      const constellation = s.attributes?.constellation || "";

      if (visible) {
        rows.push({ name, alt, az, transit, score, type, constellation });
      }
    }

    rows.sort((a, b) => b.score - a.score);
    const displayRows = rows.slice(0, 15);

    let tableHtml = "";
    if (displayRows.length > 0) {
      tableHtml = `<table class="dso-table"><thead><tr><th>Object</th><th>Alt</th><th>Az</th><th>Transit</th><th>Type</th><th>Score</th></tr></thead><tbody>`;
      for (const r of displayRows) {
        const dotColor = r.score > 70 ? "#4caf50" : r.score >= 40 ? "#ff9800" : "#f44336";
        tableHtml += `<tr><td><strong>${r.name}</strong><br><span style="font-size:0.8em;color:var(--secondary-text-color)">${r.constellation}</span></td><td>${r.alt}°</td><td>${r.az}°</td><td>${r.transit}</td><td><span class="dso-type-badge">${r.type}</span></td><td><span class="dso-score-dot" style="background:${dotColor}"></span>${r.score}</td></tr>`;
      }
      tableHtml += `</tbody></table>`;
    } else {
      tableHtml = `<div class="dsk-empty">No objects visible above minimum altitude</div>`;
    }

    this.shadowRoot.innerHTML = `<style>${DSO_TABLE_STYLES}</style><ha-card><div class="dsk-card"><div class="dsk-header"><div><div class="dsk-title">${this._config.title}</div><div class="dsk-subtitle">${countVisible} objects visible tonight</div></div></div>${tableHtml}</div></ha-card>`;
  }
  getCardSize() { return 5; }
}

class DsoTonightTableCardEditor extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); }
  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(h) {}
  _render() {
    this.shadowRoot.innerHTML = `<style>.ed{padding:16px}.f{margin-bottom:10px}.f label{display:block;font-size:0.8em;margin-bottom:3px;color:var(--secondary-text-color)}.f input{width:100%;padding:7px;border:1px solid var(--divider-color,#ccc);border-radius:6px;box-sizing:border-box;background:var(--card-background-color);color:var(--primary-text-color)}</style><div class="ed"><div class="f"><label>Title</label><input id="t" value="${this._config.title||"Deep Sky Tonight"}"/></div><div class="f"><label>Best Tonight Entity</label><input id="e" value="${this._config.entity||"sensor.nasa_astronomy_deepsky_best_tonight"}"/></div></div>`;
    this.shadowRoot.getElementById("t").addEventListener("input", ev => { this._config.title = ev.target.value; this._fire(); });
    this.shadowRoot.getElementById("e").addEventListener("input", ev => { this._config.entity = ev.target.value; this._fire(); });
  }
  _fire() { this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: {...this._config} }, bubbles: true, composed: true })); }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CARD 3: YARD MAP (SVG top-down view)
// ═══════════════════════════════════════════════════════════════════════════════

const YARD_MAP_STYLES = `
  ${DSK_BASE_STYLES}
  .yard-svg { width: 100%; aspect-ratio: 1; border-radius: 50%; overflow: hidden; background: radial-gradient(circle, #0d1b2a 0%, #1b2838 70%, #2c3e50 100%); position: relative; }
  .yard-svg svg { width: 100%; height: 100%; position: relative; z-index: 2; }
  .yard-bg-map { position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; border-radius: 50%; opacity: 0.35; object-fit: cover; pointer-events: none; }
  .yard-legend { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; justify-content: center; font-size: 0.72em; color: var(--secondary-text-color); }
  .yard-legend-item { display: flex; align-items: center; gap: 4px; }
  .yard-legend-dot { width: 8px; height: 8px; border-radius: 50%; }
`;

class DsoYardMapCard extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); this._config = {}; }
  static getConfigElement() { return document.createElement("dso-yard-map-card-editor"); }
  static getStubConfig() { return { title: "Sky Map", show_house_map: false, map_latitude: "", map_longitude: "", map_zoom: 18 }; }
  setConfig(config) { this._config = { title: config.title || "Sky Map", show_house_map: false, map_zoom: 18, ...config }; }
  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;

    // Gather all visible DSOs
    const objects = [];
    const dsoStates = Object.entries(this._hass.states).filter(([id]) => id.startsWith("sensor.nasa_astronomy_deepsky_") && id.endsWith("_altitude"));

    for (const [id, s] of dsoStates) {
      const objKey = id.replace("sensor.nasa_astronomy_deepsky_", "").replace("_altitude", "");
      const alt = parseFloat(s.state);
      if (isNaN(alt) || alt < 0) continue;

      const azState = this._hass.states[`sensor.nasa_astronomy_deepsky_${objKey}_azimuth`];
      const az = azState ? parseFloat(azState.state) : 0;
      const score = s.attributes?.score || 0;
      const type = s.attributes?.type || "Unknown";
      const name = dskObjectName(s, objKey);

      objects.push({ name, alt, az, score, type });
    }

    // Also add planets from ephemeris if available
    const planets = ["mercury", "venus", "mars", "jupiter", "saturn"];
    for (const p of planets) {
      const altState = this._hass.states[`sensor.nasa_astronomy_ephemeris_${p}_altitude`];
      const azState = this._hass.states[`sensor.nasa_astronomy_ephemeris_${p}_azimuth`];
      if (altState && azState) {
        const alt = parseFloat(altState.state);
        const az = parseFloat(azState.state);
        if (!isNaN(alt) && alt > 0) {
          objects.push({ name: p.charAt(0).toUpperCase() + p.slice(1), alt, az, score: 80, type: "Planet" });
        }
      }
    }

    // Convert alt/az to SVG coordinates (polar projection)
    const size = 300;
    const cx = size / 2, cy = size / 2;
    const maxR = size / 2 - 20;

    let dots = "";
    const labelFontSize = 8;
    const labelInputs = [];
    for (const obj of objects) {
      const r = maxR * (1 - obj.alt / 90); // 90° at center, 0° at edge
      const angle = (obj.az - 90) * Math.PI / 180; // 0° = North = top
      const x = cx + r * Math.cos(angle);
      const y = cy + r * Math.sin(angle);
      const color = obj.type === "Planet" ? "#ffd700" : obj.type === "Galaxy" ? "#e040fb" : obj.type === "Nebula" ? "#00e5ff" : "#69f0ae";
      const radius = obj.score > 60 ? 5 : 4;
      dots += `<circle cx="${x}" cy="${y}" r="${radius}" fill="${color}" opacity="0.9"><title>${dskEsc(obj.name)} (${obj.alt}° alt, ${obj.az}° az)</title></circle>`;
      if (obj.score > 50) {
        labelInputs.push({
          x: x + 7,
          y: y + 3,
          width: dskTextWidth(obj.name, labelFontSize),
          anchorX: x,
          anchorY: y,
          color,
          text: obj.name,
        });
      }
    }

    const { leaders, text: labelText } = dskRenderSvgLabels(labelInputs, {
      fontSize: labelFontSize,
      minY: labelFontSize,
      maxY: size - 4,
    });

    // Cardinal directions
    const cardinals = `
      <text x="${cx}" y="14" text-anchor="middle" fill="#ffffff80" font-size="10">N</text>
      <text x="${cx}" y="${size - 6}" text-anchor="middle" fill="#ffffff80" font-size="10">S</text>
      <text x="8" y="${cy + 4}" text-anchor="middle" fill="#ffffff80" font-size="10">E</text>
      <text x="${size - 8}" y="${cy + 4}" text-anchor="middle" fill="#ffffff80" font-size="10">W</text>
    `;

    // Altitude rings
    const rings = [30, 60].map(a => {
      const rr = maxR * (1 - a / 90);
      return `<circle cx="${cx}" cy="${cy}" r="${rr}" fill="none" stroke="#ffffff15" stroke-width="0.5" stroke-dasharray="3,3"/>`;
    }).join("");

    const svg = `<svg viewBox="0 0 ${size} ${size}" xmlns="http://www.w3.org/2000/svg">
      <circle cx="${cx}" cy="${cy}" r="${maxR}" fill="none" stroke="#ffffff20" stroke-width="1"/>
      ${rings}
      <line x1="${cx}" y1="20" x2="${cx}" y2="${size-20}" stroke="#ffffff10" stroke-width="0.5"/>
      <line x1="20" y1="${cy}" x2="${size-20}" y2="${cy}" stroke="#ffffff10" stroke-width="0.5"/>
      ${cardinals}
      ${leaders}
      ${dots}
      ${labelText}
    </svg>`;

    const legend = `<div class="yard-legend">
      <div class="yard-legend-item"><span class="yard-legend-dot" style="background:#ffd700"></span>Planet</div>
      <div class="yard-legend-item"><span class="yard-legend-dot" style="background:#e040fb"></span>Galaxy</div>
      <div class="yard-legend-item"><span class="yard-legend-dot" style="background:#00e5ff"></span>Nebula</div>
      <div class="yard-legend-item"><span class="yard-legend-dot" style="background:#69f0ae"></span>Cluster</div>
    </div>`;

    // House map background overlay
    let houseMapBg = "";
    if (this._config.show_house_map) {
      const lat = this._config.map_latitude || this._hass.config?.latitude || 52.37;
      const lon = this._config.map_longitude || this._hass.config?.longitude || 4.89;
      const zoom = Math.max(14, Math.min(20, parseInt(this._config.map_zoom) || 18));
      // Use OpenStreetMap static tile — dark style from CartoDB
      const tileUrl = `https://basemaps.cartocdn.com/dark_all/${zoom}/${this._lonToTileX(lon, zoom)}/${this._latToTileY(lat, zoom)}.png`;
      houseMapBg = `<img class="yard-bg-map" src="${tileUrl}" alt="" />`;
    }

    this.shadowRoot.innerHTML = `<style>${YARD_MAP_STYLES}</style><ha-card><div class="dsk-card"><div class="dsk-header"><div class="dsk-title">${this._config.title}</div><span class="dsk-badge">${objects.length} objects</span></div><div class="yard-svg">${houseMapBg}${svg}</div>${legend}</div></ha-card>`;
  }
  _lonToTileX(lon, zoom) { return Math.floor((lon + 180) / 360 * Math.pow(2, zoom)); }
  _latToTileY(lat, zoom) { const r = lat * Math.PI / 180; return Math.floor((1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * Math.pow(2, zoom)); }
  getCardSize() { return 6; }
}

class DsoYardMapCardEditor extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); }
  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(h) {}
  _render() {
    const showMap = this._config.show_house_map ? "checked" : "";
    this.shadowRoot.innerHTML = `<style>.ed{padding:16px}.f{margin-bottom:10px}.f label{display:block;font-size:0.8em;margin-bottom:3px;color:var(--secondary-text-color)}.f input,.f select{width:100%;padding:7px;border:1px solid var(--divider-color,#ccc);border-radius:6px;box-sizing:border-box;background:var(--card-background-color);color:var(--primary-text-color)}.sw{display:flex;align-items:center;gap:8px;margin-bottom:10px}.sw input[type=checkbox]{width:18px;height:18px}</style>
    <div class="ed">
      <div class="f"><label>Title</label><input id="t" value="${this._config.title||"Sky Map"}"/></div>
      <div class="sw"><input type="checkbox" id="sm" ${showMap}/><label for="sm">Show house map overlay</label></div>
      <div class="f"><label>Latitude (blank = HA default)</label><input id="lat" type="number" step="any" value="${this._config.map_latitude||""}"/></div>
      <div class="f"><label>Longitude (blank = HA default)</label><input id="lon" type="number" step="any" value="${this._config.map_longitude||""}"/></div>
      <div class="f"><label>Zoom (14-20)</label><input id="z" type="number" min="14" max="20" value="${this._config.map_zoom||18}"/></div>
    </div>`;
    this.shadowRoot.getElementById("t").addEventListener("input", ev => { this._config.title = ev.target.value; this._fire(); });
    this.shadowRoot.getElementById("sm").addEventListener("change", ev => { this._config.show_house_map = ev.target.checked; this._fire(); });
    this.shadowRoot.getElementById("lat").addEventListener("input", ev => { this._config.map_latitude = ev.target.value; this._fire(); });
    this.shadowRoot.getElementById("lon").addEventListener("input", ev => { this._config.map_longitude = ev.target.value; this._fire(); });
    this.shadowRoot.getElementById("z").addEventListener("input", ev => { this._config.map_zoom = parseInt(ev.target.value) || 18; this._fire(); });
  }
  _fire() { this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: {...this._config} }, bubbles: true, composed: true })); }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CARD 4: PANORAMA (Horizon strip)
// ═══════════════════════════════════════════════════════════════════════════════

const PANORAMA_STYLES = `
  ${DSK_BASE_STYLES}
  .pano-strip { width: 100%; height: 120px; border-radius: 8px; overflow: hidden; position: relative; background: linear-gradient(180deg, #0d1b2a 0%, #1b2838 60%, #2d4a3e 85%, #3d5a4e 100%); }
  .pano-strip svg { width: 100%; height: 100%; }
  .pano-compass { display: flex; justify-content: space-between; padding: 4px 8px; font-size: 0.7em; color: var(--secondary-text-color); }
`;

class DsoPanoramaCard extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); this._config = {}; }
  static getConfigElement() { return document.createElement("dso-panorama-card-editor"); }
  static getStubConfig() { return { title: "Horizon Panorama" }; }
  setConfig(config) { this._config = { title: config.title || "Horizon Panorama", ...config }; }
  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;

    const width = 600, height = 120;
    const objects = [];

    // Gather DSOs above horizon
    const dsoStates = Object.entries(this._hass.states).filter(([id]) => id.startsWith("sensor.nasa_astronomy_deepsky_") && id.endsWith("_altitude"));
    for (const [id, s] of dsoStates) {
      const objKey = id.replace("sensor.nasa_astronomy_deepsky_", "").replace("_altitude", "");
      const alt = parseFloat(s.state);
      if (isNaN(alt) || alt < 0) continue;
      const azState = this._hass.states[`sensor.nasa_astronomy_deepsky_${objKey}_azimuth`];
      const az = azState ? parseFloat(azState.state) : 0;
      const type = s.attributes?.type || "Unknown";
      const name = dskObjectName(s, objKey);
      objects.push({ name, alt, az, type });
    }

    // Add planets
    const planets = ["mercury", "venus", "mars", "jupiter", "saturn"];
    for (const p of planets) {
      const altS = this._hass.states[`sensor.nasa_astronomy_ephemeris_${p}_altitude`];
      const azS = this._hass.states[`sensor.nasa_astronomy_ephemeris_${p}_azimuth`];
      if (altS && azS) {
        const alt = parseFloat(altS.state);
        const az = parseFloat(azS.state);
        if (!isNaN(alt) && alt > 0) objects.push({ name: p.charAt(0).toUpperCase() + p.slice(1), alt, az, type: "Planet" });
      }
    }

    // Map to panorama: x = azimuth (0-360 → 0-width), y = altitude (0-90 → bottom-top)
    const panoFontSize = 7;
    let dots = "";
    const labelInputs = [];
    for (const obj of objects) {
      const x = (obj.az / 360) * width;
      const y = height - (obj.alt / 90) * (height - 15) - 10;
      const color = obj.type === "Planet" ? "#ffd700" : obj.type === "Galaxy" ? "#e040fb" : obj.type === "Nebula" ? "#00e5ff" : "#69f0ae";
      dots += `<circle cx="${x}" cy="${y}" r="4" fill="${color}" opacity="0.85"><title>${dskEsc(obj.name)} (${obj.alt}° alt)</title></circle>`;
      if (obj.alt > 30) {
        const textWidth = dskTextWidth(obj.name, panoFontSize);
        labelInputs.push({
          x: x - textWidth / 2,
          y: y - 7,
          width: textWidth,
          anchorX: x,
          anchorY: y,
          color,
          text: obj.name,
          textAnchor: "middle",
        });
      }
    }

    const { leaders, text: labelText } = dskRenderSvgLabels(labelInputs, {
      fontSize: panoFontSize,
      minY: panoFontSize,
      maxY: height - 14,
    });

    // Horizon line
    const horizon = `<line x1="0" y1="${height - 10}" x2="${width}" y2="${height - 10}" stroke="#ffffff20" stroke-width="1"/>`;

    const svg = `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">${horizon}${leaders}${dots}${labelText}</svg>`;
    const compass = `<div class="pano-compass"><span>N</span><span>NE</span><span>E</span><span>SE</span><span>S</span><span>SW</span><span>W</span><span>NW</span><span>N</span></div>`;

    this.shadowRoot.innerHTML = `<style>${PANORAMA_STYLES}</style><ha-card><div class="dsk-card"><div class="dsk-header"><div class="dsk-title">${this._config.title}</div><span class="dsk-badge">${objects.length} above horizon</span></div><div class="pano-strip">${svg}</div>${compass}</div></ha-card>`;
  }
  getCardSize() { return 3; }
}

class DsoPanoramaCardEditor extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); }
  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(h) {}
  _render() {
    this.shadowRoot.innerHTML = `<style>.ed{padding:16px}.f{margin-bottom:10px}.f label{display:block;font-size:0.8em;margin-bottom:3px;color:var(--secondary-text-color)}.f input{width:100%;padding:7px;border:1px solid var(--divider-color,#ccc);border-radius:6px;box-sizing:border-box;background:var(--card-background-color);color:var(--primary-text-color)}</style><div class="ed"><div class="f"><label>Title</label><input id="t" value="${this._config.title||"Horizon Panorama"}"/></div></div>`;
    this.shadowRoot.getElementById("t").addEventListener("input", ev => { this._config.title = ev.target.value; this._fire(); });
  }
  _fire() { this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: {...this._config} }, bubbles: true, composed: true })); }
}

// ═══════════════════════════════════════════════════════════════════════════════
// CARD 5: 3D DOME (Canvas-backed)
// ═══════════════════════════════════════════════════════════════════════════════

const DOME_STYLES = `
  ${DSK_BASE_STYLES}
  .dome-container { width: 100%; aspect-ratio: 1.2; border-radius: 10px; overflow: hidden; position: relative; cursor: grab; background: radial-gradient(ellipse at center, #0a0e1a 0%, #0d1520 100%); }
  .dome-container canvas { width: 100%; height: 100%; }
  .dome-container:active { cursor: grabbing; }
  .dome-info { position: absolute; bottom: 8px; left: 8px; font-size: 0.7em; color: #ffffff80; pointer-events: none; }
`;

class DsoDomeCard extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); this._config = {}; this._rotation = 0; this._dragging = false; }
  static getConfigElement() { return document.createElement("dso-dome-card-editor"); }
  static getStubConfig() { return { title: "3D Sky Dome" }; }
  setConfig(config) { this._config = { title: config.title || "3D Sky Dome", ...config }; }
  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;

    this.shadowRoot.innerHTML = `<style>${DOME_STYLES}</style><ha-card><div class="dsk-card"><div class="dsk-header"><div class="dsk-title">${this._config.title}</div><span class="dsk-badge">Drag to rotate</span></div><div class="dome-container"><canvas id="dome"></canvas><div class="dome-info">↔ Drag to look around</div></div></div></ha-card>`;

    const container = this.shadowRoot.querySelector(".dome-container");
    const canvas = this.shadowRoot.getElementById("dome");
    if (!canvas) return;

    // Set canvas resolution
    const rect = container.getBoundingClientRect();
    const w = rect.width || 400;
    const h = rect.height || 333;
    canvas.width = w * 2;
    canvas.height = h * 2;
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";

    const ctx = canvas.getContext("2d");
    ctx.scale(2, 2);

    // Gather objects
    const objects = [];
    const dsoStates = Object.entries(this._hass.states).filter(([id]) => id.startsWith("sensor.nasa_astronomy_deepsky_") && id.endsWith("_altitude"));
    for (const [id, s] of dsoStates) {
      const objKey = id.replace("sensor.nasa_astronomy_deepsky_", "").replace("_altitude", "");
      const alt = parseFloat(s.state);
      if (isNaN(alt) || alt < 0) continue;
      const azState = this._hass.states[`sensor.nasa_astronomy_deepsky_${objKey}_azimuth`];
      const az = azState ? parseFloat(azState.state) : 0;
      const type = s.attributes?.type || "Unknown";
      const name = dskObjectName(s, objKey);
      objects.push({ name, alt, az, type });
    }

    // Add planets
    ["mercury", "venus", "mars", "jupiter", "saturn"].forEach(p => {
      const altS = this._hass.states[`sensor.nasa_astronomy_ephemeris_${p}_altitude`];
      const azS = this._hass.states[`sensor.nasa_astronomy_ephemeris_${p}_azimuth`];
      if (altS && azS) {
        const alt = parseFloat(altS.state), az = parseFloat(azS.state);
        if (!isNaN(alt) && alt > 0) objects.push({ name: p.charAt(0).toUpperCase() + p.slice(1), alt, az, type: "Planet" });
      }
    });

    this._drawDome(ctx, w, h, objects);

    // Drag to rotate
    let startX = 0;
    container.addEventListener("pointerdown", (e) => { this._dragging = true; startX = e.clientX; container.setPointerCapture(e.pointerId); });
    container.addEventListener("pointermove", (e) => {
      if (!this._dragging) return;
      const dx = e.clientX - startX;
      startX = e.clientX;
      this._rotation = (this._rotation + dx * 0.5) % 360;
      ctx.clearRect(0, 0, w, h);
      this._drawDome(ctx, w, h, objects);
    });
    container.addEventListener("pointerup", () => { this._dragging = false; });
  }

  _drawDome(ctx, w, h, objects) {
    const cx = w / 2, cy = h * 0.85;
    const maxR = Math.min(w, h) * 0.7;

    // Draw dome outline
    ctx.beginPath();
    ctx.ellipse(cx, cy, maxR, maxR * 0.6, 0, Math.PI, 0);
    ctx.strokeStyle = "#ffffff15";
    ctx.lineWidth = 1;
    ctx.stroke();

    // Altitude rings
    [30, 60].forEach(a => {
      const r = maxR * (1 - a / 90);
      ctx.beginPath();
      ctx.ellipse(cx, cy, r, r * 0.6, 0, Math.PI, 0);
      ctx.strokeStyle = "#ffffff08";
      ctx.lineWidth = 0.5;
      ctx.setLineDash([3, 3]);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // Draw objects
    const labelFontSize = 8;
    const labelInputs = [];
    ctx.font = `${labelFontSize}px sans-serif`;
    ctx.textAlign = "left";
    for (const obj of objects) {
      const adjustedAz = ((obj.az - this._rotation) % 360 + 360) % 360;
      // Only show front hemisphere (90-270 wrapped)
      const angleRad = (adjustedAz - 180) * Math.PI / 180;
      const dist = maxR * (1 - obj.alt / 90);
      const x = cx + dist * Math.sin(angleRad);
      const yBase = cy - dist * Math.cos(angleRad) * 0.6; // perspective squish

      if (yBase > cy) continue; // below horizon

      const color = obj.type === "Planet" ? "#ffd700" : obj.type === "Galaxy" ? "#e040fb" : obj.type === "Nebula" ? "#00e5ff" : "#69f0ae";

      ctx.beginPath();
      ctx.arc(x, yBase, 4, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.globalAlpha = 0.85;
      ctx.fill();
      ctx.globalAlpha = 1;

      if (obj.alt > 20) {
        labelInputs.push({
          x: x + 6,
          y: yBase + 3,
          width: ctx.measureText(obj.name).width,
          anchorX: x,
          anchorY: yBase,
          color,
          text: obj.name,
        });
      }
    }

    // Labels last, nudged apart so angularly close objects stay readable.
    const placedLabels = dskResolveLabelCollisions(labelInputs, {
      lineHeight: labelFontSize + 2,
      minY: labelFontSize,
      maxY: cy,
    });
    for (const label of placedLabels) {
      ctx.globalAlpha = 0.7;
      ctx.strokeStyle = label.color;
      ctx.fillStyle = label.color;
      if (label.offset) {
        ctx.globalAlpha = 0.3;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(label.anchorX, label.anchorY);
        ctx.lineTo(label.x, label.y - labelFontSize / 3);
        ctx.stroke();
        ctx.globalAlpha = 0.7;
      }
      ctx.fillText(label.text, label.x, label.y);
      ctx.globalAlpha = 1;
    }

    // Cardinal labels
    ctx.font = "10px sans-serif";
    ctx.fillStyle = "#ffffff60";
    ctx.textAlign = "center";
    const cardinals = [["N", 0], ["E", 90], ["S", 180], ["W", 270]];
    for (const [label, bearing] of cardinals) {
      const adj = ((bearing - this._rotation) % 360 + 360) % 360;
      const rad = (adj - 180) * Math.PI / 180;
      const lx = cx + (maxR + 12) * Math.sin(rad);
      const ly = cy - (maxR + 12) * Math.cos(rad) * 0.6;
      if (ly < cy) ctx.fillText(label, lx, ly);
    }
  }

  getCardSize() { return 6; }
}

class DsoDomeCardEditor extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: "open" }); }
  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(h) {}
  _render() {
    this.shadowRoot.innerHTML = `<style>.ed{padding:16px}.f{margin-bottom:10px}.f label{display:block;font-size:0.8em;margin-bottom:3px;color:var(--secondary-text-color)}.f input{width:100%;padding:7px;border:1px solid var(--divider-color,#ccc);border-radius:6px;box-sizing:border-box;background:var(--card-background-color);color:var(--primary-text-color)}</style><div class="ed"><div class="f"><label>Title</label><input id="t" value="${this._config.title||"3D Sky Dome"}"/></div></div>`;
    this.shadowRoot.getElementById("t").addEventListener("input", ev => { this._config.title = ev.target.value; this._fire(); });
  }
  _fire() { this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: {...this._config} }, bubbles: true, composed: true })); }
}

// ═══════════════════════════════════════════════════════════════════════════════
// REGISTRATION
// ═══════════════════════════════════════════════════════════════════════════════

customElements.get("night-sky-highlights-2-card") || customElements.define("night-sky-highlights-2-card", NightSkyHighlights2Card);
customElements.get("night-sky-highlights-2-card-editor") || customElements.define("night-sky-highlights-2-card-editor", NightSkyHighlights2CardEditor);
customElements.get("dso-tonight-table-card") || customElements.define("dso-tonight-table-card", DsoTonightTableCard);
customElements.get("dso-tonight-table-card-editor") || customElements.define("dso-tonight-table-card-editor", DsoTonightTableCardEditor);
customElements.get("dso-yard-map-card") || customElements.define("dso-yard-map-card", DsoYardMapCard);
customElements.get("dso-yard-map-card-editor") || customElements.define("dso-yard-map-card-editor", DsoYardMapCardEditor);
customElements.get("dso-panorama-card") || customElements.define("dso-panorama-card", DsoPanoramaCard);
customElements.get("dso-panorama-card-editor") || customElements.define("dso-panorama-card-editor", DsoPanoramaCardEditor);
customElements.get("dso-dome-card") || customElements.define("dso-dome-card", DsoDomeCard);
customElements.get("dso-dome-card-editor") || customElements.define("dso-dome-card-editor", DsoDomeCardEditor);

window.customCards = window.customCards || [];
window.customCards.push(
  { type: "night-sky-highlights-2-card", name: "ASS Night Sky Highlights 2", description: "Enhanced night sky highlights with visibility scores.", preview: true },
  { type: "dso-tonight-table-card", name: "ASS Deep Sky Tonight", description: "Table of best deep-sky objects visible tonight.", preview: true },
  { type: "dso-yard-map-card", name: "ASS Sky Map", description: "Top-down polar projection of visible objects.", preview: true },
  { type: "dso-panorama-card", name: "ASS Horizon Panorama", description: "360° horizon strip showing object positions.", preview: true },
  { type: "dso-dome-card", name: "ASS 3D Sky Dome", description: "Interactive 3D dome view — drag to rotate.", preview: true },
);

console.info(
  `%c  DEEPSKY-CARDS  %c  v${DEEPSKY_VERSION}  `,
  "background: #1a237e; color: #fff; font-weight: bold;",
  "background: #283593; color: #fff;"
);
