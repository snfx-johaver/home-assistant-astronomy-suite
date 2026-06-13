/**
 * Astronomy Space Suite Cards v1.7.2
 * Pre-built Astronomy Space Suite bundle for Home Assistant Lovelace.
 *
 * Cards:
 *  - <apod-card>
 *  - <neo-threat-card>
 *  - <solar-activity-card>
 *  - <astro-horizon-card>
 *  - <astro-lunar-card>
 *  - <solar-system-card>
 *  - <rocket-launch-card>
 *  - <iss-tracker-card>
 *  - <earth-observation-card>
 */

const ASTRO = {
  radius: "var(--ha-card-border-radius, 12px)",
  shadow: "var(--ha-card-box-shadow, none)",
  surface: "var(--ha-card-background, var(--card-background-color, white))",
  text1: "var(--primary-text-color)",
  text2: "var(--secondary-text-color)",
  bg2: "var(--card-background-color, var(--secondary-background-color))",
  divider: "var(--divider-color)",
  chipBg: "rgba(var(--rgb-primary-text-color, 0,0,0), 0.05)",
  success: "var(--success-color, #4caf50)",
  warning: "var(--warning-color, #ff9800)",
  error: "var(--error-color, #f44336)",
  info: "var(--info-color, #42a5f5)",
  accent: "var(--accent-color, #7c4dff)",
  stateIcon: "var(--state-icon-color, #7c4dff)",
  cme: "#ff6b35",
  flare: "#ffc107",
  storm: "#ab47bc",
  neo: "var(--info-color, #42a5f5)",
};

const BASE_STYLES = `
  :host {
    display: block;
    contain: content;
    --astro-spacing: 12px;
    --astro-icon-size: 20px;
  }
  .astro-card {
    background: ${ASTRO.surface};
    border-radius: ${ASTRO.radius};
    box-shadow: ${ASTRO.shadow};
    overflow: hidden;
  }
  .astro-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 12px 0;
    margin-bottom: var(--astro-spacing);
  }
  .astro-header ha-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px; height: 36px;
    border-radius: 50%;
    background: rgba(var(--rgb-state-icon-color, 124,77,255), 0.1);
    color: ${ASTRO.stateIcon};
    --mdc-icon-size: var(--astro-icon-size);
  }
  .astro-title {
    font-size: 0.9rem;
    font-weight: 500;
    letter-spacing: 0.01em;
    color: ${ASTRO.text1};
    flex: 1;
  }
  .astro-badge {
    background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.06);
    color: ${ASTRO.text2};
    padding: 4px 10px;
    border-radius: 16px;
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.02em;
  }
  .astro-badge.warn {
    background: rgba(var(--rgb-warning-color, 255,152,0), 0.12);
    color: ${ASTRO.warning};
  }
  .astro-badge.danger {
    background: rgba(var(--rgb-error-color, 244,67,54), 0.12);
    color: ${ASTRO.error};
  }
  .astro-stat-grid {
    display: grid;
    gap: 8px;
    padding: 0 12px;
    margin-bottom: var(--astro-spacing);
  }
  .astro-stat-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
  .astro-stat-grid.cols-4 { grid-template-columns: repeat(4, 1fr); }
  .astro-stat {
    background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
    border-radius: var(--ha-card-border-radius, 12px);
    padding: 12px 8px;
    text-align: center;
  }
  .astro-stat-value {
    font-size: 1.1rem;
    font-weight: 600;
    color: ${ASTRO.text1};
  }
  .astro-stat-label {
    font-size: 0.68rem;
    color: ${ASTRO.text2};
    margin-top: 4px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    font-weight: 500;
  }
`;

const EDITOR_STYLES = `
  :host { display: block; }
  .editor {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .editor-section {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .editor-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--secondary-text-color);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .editor ha-entity-picker,
  .editor ha-textfield,
  .editor .native-select,
  .editor .astro-input-wrap {
    display: block;
    width: 100%;
  }
  .editor label.switch-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
    color: var(--primary-text-color);
    font-size: 0.9rem;
  }
  .editor-grid {
    display: grid;
    gap: 12px;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  }
  .native-select {
    box-sizing: border-box;
    width: 100%;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid var(--divider-color);
    background: var(--card-background-color, var(--secondary-background-color));
    color: var(--primary-text-color);
    font: inherit;
    outline: none;
  }
  .astro-input-wrap {
    position: relative;
  }
  .astro-input-wrap label {
    display: block;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--secondary-text-color);
    margin-bottom: 4px;
  }
  .astro-input-wrap input {
    box-sizing: border-box;
    width: 100%;
    padding: 12px;
    border-radius: 12px;
    border: 1px solid var(--divider-color);
    background: var(--card-background-color, var(--secondary-background-color));
    color: var(--primary-text-color);
    font: inherit;
    font-size: 0.95rem;
    outline: none;
    transition: border-color 0.2s;
  }
  .astro-input-wrap input:focus {
    border-color: var(--primary-color);
  }
`;

const DOCS_URL = "https://github.com/snfx-johaver/home-assistant-astronomy-suite";
const VERSION = "1.7.0";
const DAY_MS = 86400000;
const J2000 = 2451545.0;

const MOON_PHASE_ORDER = [
  "new_moon",
  "waxing_crescent",
  "first_quarter",
  "waxing_gibbous",
  "full_moon",
  "waning_gibbous",
  "last_quarter",
  "waning_crescent",
];

const MOON_ICONS = {
  new_moon: "🌑",
  waxing_crescent: "🌒",
  first_quarter: "🌓",
  waxing_gibbous: "🌔",
  full_moon: "🌕",
  waning_gibbous: "🌖",
  last_quarter: "🌗",
  waning_crescent: "🌘",
};

const PLANET_ELEMENTS = {
  Mercury: { a: 0.387, e: 0.2056, L: 252.25, wBar: 77.46, daily: 4.0923, color: "#ff80ab" },
  Venus: { a: 0.723, e: 0.0068, L: 181.98, wBar: 131.53, daily: 1.6021, color: "#ba68c8" },
  Earth: { a: 1.0, e: 0.0167, L: 100.47, wBar: 102.94, daily: 0.9856, color: "#4dd0e1" },
  Mars: { a: 1.524, e: 0.0934, L: 355.45, wBar: 336.04, daily: 0.524, color: "#ef5350" },
  Jupiter: { a: 5.203, e: 0.0484, L: 34.4, wBar: 14.33, daily: 0.0831, color: "#ffb74d" },
  Saturn: { a: 9.537, e: 0.0542, L: 49.94, wBar: 92.43, daily: 0.0335, color: "#ffe082" },
};

function esc(str) {
  const d = document.createElement("div");
  d.textContent = str == null ? "" : String(str);
  return d.innerHTML;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function toNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function parseDate(value) {
  if (!value) return null;
  const date = value instanceof Date ? value : new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatDate(dateLike) {
  const date = parseDate(dateLike);
  if (!date) return "Unknown";
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function formatTime(dateLike) {
  const date = parseDate(dateLike);
  if (!date) return "--:--";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDateTime(dateLike) {
  const date = parseDate(dateLike);
  if (!date) return "Unknown";
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDistanceKm(km) {
  const value = toNumber(km, NaN);
  if (!Number.isFinite(value) || value <= 0) return "—";
  if (value >= 1000000) return `${(value / 1000000).toFixed(2)}M km`;
  if (value >= 1000) return `${(value / 1000).toFixed(0)}K km`;
  return `${value.toFixed(0)} km`;
}

function formatSpeedKmh(kmh) {
  const value = toNumber(kmh, NaN);
  if (!Number.isFinite(value) || value <= 0) return "—";
  if (value >= 1000000) return `${(value / 1000000).toFixed(2)}M km/h`;
  return `${(value / 1000).toFixed(0)}K km/h`;
}

function formatMeters(value) {
  const number = toNumber(value, NaN);
  if (!Number.isFinite(number) || number <= 0) return "—";
  if (number >= 1000) return `${(number / 1000).toFixed(2)} km`;
  return `${number.toFixed(0)} m`;
}

function formatCountdown(targetDate) {
  const date = parseDate(targetDate);
  if (!date) return "";
  const diff = date.getTime() - Date.now();
  if (diff <= -30 * 60 * 1000) return "Launched";
  if (diff <= 0) return "Live now";
  const totalMinutes = Math.floor(diff / 60000);
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;
  if (days > 0) return `T-${days}d ${hours}h`;
  if (hours > 0) return `T-${hours}h ${minutes}m`;
  return `T-${minutes}m`;
}

function isWithinHours(targetDate, hours) {
  const date = parseDate(targetDate);
  if (!date) return false;
  const diff = date.getTime() - Date.now();
  return diff >= 0 && diff <= hours * 60 * 60 * 1000;
}

function getState(hass, entityId) {
  return hass && entityId ? hass.states[entityId] : undefined;
}

function renderErrorCard(message, icon = "mdi:alert-circle-outline") {
  return `
    <style>
      ${BASE_STYLES}
      .astro-error { padding: 20px 16px 16px; color: ${ASTRO.text2}; text-align: center; }
      .astro-error ha-icon { color: ${ASTRO.warning}; --mdc-icon-size: 28px; margin-bottom: 8px; }
      .astro-error div:last-child { font-size: 0.85rem; line-height: 1.4; }
    </style>
    <ha-card class="astro-card">
      <div class="astro-error">
        <ha-icon icon="${icon}"></ha-icon>
        <div>${esc(message)}</div>
      </div>
    </ha-card>
  `;
}

function dispatchConfigChanged(editor) {
  editor.dispatchEvent(new CustomEvent("config-changed", {
    detail: { config: { ...editor._config } },
    bubbles: true,
    composed: true,
  }));
}

function setPickerValue(root, id, hass, value) {
  const picker = root.getElementById(id);
  if (!picker) return;
  picker.hass = hass;
  picker.value = value || "";
}

function setTextValue(root, id, value) {
  const field = root.getElementById(id);
  if (field) field.value = value == null ? "" : String(value);
}

function setSwitchValue(root, id, checked) {
  const sw = root.getElementById(id);
  if (sw) sw.checked = Boolean(checked);
}

function setSelectValue(root, id, value) {
  const select = root.getElementById(id);
  if (select) select.value = String(value);
}

function normalizePhase(phase) {
  return String(phase || "unknown").toLowerCase().replace(/\s+/g, "_");
}

function getMoonPhaseData(phase) {
  const normalized = normalizePhase(phase);
  return {
    new_moon: { name: "New moon", illumination: 0, fraction: 0, waxing: true },
    waxing_crescent: { name: "Waxing crescent", illumination: 25, fraction: 0.25, waxing: true },
    first_quarter: { name: "First quarter", illumination: 50, fraction: 0.5, waxing: true },
    waxing_gibbous: { name: "Waxing gibbous", illumination: 75, fraction: 0.75, waxing: true },
    full_moon: { name: "Full moon", illumination: 100, fraction: 1, waxing: false },
    waning_gibbous: { name: "Waning gibbous", illumination: 75, fraction: 0.75, waxing: false },
    last_quarter: { name: "Last quarter", illumination: 50, fraction: 0.5, waxing: false },
    waning_crescent: { name: "Waning crescent", illumination: 25, fraction: 0.25, waxing: false },
  }[normalized] || { name: "Unknown", illumination: 0, fraction: 0, waxing: true };
}

function renderMoonSvg(fraction, waxing, size) {
  const r = size / 2 - 5;
  const cx = size / 2;
  const cy = size / 2;
  let shadowPath = "";

  if (fraction <= 0.01) {
    shadowPath = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="rgba(10,10,20,0.94)" />`;
  } else if (fraction < 0.99) {
    const sweep = Math.max(r * 0.08, Math.abs((fraction < 0.5 ? 1 - 2 * fraction : 2 * fraction - 1) * r));
    const largeArc = fraction >= 0.5 ? 1 : 0;
    if (waxing) {
      shadowPath = `<path d="M ${cx} ${cy - r} A ${r} ${r} 0 0 0 ${cx} ${cy + r} A ${sweep} ${r} 0 0 ${largeArc} ${cx} ${cy - r} Z" fill="rgba(10,10,20,0.92)" />`;
    } else {
      shadowPath = `<path d="M ${cx} ${cy - r} A ${r} ${r} 0 0 1 ${cx} ${cy + r} A ${sweep} ${r} 0 0 ${largeArc ? 0 : 1} ${cx} ${cy - r} Z" fill="rgba(10,10,20,0.92)" />`;
    }
  }

  return `
    <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" aria-hidden="true">
      <defs>
        <radialGradient id="moon-surface" cx="38%" cy="38%">
          <stop offset="0%" stop-color="#f6f3e8"></stop>
          <stop offset="55%" stop-color="#d6d0c0"></stop>
          <stop offset="100%" stop-color="#a39a86"></stop>
        </radialGradient>
      </defs>
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="url(#moon-surface)"></circle>
      <circle cx="${cx - r * 0.2}" cy="${cy - r * 0.1}" r="${r * 0.12}" fill="rgba(130,120,100,0.26)"></circle>
      <circle cx="${cx + r * 0.24}" cy="${cy + r * 0.28}" r="${r * 0.09}" fill="rgba(130,120,100,0.22)"></circle>
      <circle cx="${cx - r * 0.08}" cy="${cy + r * 0.34}" r="${r * 0.15}" fill="rgba(120,110,90,0.18)"></circle>
      <circle cx="${cx + r * 0.34}" cy="${cy - r * 0.26}" r="${r * 0.06}" fill="rgba(120,110,90,0.18)"></circle>
      ${shadowPath}
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(70,60,50,0.28)" stroke-width="2"></circle>
    </svg>
  `;
}

function degToRad(deg) {
  return (deg * Math.PI) / 180;
}

function normalizeAngleDeg(deg) {
  return ((deg % 360) + 360) % 360;
}

function toJulianDay(date) {
  return date.getTime() / DAY_MS + 2440587.5;
}

function solveKepler(meanAnomalyRad, eccentricity) {
  let E = meanAnomalyRad;
  for (let i = 0; i < 8; i += 1) {
    E -= (E - eccentricity * Math.sin(E) - meanAnomalyRad) / (1 - eccentricity * Math.cos(E));
  }
  return E;
}

function calculatePlanetPosition(name, date = new Date()) {
  const planet = PLANET_ELEMENTS[name];
  const days = toJulianDay(date) - J2000;
  const Mdeg = normalizeAngleDeg(planet.L + planet.daily * days - planet.wBar);
  const M = degToRad(Mdeg);
  const E = solveKepler(M, planet.e);
  const trueAnomaly = 2 * Math.atan2(
    Math.sqrt(1 + planet.e) * Math.sin(E / 2),
    Math.sqrt(1 - planet.e) * Math.cos(E / 2),
  );
  const longitude = trueAnomaly + degToRad(planet.wBar);
  const r = planet.a * (1 - planet.e * Math.cos(E));
  return {
    name,
    color: planet.color,
    r,
    x: r * Math.cos(longitude),
    y: r * Math.sin(longitude),
  };
}

function buildOrbitPath(name, scale, center, samples = 180) {
  const planet = PLANET_ELEMENTS[name];
  const wBar = degToRad(planet.wBar);
  const points = [];
  for (let i = 0; i <= samples; i += 1) {
    const trueAnomaly = (Math.PI * 2 * i) / samples;
    const radius = (planet.a * (1 - planet.e * planet.e)) / (1 + planet.e * Math.cos(trueAnomaly));
    const angle = trueAnomaly + wBar;
    const x = center + radius * Math.cos(angle) * scale;
    const y = center + radius * Math.sin(angle) * scale;
    points.push(`${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`);
  }
  return `${points.join(" ")} Z`;
}

function buildStarFieldSvg(width, height, count, seed = 42) {
  let state = seed;
  const stars = [];
  for (let i = 0; i < count; i += 1) {
    state = (1664525 * state + 1013904223) % 4294967296;
    const x = ((state / 4294967296) * width).toFixed(2);
    state = (1664525 * state + 1013904223) % 4294967296;
    const y = ((state / 4294967296) * height).toFixed(2);
    state = (1664525 * state + 1013904223) % 4294967296;
    const r = (0.4 + (state / 4294967296) * 1.6).toFixed(2);
    const opacity = (0.2 + (state / 4294967296) * 0.7).toFixed(2);
    stars.push(`<circle cx="${x}" cy="${y}" r="${r}" fill="rgba(255,255,255,${opacity})"></circle>`);
  }
  return stars.join("");
}

class AstroEditorBase extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._rendered = false;
  }

  setConfig(config) {
    this._config = { ...config };
    if (this._rendered) this._updateValues();
    else this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._rendered) this._updateValues();
    else this._render();
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>${EDITOR_STYLES}</style>
      <div class="editor">${this._editorTemplate()}</div>
    `;
    this._rendered = true;
    this._setupListeners();
    this._updateValues();
  }

  _updateValues() {
    this.shadowRoot.querySelectorAll("ha-entity-picker").forEach((picker) => {
      picker.hass = this._hass;
    });
    this._syncValues();
  }

  _setValue(key, value) {
    this._config = { ...this._config, [key]: value };
    dispatchConfigChanged(this);
  }

  _bindPicker(id, key) {
    const field = this.shadowRoot.getElementById(id);
    if (!field) return;
    field.addEventListener("value-changed", (event) => {
      this._setValue(key, event.detail.value);
    });
  }

  _bindText(id, key, transform = (value) => value) {
    const field = this.shadowRoot.getElementById(id);
    if (!field) return;
    field.addEventListener("input", (event) => {
      this._setValue(key, transform(event.target.value));
    });
    field.addEventListener("change", (event) => {
      this._setValue(key, transform(event.target.value));
    });
  }

  _bindSwitch(id, key) {
    const field = this.shadowRoot.getElementById(id);
    if (!field) return;
    field.addEventListener("change", (event) => {
      this._setValue(key, event.target.checked);
    });
  }

  _bindSelect(id, key, transform = (value) => value) {
    const field = this.shadowRoot.getElementById(id);
    if (!field) return;
    field.addEventListener("change", (event) => {
      this._setValue(key, transform(event.target.value));
    });
  }

  _editorTemplate() { return ""; }
  _setupListeners() {}
  _syncValues() {}
}

class ApodCardEditor extends AstroEditorBase {
  setConfig(config) {
    super.setConfig({
      entity: "sensor.nasa_astronomy_suite_apod",
      show_explanation: true,
      show_copyright: true,
      show_hd_link: false,
      show_date: true,
      title: "",
      image_height: 400,
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <ha-entity-picker id="entity" label="APOD entity"></ha-entity-picker>
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <div class="astro-input-wrap"><label for="image_height">Image height (px)</label><input type="number" id="image_height" min="160" max="1200" /></div>
      <label class="switch-row"><span>Show explanation</span><ha-switch id="show_explanation"></ha-switch></label>
      <label class="switch-row"><span>Show copyright</span><ha-switch id="show_copyright"></ha-switch></label>
      <label class="switch-row"><span>Show HD link</span><ha-switch id="show_hd_link"></ha-switch></label>
      <label class="switch-row"><span>Show date</span><ha-switch id="show_date"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindPicker("entity", "entity");
    this._bindText("title", "title", (value) => value.trim());
    this._bindText("image_height", "image_height", (value) => clamp(parseInt(value, 10) || 400, 160, 1200));
    ["show_explanation", "show_copyright", "show_hd_link", "show_date"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setPickerValue(this.shadowRoot, "entity", this._hass, this._config.entity);
    setTextValue(this.shadowRoot, "title", this._config.title || "");
    setTextValue(this.shadowRoot, "image_height", this._config.image_height || 400);
    setSwitchValue(this.shadowRoot, "show_explanation", this._config.show_explanation !== false);
    setSwitchValue(this.shadowRoot, "show_copyright", this._config.show_copyright !== false);
    setSwitchValue(this.shadowRoot, "show_hd_link", this._config.show_hd_link === true);
    setSwitchValue(this.shadowRoot, "show_date", this._config.show_date !== false);
  }
}

class ApodCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._lastStateHash = "";
  }

  static getConfigElement() { return document.createElement("apod-card-editor"); }
  static getStubConfig() {
    return {
      entity: "sensor.nasa_astronomy_suite_apod",
      show_explanation: true,
      show_copyright: true,
      show_hd_link: false,
      show_date: true,
      title: "",
      image_height: 400,
    };
  }

  setConfig(config) {
    if (!config.entity) throw new Error("You must define an entity");
    this._config = { ...ApodCard.getStubConfig(), ...config };
    this._lastStateHash = "";
  }

  set hass(hass) {
    this._hass = hass;
    const stateObj = hass.states[this._config.entity];
    const hash = stateObj ? `${stateObj.state}|${stateObj.last_updated}` : "";
    if (hash !== this._lastStateHash) {
      this._lastStateHash = hash;
      this._render();
    }
  }

  _render() {
    if (!this._hass) return;
    const stateObj = getState(this._hass, this._config.entity);
    if (!stateObj) {
      const cached = this._getCachedApod();
      if (cached) {
        this._renderApod(cached);
        return;
      }
      this.shadowRoot.innerHTML = renderErrorCard(`Entity not found: ${this._config.entity}`);
      return;
    }

    // If state is unavailable/unknown, try cache first, then show loading
    if (["unknown", "unavailable"].includes(String(stateObj.state).toLowerCase())) {
      const cached = this._getCachedApod();
      if (cached) {
        this._renderApod(cached);
        return;
      }
      this.shadowRoot.innerHTML = renderErrorCard(`APOD data loading... (${this._config.entity})`);
      return;
    }

    const attrs = stateObj.attributes || {};
    const data = {
      cardTitle: this._config.title || "Astronomy Picture of the Day",
      mediaTitle: attrs.title || stateObj.state || "APOD",
      explanation: attrs.explanation || "",
      url: attrs.url || "",
      hdurl: attrs.hdurl || "",
      date: attrs.date || "",
      mediaType: attrs.media_type || "image",
      copyright: attrs.copyright || "",
    };

    // Cache successful data
    if (data.url) {
      try { localStorage.setItem("astro_apod_cache", JSON.stringify(data)); } catch (e) { /* ignore */ }
    }

    this._renderApod(data);
  }

  _getCachedApod() {
    try {
      const raw = localStorage.getItem("astro_apod_cache");
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }

  _renderApod(data) {
    const { cardTitle, mediaTitle, explanation, url, hdurl, date, mediaType, copyright } = data;
    const imageHeight = clamp(parseInt(this._config.image_height, 10) || 400, 160, 1200);

    const mediaHtml = mediaType === "video"
      ? `
        <div class="apod-video" style="height:${imageHeight}px;">
          <iframe src="${esc(url)}" title="${esc(mediaTitle)}" loading="lazy" allowfullscreen></iframe>
        </div>
      `
      : `
        <div class="apod-media" style="height:${imageHeight}px;">
          <img src="${esc(url)}" alt="${esc(mediaTitle)}" loading="lazy" />
          <div class="apod-overlay">
            <div class="apod-media-title">${esc(mediaTitle)}</div>
            ${this._config.show_date !== false && date ? `<div class="apod-media-date">${esc(date)}</div>` : ""}
          </div>
        </div>
      `;

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .apod-scene { position: relative; }
        .apod-media,
        .apod-video {
          position: relative;
          width: 100%;
          overflow: hidden;
          background: #000;
        }
        .apod-media img,
        .apod-video iframe {
          width: 100%;
          height: 100%;
          display: block;
          border: 0;
          object-fit: cover;
        }
        .apod-overlay {
          position: absolute;
          inset: auto 0 0 0;
          padding: 56px 16px 16px;
          background: linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.85) 100%);
          color: white;
        }
        .apod-media-title { font-size: 1rem; font-weight: 600; line-height: 1.35; }
        .apod-media-date { margin-top: 4px; font-size: 0.78rem; opacity: 0.82; }
        .apod-content { padding: 0 12px 14px; display: flex; flex-direction: column; gap: 12px; }
        .apod-explanation {
          font-size: 0.84rem;
          line-height: 1.55;
          color: ${ASTRO.text2};
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
          border-radius: 12px;
          padding: 12px;
        }
        .apod-meta,
        .apod-links {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .apod-pill {
          padding: 6px 10px;
          border-radius: 999px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.05);
          color: ${ASTRO.text2};
          font-size: 0.75rem;
        }
        .apod-button {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          text-decoration: none;
          color: ${ASTRO.accent};
          background: rgba(var(--rgb-accent-color, 124,77,255), 0.1);
          padding: 8px 12px;
          border-radius: 999px;
          font-size: 0.8rem;
          font-weight: 600;
        }
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:image-outline"></ha-icon>
          <span class="astro-title">${esc(cardTitle)}</span>
          <span class="astro-badge">NASA APOD</span>
        </div>
        <div class="apod-scene">${mediaHtml}</div>
        <div class="apod-content">
          ${this._config.show_explanation !== false && explanation ? `<div class="apod-explanation">${esc(explanation)}</div>` : ""}
          <div class="apod-meta">
            ${this._config.show_date !== false && date ? `<span class="apod-pill">${esc(date)}</span>` : ""}
            ${this._config.show_copyright !== false && copyright ? `<span class="apod-pill">© ${esc(copyright)}</span>` : ""}
            <span class="apod-pill">${esc(mediaType)}</span>
          </div>
          ${this._config.show_hd_link && hdurl ? `<div class="apod-links"><a class="apod-button" href="${esc(hdurl)}" target="_blank" rel="noopener">View HD image ↗</a></div>` : ""}
        </div>
      </ha-card>
    `;
  }

  getCardSize() { return 6; }
}

class NeoThreatCardEditor extends AstroEditorBase {
  setConfig(config) {
    super.setConfig({
      entity: "sensor.nasa_astronomy_suite_neo_count_today",
      largest_entity: "sensor.nasa_astronomy_suite_largest_neo",
      max_items: 5,
      show_hazardous_only: false,
      show_stats: true,
      title: "",
      show_velocity: true,
      show_diameter: true,
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <ha-entity-picker id="entity" label="NEO count entity"></ha-entity-picker>
      <ha-entity-picker id="largest_entity" label="Largest NEO entity"></ha-entity-picker>
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <div class="astro-input-wrap"><label for="max_items">Max items shown</label><input type="number" id="max_items" min="1" max="20" /></div>
      <label class="switch-row"><span>Show hazardous only</span><ha-switch id="show_hazardous_only"></ha-switch></label>
      <label class="switch-row"><span>Show statistics</span><ha-switch id="show_stats"></ha-switch></label>
      <label class="switch-row"><span>Show velocity</span><ha-switch id="show_velocity"></ha-switch></label>
      <label class="switch-row"><span>Show diameter</span><ha-switch id="show_diameter"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindPicker("entity", "entity");
    this._bindPicker("largest_entity", "largest_entity");
    this._bindText("title", "title", (value) => value.trim());
    this._bindText("max_items", "max_items", (value) => clamp(parseInt(value, 10) || 5, 1, 20));
    ["show_hazardous_only", "show_stats", "show_velocity", "show_diameter"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setPickerValue(this.shadowRoot, "entity", this._hass, this._config.entity);
    setPickerValue(this.shadowRoot, "largest_entity", this._hass, this._config.largest_entity || "");
    setTextValue(this.shadowRoot, "title", this._config.title || "");
    setTextValue(this.shadowRoot, "max_items", this._config.max_items || 5);
    setSwitchValue(this.shadowRoot, "show_hazardous_only", this._config.show_hazardous_only === true);
    setSwitchValue(this.shadowRoot, "show_stats", this._config.show_stats !== false);
    setSwitchValue(this.shadowRoot, "show_velocity", this._config.show_velocity !== false);
    setSwitchValue(this.shadowRoot, "show_diameter", this._config.show_diameter !== false);
  }
}

class NeoThreatCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  static getConfigElement() { return document.createElement("neo-threat-card-editor"); }
  static getStubConfig() {
    return {
      entity: "sensor.nasa_astronomy_suite_neo_count_today",
      largest_entity: "sensor.nasa_astronomy_suite_largest_neo",
      max_items: 5,
      show_hazardous_only: false,
      show_stats: true,
      title: "",
      show_velocity: true,
      show_diameter: true,
    };
  }

  setConfig(config) {
    if (!config.entity) throw new Error("You must define an entity");
    this._config = { ...NeoThreatCard.getStubConfig(), ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) return;
    const stateObj = getState(this._hass, this._config.entity);
    if (!stateObj) {
      this.shadowRoot.innerHTML = renderErrorCard(`Entity not found: ${this._config.entity}`);
      return;
    }

    const attrs = stateObj.attributes || {};
    let neoList = safeArray(attrs.neo_list).map((item) => ({ ...item }));
    if (this._config.show_hazardous_only) neoList = neoList.filter((item) => item.hazardous);

    const sorted = [...neoList].sort((a, b) => toNumber(a.miss_distance_km, Infinity) - toNumber(b.miss_distance_km, Infinity));
    const displayed = sorted.slice(0, clamp(parseInt(this._config.max_items, 10) || 5, 1, 20));
    const hazardousCount = sorted.filter((item) => item.hazardous).length || toNumber(attrs.hazardous_count, 0);
    const totalCount = sorted.length || toNumber(attrs.total_count, 0);
    const closest = sorted[0];
    const fastest = [...sorted].sort((a, b) => toNumber(b.velocity_kmh, 0) - toNumber(a.velocity_kmh, 0))[0];
    const title = this._config.title || "Near-Earth Objects";

    // Largest NEO
    const largestState = this._config.largest_entity ? getState(this._hass, this._config.largest_entity) : null;
    const largestName = largestState ? (largestState.state || largestState.attributes?.name || "—") : "—";

    const listHtml = displayed.length
      ? displayed.map((neo) => {
          const detail = [];
          if (this._config.show_diameter !== false) detail.push(`⌀ ${formatMeters(neo.diameter_max_m || neo.diameter_min_m)}`);
          if (this._config.show_velocity !== false) detail.push(formatSpeedKmh(neo.velocity_kmh));
          if (neo.close_approach_date) detail.push(formatDateTime(neo.close_approach_date));
          return `
            <div class="neo-item ${neo.hazardous ? "danger" : ""}">
              <div class="neo-dot ${neo.hazardous ? "danger" : "safe"}"></div>
              <div class="neo-copy">
                <div class="neo-name">${esc(neo.name || "Unnamed object")}</div>
                <div class="neo-detail">${esc(detail.join(" · "))}</div>
              </div>
              <div class="neo-distance">${formatDistanceKm(neo.miss_distance_km)}</div>
            </div>
          `;
        }).join("")
      : `<div class="neo-empty">No NEO objects available for the current filter.</div>`;

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .neo-list { display: flex; flex-direction: column; gap: 8px; padding: 0 12px 14px; }
        .neo-item {
          display: grid;
          grid-template-columns: auto 1fr auto;
          gap: 10px;
          align-items: center;
          padding: 12px;
          border-radius: 14px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
        }
        .neo-item.danger { box-shadow: inset 0 0 0 1px rgba(var(--rgb-error-color, 244,67,54), 0.18); }
        .neo-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: ${ASTRO.success};
        }
        .neo-dot.danger {
          background: ${ASTRO.error};
          box-shadow: 0 0 0 6px rgba(var(--rgb-error-color, 244,67,54), 0.12);
        }
        .neo-copy { min-width: 0; }
        .neo-name {
          font-size: 0.84rem;
          font-weight: 600;
          color: ${ASTRO.text1};
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .neo-detail { font-size: 0.73rem; color: ${ASTRO.text2}; margin-top: 3px; }
        .neo-distance { font-size: 0.8rem; font-weight: 600; color: ${ASTRO.text1}; text-align: right; }
        .neo-empty {
          padding: 0 12px 16px;
          color: ${ASTRO.text2};
          font-size: 0.84rem;
        }
        .neo-stat-icon { margin-bottom: 4px; }
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:meteor"></ha-icon>
          <span class="astro-title">${esc(title)}</span>
          <span class="astro-badge ${hazardousCount > 0 ? "danger" : ""}">${hazardousCount > 0 ? `${hazardousCount} hazardous` : `${totalCount} tracked`}</span>
        </div>
        ${this._config.show_stats !== false ? `
          <div class="astro-stat-grid cols-4">
            <div class="astro-stat"><div class="neo-stat-icon"><ha-icon icon="mdi:counter" style="color:#9e9e9e;--mdc-icon-size:20px;"></ha-icon></div><div class="astro-stat-value">${totalCount}</div><div class="astro-stat-label">Number</div></div>
            <div class="astro-stat"><div class="neo-stat-icon"><ha-icon icon="mdi:resize" style="color:#42a5f5;--mdc-icon-size:20px;"></ha-icon></div><div class="astro-stat-value">${esc(largestName)}</div><div class="astro-stat-label">Largest</div></div>
            <div class="astro-stat"><div class="neo-stat-icon"><ha-icon icon="mdi:speedometer" style="color:#ff9800;--mdc-icon-size:20px;"></ha-icon></div><div class="astro-stat-value">${fastest ? formatSpeedKmh(fastest.velocity_kmh) : "—"}</div><div class="astro-stat-label">Fastest</div></div>
            <div class="astro-stat"><div class="neo-stat-icon"><ha-icon icon="mdi:bullseye-arrow" style="color:#ef5350;--mdc-icon-size:20px;"></ha-icon></div><div class="astro-stat-value">${closest ? formatDistanceKm(closest.miss_distance_km) : "—"}</div><div class="astro-stat-label">Closest</div></div>
          </div>
        ` : ""}
        <div class="neo-list">${listHtml}</div>
      </ha-card>
    `;
  }

  getCardSize() { return 5; }
}

class SolarActivityCardEditor extends AstroEditorBase {
  setConfig(config) {
    super.setConfig({
      cme_entity: "sensor.nasa_astronomy_suite_coronal_mass_ejections",
      flare_entity: "sensor.nasa_astronomy_suite_solar_flares",
      storm_entity: "sensor.nasa_astronomy_suite_geomagnetic_storms",
      kp_entity: "sensor.nasa_astronomy_suite_planetary_kp_index",
      sdo_entity: "",
      soho_entity: "",
      title: "",
      show_cme: true,
      show_flares: true,
      show_storms: true,
      show_kp_gauge: true,
      show_live_sun: true,
      show_sdo: true,
      show_soho: true,
      time_range: 7,
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <ha-entity-picker id="cme_entity" label="CME entity"></ha-entity-picker>
      <ha-entity-picker id="flare_entity" label="Solar flare entity"></ha-entity-picker>
      <ha-entity-picker id="storm_entity" label="Geomagnetic storm entity"></ha-entity-picker>
      <ha-entity-picker id="kp_entity" label="Planetary KP entity"></ha-entity-picker>
      <ha-entity-picker id="sdo_entity" label="SDO sun camera entity"></ha-entity-picker>
      <ha-entity-picker id="soho_entity" label="SOHO sun camera entity"></ha-entity-picker>
      <label class="switch-row"><span>Show CMEs</span><ha-switch id="show_cme"></ha-switch></label>
      <label class="switch-row"><span>Show flares</span><ha-switch id="show_flares"></ha-switch></label>
      <label class="switch-row"><span>Show storms</span><ha-switch id="show_storms"></ha-switch></label>
      <label class="switch-row"><span>Show KP gauge</span><ha-switch id="show_kp_gauge"></ha-switch></label>
      <label class="switch-row"><span>Show live sun section</span><ha-switch id="show_live_sun"></ha-switch></label>
      <label class="switch-row"><span>Show SDO</span><ha-switch id="show_sdo"></ha-switch></label>
      <label class="switch-row"><span>Show SOHO</span><ha-switch id="show_soho"></ha-switch></label>
      <div class="editor-section">
        <div class="editor-title">Time range</div>
        <select id="time_range" class="native-select">
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
        </select>
      </div>
    `;
  }

  _setupListeners() {
    ["cme_entity", "flare_entity", "storm_entity", "kp_entity", "sdo_entity", "soho_entity"].forEach((key) => this._bindPicker(key, key));
    this._bindText("title", "title", (value) => value.trim());
    ["show_cme", "show_flares", "show_storms", "show_kp_gauge", "show_live_sun", "show_sdo", "show_soho"].forEach((key) => this._bindSwitch(key, key));
    this._bindSelect("time_range", "time_range", (value) => (String(value) === "30" ? 30 : 7));
  }

  _syncValues() {
    ["cme_entity", "flare_entity", "storm_entity", "kp_entity", "sdo_entity", "soho_entity"].forEach((key) => setPickerValue(this.shadowRoot, key, this._hass, this._config[key]));
    setTextValue(this.shadowRoot, "title", this._config.title || "");
    setSwitchValue(this.shadowRoot, "show_cme", this._config.show_cme !== false);
    setSwitchValue(this.shadowRoot, "show_flares", this._config.show_flares !== false);
    setSwitchValue(this.shadowRoot, "show_storms", this._config.show_storms !== false);
    setSwitchValue(this.shadowRoot, "show_kp_gauge", this._config.show_kp_gauge !== false);
    setSwitchValue(this.shadowRoot, "show_live_sun", this._config.show_live_sun !== false);
    setSwitchValue(this.shadowRoot, "show_sdo", this._config.show_sdo !== false);
    setSwitchValue(this.shadowRoot, "show_soho", this._config.show_soho !== false);
    setSelectValue(this.shadowRoot, "time_range", this._config.time_range || 7);
  }
}

class SolarActivityCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._lastStateHash = "";
  }

  static getConfigElement() { return document.createElement("solar-activity-card-editor"); }
  static getStubConfig() {
    return {
      cme_entity: "sensor.nasa_astronomy_suite_coronal_mass_ejections",
      flare_entity: "sensor.nasa_astronomy_suite_solar_flares",
      storm_entity: "sensor.nasa_astronomy_suite_geomagnetic_storms",
      kp_entity: "sensor.nasa_astronomy_suite_planetary_kp_index",
      sdo_entity: "",
      soho_entity: "",
      title: "",
      show_cme: true,
      show_flares: true,
      show_storms: true,
      show_kp_gauge: true,
      show_live_sun: true,
      show_sdo: true,
      show_soho: true,
      time_range: 7,
    };
  }

  setConfig(config) {
    if (!config.cme_entity || !config.flare_entity || !config.storm_entity) {
      throw new Error("You must define cme_entity, flare_entity, and storm_entity");
    }
    this._config = { ...SolarActivityCard.getStubConfig(), ...config };
    this._lastStateHash = "";
  }

  set hass(hass) {
    this._hass = hass;
    const hash = this._computeStateHash();
    if (hash !== this._lastStateHash) {
      this._lastStateHash = hash;
      this._render();
    }
  }

  _computeStateHash() {
    if (!this._hass) return "";
    const entities = [this._config.cme_entity, this._config.flare_entity, this._config.storm_entity, this._config.kp_entity];
    return entities.map((e) => {
      const s = e ? this._hass.states[e] : null;
      return s ? `${s.state}|${s.last_updated}` : "";
    }).join(";");
  }

  _collectEvents(stateObj, kind, timeRange) {
    const now = Date.now();
    return safeArray(stateObj?.attributes?.events)
      .map((event) => {
        const stamp = event.start_time || event.begin_time || event.peak_time || event.end_time;
        const date = parseDate(stamp);
        const ageDays = date ? (now - date.getTime()) / DAY_MS : Infinity;
        const label = kind === "cme"
          ? "Coronal mass ejection"
          : kind === "flare"
            ? `Solar flare${event.class_type ? ` (${event.class_type})` : ""}`
            : `Geomagnetic storm${event.kp_index != null ? ` (Kp ${event.kp_index})` : ""}`;
        return {
          kind,
          label,
          stamp,
          date,
          ageDays,
          meta: kind === "flare"
            ? event.class_type || ""
            : kind === "storm"
              ? event.kp_index != null ? `Kp ${event.kp_index}` : ""
              : event.note || "",
        };
      })
      .filter((event) => event.date && event.ageDays <= timeRange)
      .sort((a, b) => b.date - a.date);
  }

  _getKpDetails(stateObj) {
    if (!stateObj || ["unknown", "unavailable"].includes(String(stateObj.state).toLowerCase())) return null;
    const value = toNumber(stateObj.state, NaN);
    if (!Number.isFinite(value)) return null;
    const normalized = clamp(value, 0, 9);
    const attrs = stateObj.attributes || {};
    const band = normalized >= 8
      ? { color: ASTRO.error, label: "Severe" }
      : normalized >= 6
        ? { color: ASTRO.warning, label: "Storm" }
        : normalized >= 4
          ? { color: "#fdd835", label: "Active" }
          : { color: ASTRO.success, label: "Quiet" };
    return {
      value: normalized,
      color: band.color,
      auroraLevel: attrs.aurora_level || band.label,
      percent: clamp((normalized / 9) * 100, 0, 100),
    };
  }

  _render() {
    if (!this._hass) return;
    const cmeState = getState(this._hass, this._config.cme_entity);
    const flareState = getState(this._hass, this._config.flare_entity);
    const stormState = getState(this._hass, this._config.storm_entity);
    const kpState = getState(this._hass, this._config.kp_entity);
    const timeRange = this._config.time_range === 30 ? 30 : 7;

    const sections = [
      { enabled: this._config.show_cme !== false, kind: "cme", title: "CMEs", icon: "💥", color: ASTRO.cme, state: cmeState, events: this._collectEvents(cmeState, "cme", timeRange), count: toNumber(cmeState?.state, 0) },
      { enabled: this._config.show_flares !== false, kind: "flare", title: "Flares", icon: "☀️", color: ASTRO.flare, state: flareState, events: this._collectEvents(flareState, "flare", timeRange), count: toNumber(flareState?.state, 0) },
      { enabled: this._config.show_storms !== false, kind: "storm", title: "Storms", icon: "🌊", color: ASTRO.storm, state: stormState, events: this._collectEvents(stormState, "storm", timeRange), count: toNumber(stormState?.state, 0) },
    ].filter((section) => section.enabled);
    const kpDetails = this._config.show_kp_gauge !== false && this._config.kp_entity ? this._getKpDetails(kpState) : null;
    const sunFeeds = [];
    if (this._config.show_live_sun !== false) {
      if (this._config.show_sdo !== false && this._config.sdo_entity) {
        const sdo = getState(this._hass, this._config.sdo_entity);
        if (sdo) sunFeeds.push({ title: "SDO", entityId: this._config.sdo_entity, stateObj: sdo });
      }
      if (this._config.show_soho !== false && this._config.soho_entity) {
        const soho = getState(this._hass, this._config.soho_entity);
        if (soho) sunFeeds.push({ title: "SOHO", entityId: this._config.soho_entity, stateObj: soho });
      }
    }

    if (!sections.length) {
      this.shadowRoot.innerHTML = renderErrorCard("Enable at least one solar activity feed in the card editor.", "mdi:white-balance-sunny");
      return;
    }

    const total = sections.reduce((sum, section) => sum + section.count, 0);
    const status = total >= 10 ? { label: "Intense activity", className: "danger" } : total >= 3 ? { label: "Elevated activity", className: "warn" } : { label: "Calm conditions", className: "" };
    const timeline = sections.flatMap((section) => section.events.map((event) => ({ ...event, color: section.color }))).sort((a, b) => b.date - a.date).slice(0, 6);

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .solar-grid { display: grid; grid-template-columns: repeat(${Math.min(sections.length, 3)}, 1fr); gap: 8px; padding: 0 12px; margin-bottom: 12px; }
        .solar-metric {
          position: relative;
          border-radius: 14px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
          padding: 14px 10px;
          text-align: center;
          overflow: hidden;
        }
        .solar-metric::before { content: ""; position: absolute; inset: 0 0 auto 0; height: 3px; background: var(--metric-color); }
        .solar-icon { font-size: 1.25rem; margin-bottom: 4px; }
        .solar-value { font-size: 1.45rem; font-weight: 700; color: ${ASTRO.text1}; }
        .solar-label { font-size: 0.7rem; color: ${ASTRO.text2}; margin-top: 2px; text-transform: uppercase; letter-spacing: 0.05em; }
        .kp-panel {
          margin: 0 12px 12px;
          padding: 14px;
          border-radius: 16px;
          background: linear-gradient(180deg, rgba(var(--rgb-primary-text-color, 0,0,0), 0.04), rgba(var(--rgb-primary-text-color, 0,0,0), 0.02));
        }
        .kp-top { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
        .kp-title { font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.06em; color: ${ASTRO.text2}; }
        .kp-value { font-size: 2rem; font-weight: 800; color: ${ASTRO.text1}; line-height: 1; }
        .kp-level { font-size: 0.8rem; font-weight: 600; color: var(--kp-color); }
        .kp-scale { position: relative; margin-top: 12px; }
        .kp-bar {
          height: 10px;
          border-radius: 999px;
          background: linear-gradient(90deg, ${ASTRO.success} 0 33.33%, #fdd835 33.33% 55.55%, ${ASTRO.warning} 55.55% 77.77%, ${ASTRO.error} 77.77% 100%);
        }
        .kp-marker {
          position: absolute;
          top: 50%;
          left: var(--kp-percent);
          width: 16px;
          height: 16px;
          border-radius: 50%;
          transform: translate(-50%, -50%);
          background: var(--kp-color);
          border: 3px solid ${ASTRO.surface};
          box-shadow: 0 0 0 2px rgba(var(--rgb-primary-text-color, 0,0,0), 0.12);
        }
        .kp-ticks { display: flex; justify-content: space-between; margin-top: 8px; font-size: 0.68rem; color: ${ASTRO.text2}; }
        .solar-list { display: flex; flex-direction: column; gap: 8px; padding: 0 12px 14px; }
        .solar-item {
          display: grid;
          grid-template-columns: auto 1fr auto;
          gap: 10px;
          align-items: center;
          border-radius: 14px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
          padding: 10px 12px;
        }
        .solar-dot { width: 10px; height: 10px; border-radius: 50%; }
        .solar-copy { min-width: 0; }
        .solar-item-title { font-size: 0.8rem; font-weight: 600; color: ${ASTRO.text1}; }
        .solar-item-meta { font-size: 0.72rem; color: ${ASTRO.text2}; margin-top: 3px; }
        .solar-item-time { font-size: 0.74rem; color: ${ASTRO.text2}; text-align: right; }
        .live-sun {
          margin: 0 12px 14px;
          padding-top: 12px;
          border-top: 1px solid rgba(var(--rgb-primary-text-color, 0,0,0), 0.08);
        }
        .live-sun-title {
          font-size: 0.78rem;
          font-weight: 700;
          color: ${ASTRO.text1};
          margin-bottom: 8px;
        }
        .live-sun-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; }
        .live-sun-card {
          border-radius: 14px;
          overflow: hidden;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
        }
        .live-sun-card img {
          display: block;
          width: 100%;
          aspect-ratio: 4 / 3;
          object-fit: cover;
          background: #000;
        }
        .live-sun-label {
          padding: 8px 10px 10px;
          font-size: 0.74rem;
          font-weight: 700;
          color: ${ASTRO.text1};
          text-align: center;
        }
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:white-balance-sunny"></ha-icon>
          <span class="astro-title">${esc(this._config.title || "Solar Activity Monitor")}</span>
          <span class="astro-badge ${status.className}">${esc(status.label)}</span>
        </div>
        <div class="solar-grid">
          ${sections.map((section) => `
            <div class="solar-metric" style="--metric-color:${section.color}">
              <div class="solar-icon">${section.icon}</div>
              <div class="solar-value">${section.count}</div>
              <div class="solar-label">${esc(section.title)} · ${timeRange}d</div>
            </div>
          `).join("")}
        </div>
        ${kpDetails ? `
          <div class="kp-panel" style="--kp-color:${kpDetails.color}; --kp-percent:${kpDetails.percent}%">
            <div class="kp-top">
              <div>
                <div class="kp-title">Planetary KP Index</div>
                <div class="kp-value">${kpDetails.value.toFixed(1)}</div>
              </div>
              <div class="kp-level">${esc(kpDetails.auroraLevel)}</div>
            </div>
            <div class="kp-scale">
              <div class="kp-bar"></div>
              <div class="kp-marker"></div>
            </div>
            <div class="kp-ticks"><span>0-3</span><span>4-5</span><span>6-7</span><span>8-9</span></div>
          </div>
        ` : ""}
        <div class="solar-list">
          ${timeline.length
            ? timeline.map((event) => `
              <div class="solar-item">
                <div class="solar-dot" style="background:${event.color}"></div>
                <div class="solar-copy">
                  <div class="solar-item-title">${esc(event.label)}</div>
                  <div class="solar-item-meta">${esc(event.meta || `${timeRange}-day window`)}</div>
                </div>
                <div class="solar-item-time">${esc(formatDateTime(event.stamp))}</div>
              </div>
            `).join("")
            : `<div class="solar-item"><div class="solar-dot" style="background:${ASTRO.info}"></div><div class="solar-copy"><div class="solar-item-title">No recent events</div><div class="solar-item-meta">No solar events recorded in the selected time range.</div></div><div class="solar-item-time">${timeRange}d</div></div>`}
        </div>
        ${sunFeeds.length ? `
          <div class="live-sun">
            <div class="live-sun-title">Live Sun</div>
            <div class="live-sun-grid">
              ${sunFeeds.map((feed) => {
                const token = feed.stateObj.attributes?.access_token || "";
                const imgUrl = `/api/camera_proxy/${feed.entityId}${token ? `?token=${token}` : ""}`;
                return `
                <div class="live-sun-card">
                  <img src="${imgUrl}" alt="${esc(feed.title)} live sun image" loading="lazy" onerror="this.style.opacity='0.3'">
                  <div class="live-sun-label">${esc(feed.title)}</div>
                </div>
              `;}).join("")}
            </div>
          </div>
        ` : ""}
      </ha-card>
    `;
  }

  getCardSize() { return 5; }
}

class AstroHorizonCardEditor extends AstroEditorBase {
  setConfig(config) {
    super.setConfig({
      sun_entity: "sun.sun",
      title: "",
      show_elevation: true,
      show_azimuth: true,
      show_times: true,
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <ha-entity-picker id="sun_entity" label="Sun entity"></ha-entity-picker>
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <label class="switch-row"><span>Show elevation</span><ha-switch id="show_elevation"></ha-switch></label>
      <label class="switch-row"><span>Show azimuth</span><ha-switch id="show_azimuth"></ha-switch></label>
      <label class="switch-row"><span>Show times</span><ha-switch id="show_times"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindPicker("sun_entity", "sun_entity");
    this._bindText("title", "title", (value) => value.trim());
    ["show_elevation", "show_azimuth", "show_times"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setPickerValue(this.shadowRoot, "sun_entity", this._hass, this._config.sun_entity || "sun.sun");
    setTextValue(this.shadowRoot, "title", this._config.title || "");
    setSwitchValue(this.shadowRoot, "show_elevation", this._config.show_elevation !== false);
    setSwitchValue(this.shadowRoot, "show_azimuth", this._config.show_azimuth !== false);
    setSwitchValue(this.shadowRoot, "show_times", this._config.show_times !== false);
  }
}

class AstroHorizonCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  static getConfigElement() { return document.createElement("astro-horizon-card-editor"); }
  static getStubConfig() {
    return {
      sun_entity: "sun.sun",
      title: "",
      show_elevation: true,
      show_azimuth: true,
      show_times: true,
    };
  }

  setConfig(config) {
    this._config = { ...AstroHorizonCard.getStubConfig(), ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) return;
    const sun = getState(this._hass, this._config.sun_entity);
    if (!sun) {
      this.shadowRoot.innerHTML = renderErrorCard(`Sun entity not found: ${this._config.sun_entity}`);
      return;
    }

    const elevation = toNumber(sun.attributes?.elevation, 0);
    const azimuth = toNumber(sun.attributes?.azimuth, 0);
    const rising = Boolean(sun.attributes?.rising);
    const nextRise = sun.attributes?.next_rising;
    const nextSet = sun.attributes?.next_setting;
    const nextNoon = sun.attributes?.next_noon;

    const arcCenterX = 200;
    const arcRadius = 160;
    const baseLineY = 180;
    const sunAngle = Math.PI * (1 - clamp(azimuth / 360, 0, 1));
    const visualRadius = elevation >= 0 ? arcRadius * (1 - clamp(elevation / 90, 0, 1)) : arcRadius + Math.min(Math.abs(elevation), 45);
    const x = arcCenterX + Math.cos(sunAngle) * arcRadius;
    const y = elevation >= 0 ? 20 + visualRadius : baseLineY + Math.min(Math.abs(elevation) * 1.2, 34);
    const skyGradient = elevation > 20
      ? "linear-gradient(180deg, #16385a 0%, #4d8cd7 50%, #9fd6ff 100%)"
      : elevation >= 0
        ? "linear-gradient(180deg, #1b2558 0%, #ff7c4a 40%, #ffd76c 100%)"
        : "linear-gradient(180deg, #090c18 0%, #1f2552 55%, #2e2147 100%)";

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .hz-scene {
          position: relative;
          height: 220px;
          background: ${skyGradient};
          overflow: hidden;
        }
        .hz-svg { position: absolute; inset: 0; width: 100%; height: 100%; }
        .hz-arc { fill: none; stroke: rgba(255,255,255,0.18); stroke-width: 1.5; stroke-dasharray: 4 4; }
        .hz-line { stroke: rgba(255,255,255,0.25); stroke-width: 1; stroke-dasharray: 4 4; }
        .hz-ground { fill: rgba(10, 15, 26, 0.9); }
        .hz-sun-glow { fill: rgba(255, 214, 79, 0.25); }
        .hz-sun-core { fill: ${elevation >= 0 ? "#ffd54f" : "#ff8a65"}; }
        .hz-state {
          position: absolute;
          top: 12px;
          right: 12px;
          padding: 6px 10px;
          border-radius: 999px;
          background: rgba(0,0,0,0.34);
          color: white;
          font-size: 0.72rem;
          font-weight: 600;
          backdrop-filter: blur(6px);
        }
        .hz-times {
          position: absolute;
          left: 12px;
          right: 12px;
          bottom: 12px;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 8px;
        }
        .hz-time {
          padding: 8px 10px;
          border-radius: 12px;
          background: rgba(255,255,255,0.12);
          color: white;
          text-align: center;
          font-size: 0.72rem;
          backdrop-filter: blur(4px);
        }
        .hz-time-top { display: flex; align-items: center; justify-content: center; gap: 4px; }
        .hz-time-label { font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.06em; opacity: 0.85; font-weight: 600; }
        .hz-time strong { display: block; font-size: 0.85rem; margin-top: 3px; }
        .hz-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          padding: 12px;
        }
        .hz-pill {
          padding: 8px 12px;
          border-radius: 999px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.05);
          color: ${ASTRO.text2};
          font-size: 0.78rem;
        }
        .hz-pill strong { color: ${ASTRO.text1}; margin-right: 4px; }
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:weather-sunset-up"></ha-icon>
          <span class="astro-title">${esc(this._config.title || "Sun Horizon Arc")}</span>
          <span class="astro-badge">${elevation >= 0 ? "Above horizon" : "Below horizon"}</span>
        </div>
        <div class="hz-scene">
          <svg class="hz-svg" viewBox="0 0 400 220" preserveAspectRatio="none">
            <path class="hz-arc" d="M 40,180 A 160,160 0 0,1 360,180"></path>
            <line class="hz-line" x1="20" y1="180" x2="380" y2="180"></line>
            <line class="hz-line" x1="200" y1="20" x2="200" y2="180"></line>
            <rect class="hz-ground" x="0" y="180" width="400" height="40"></rect>
            <g transform="translate(${x.toFixed(2)} ${y.toFixed(2)})">
              <circle class="hz-sun-glow" r="18"></circle>
              <circle class="hz-sun-core" r="8"></circle>
            </g>
          </svg>
          <div class="hz-state">${elevation >= 0 ? (rising ? "Rising" : "Setting") : "Night arc"}</div>
          ${this._config.show_times !== false ? `
            <div class="hz-times">
              <div class="hz-time"><div class="hz-time-top"><span class="hz-time-label">Dawn</span> 🌅</div><strong>${formatTime(nextRise)}</strong></div>
              <div class="hz-time"><div class="hz-time-top"><span class="hz-time-label">Noon</span> ☀️</div><strong>${formatTime(nextNoon)}</strong></div>
              <div class="hz-time"><div class="hz-time-top"><span class="hz-time-label">Dusk</span> 🌇</div><strong>${formatTime(nextSet)}</strong></div>
            </div>
          ` : ""}
        </div>
        <div class="hz-meta">
          ${this._config.show_elevation !== false ? `<span class="hz-pill"><strong>Elevation</strong>${elevation.toFixed(1)}°</span>` : ""}
          ${this._config.show_azimuth !== false ? `<span class="hz-pill"><strong>Azimuth</strong>${azimuth.toFixed(1)}°</span>` : ""}
          ${this._config.show_times !== false ? `<span class="hz-pill"><strong>Sunset</strong>${formatTime(nextSet)}</span>` : ""}
        </div>
      </ha-card>
    `;
  }

  getCardSize() { return 5; }
}

class AstroLunarCardEditor extends AstroEditorBase {
  setConfig(config) {
    super.setConfig({
      moon_entity: "sensor.moon_phase",
      title: "",
      show_next_phases: true,
      show_illumination: true,
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <ha-entity-picker id="moon_entity" label="Moon phase entity"></ha-entity-picker>
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <label class="switch-row"><span>Show next phases</span><ha-switch id="show_next_phases"></ha-switch></label>
      <label class="switch-row"><span>Show illumination</span><ha-switch id="show_illumination"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindPicker("moon_entity", "moon_entity");
    this._bindText("title", "title", (value) => value.trim());
    ["show_next_phases", "show_illumination"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setPickerValue(this.shadowRoot, "moon_entity", this._hass, this._config.moon_entity || "sensor.moon_phase");
    setTextValue(this.shadowRoot, "title", this._config.title || "");
    setSwitchValue(this.shadowRoot, "show_next_phases", this._config.show_next_phases !== false);
    setSwitchValue(this.shadowRoot, "show_illumination", this._config.show_illumination !== false);
  }
}

class AstroLunarCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  static getConfigElement() { return document.createElement("astro-lunar-card-editor"); }
  static getStubConfig() {
    return {
      moon_entity: "sensor.moon_phase",
      title: "",
      show_next_phases: true,
      show_illumination: true,
    };
  }

  setConfig(config) {
    if (!config.moon_entity) throw new Error("You must define a moon_entity");
    this._config = { ...AstroLunarCard.getStubConfig(), ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass) return;
    const stateObj = getState(this._hass, this._config.moon_entity);
    if (!stateObj) {
      this.shadowRoot.innerHTML = renderErrorCard(`Entity not found: ${this._config.moon_entity}`);
      return;
    }

    const phase = normalizePhase(stateObj.state);
    const phaseData = getMoonPhaseData(phase);
    const illumination = toNumber(stateObj.attributes?.illumination, phaseData.illumination);
    const currentIndex = MOON_PHASE_ORDER.indexOf(phase);
    const upcoming = [];
    if (this._config.show_next_phases !== false && currentIndex >= 0) {
      for (let step = 1; step <= 4; step += 1) {
        const nextName = MOON_PHASE_ORDER[(currentIndex + step) % MOON_PHASE_ORDER.length];
        upcoming.push({
          name: nextName.replace(/_/g, " "),
          icon: MOON_ICONS[nextName] || "🌙",
          days: Math.round((step / 8) * 29.5),
        });
      }
    }

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .lunar-sky {
          position: relative;
          padding: 18px 16px 20px;
          background: linear-gradient(180deg, #090d18 0%, #151d39 60%, #1d284d 100%);
          display: flex;
          flex-direction: column;
          align-items: center;
          overflow: hidden;
        }
        .lunar-stars {
          position: absolute;
          inset: 0;
          background-image:
            radial-gradient(1px 1px at 18% 28%, rgba(255,255,255,0.6), transparent),
            radial-gradient(1.4px 1.4px at 82% 22%, rgba(255,255,255,0.5), transparent),
            radial-gradient(1px 1px at 50% 75%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1.2px 1.2px at 12% 70%, rgba(255,255,255,0.5), transparent),
            radial-gradient(1px 1px at 70% 62%, rgba(255,255,255,0.35), transparent);
          pointer-events: none;
        }
        .lunar-moon { position: relative; z-index: 1; filter: drop-shadow(0 0 18px rgba(204, 214, 255, 0.25)); }
        .lunar-copy { position: relative; z-index: 1; text-align: center; color: #edf1ff; margin-top: 12px; }
        .lunar-copy strong { display: block; font-size: 1rem; text-transform: capitalize; }
        .lunar-copy span { display: block; margin-top: 4px; color: rgba(237,241,255,0.72); font-size: 0.8rem; }
        .lunar-next-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
          padding: 12px;
        }
        .lunar-next {
          padding: 10px 6px;
          border-radius: 14px;
          text-align: center;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
        }
        .lunar-next-icon { font-size: 1.15rem; display: block; margin-bottom: 4px; }
        .lunar-next-name { display: block; font-size: 0.66rem; color: ${ASTRO.text2}; text-transform: capitalize; line-height: 1.3; }
        .lunar-next-days { display: block; margin-top: 4px; color: ${ASTRO.accent}; font-size: 0.7rem; font-weight: 600; }
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:moon-waning-crescent"></ha-icon>
          <span class="astro-title">${esc(this._config.title || "Lunar Phase")}</span>
          <span class="astro-badge">${esc(MOON_ICONS[phase] || "🌙")}</span>
        </div>
        <div class="lunar-sky">
          <div class="lunar-stars"></div>
          <div class="lunar-moon">${renderMoonSvg(phaseData.fraction, phaseData.waxing, 160)}</div>
          <div class="lunar-copy">
            <strong>${esc(phaseData.name)}</strong>
            ${this._config.show_illumination !== false ? `<span>${illumination.toFixed(0)}% illuminated</span>` : ""}
          </div>
        </div>
        ${this._config.show_next_phases !== false && upcoming.length ? `
          <div class="lunar-next-grid">
            ${upcoming.map((item) => `
              <div class="lunar-next">
                <span class="lunar-next-icon">${item.icon}</span>
                <span class="lunar-next-name">${esc(item.name)}</span>
                <span class="lunar-next-days">~${item.days}d</span>
              </div>
            `).join("")}
          </div>
        ` : ""}
      </ha-card>
    `;
  }

  getCardSize() { return 5; }
}

class SolarSystemCardEditor extends AstroEditorBase {
  setConfig(config) {
    super.setConfig({
      title: "",
      show_labels: true,
      show_orbits: true,
      show_mercury: true,
      show_venus: true,
      show_earth: true,
      show_mars: true,
      show_jupiter: false,
      show_saturn: false,
      show_stats: true,
      show_date: true,
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <label class="switch-row"><span>Show labels</span><ha-switch id="show_labels"></ha-switch></label>
      <label class="switch-row"><span>Show orbits</span><ha-switch id="show_orbits"></ha-switch></label>
      <label class="switch-row"><span>Show Mercury</span><ha-switch id="show_mercury"></ha-switch></label>
      <label class="switch-row"><span>Show Venus</span><ha-switch id="show_venus"></ha-switch></label>
      <label class="switch-row"><span>Show Earth</span><ha-switch id="show_earth"></ha-switch></label>
      <label class="switch-row"><span>Show Mars</span><ha-switch id="show_mars"></ha-switch></label>
      <label class="switch-row"><span>Show Jupiter</span><ha-switch id="show_jupiter"></ha-switch></label>
      <label class="switch-row"><span>Show Saturn</span><ha-switch id="show_saturn"></ha-switch></label>
      <label class="switch-row"><span>Show stats</span><ha-switch id="show_stats"></ha-switch></label>
      <label class="switch-row"><span>Show date</span><ha-switch id="show_date"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindText("title", "title", (value) => value.trim());
    ["show_labels", "show_orbits", "show_mercury", "show_venus", "show_earth", "show_mars", "show_jupiter", "show_saturn", "show_stats", "show_date"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setTextValue(this.shadowRoot, "title", this._config.title || "");
    ["show_labels", "show_orbits", "show_mercury", "show_venus", "show_earth", "show_mars", "show_stats", "show_date"].forEach((key) => setSwitchValue(this.shadowRoot, key, this._config[key] !== false));
    setSwitchValue(this.shadowRoot, "show_jupiter", this._config.show_jupiter === true);
    setSwitchValue(this.shadowRoot, "show_saturn", this._config.show_saturn === true);
  }
}

class SolarSystemCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._zoom = 1.0;
  }

  static getConfigElement() { return document.createElement("solar-system-card-editor"); }
  static getStubConfig() {
    return {
      title: "",
      show_labels: true,
      show_orbits: true,
      show_mercury: true,
      show_venus: true,
      show_earth: true,
      show_mars: true,
      show_jupiter: false,
      show_saturn: false,
      show_stats: true,
      show_date: true,
    };
  }

  setConfig(config) {
    this._config = { ...SolarSystemCard.getStubConfig(), ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _zoomIn() {
    this._zoom = Math.min(this._zoom * 1.4, 5);
    this._render();
  }

  _zoomOut() {
    this._zoom = Math.max(this._zoom / 1.4, 0.5);
    this._render();
  }

  _render() {
    const date = new Date();
    const center = 200;
    const baseRadius = 165;
    const radius = baseRadius * this._zoom;
    const names = [];
    if (this._config.show_mercury !== false) names.push("Mercury");
    if (this._config.show_venus !== false) names.push("Venus");
    if (this._config.show_earth !== false) names.push("Earth");
    if (this._config.show_mars !== false) names.push("Mars");
    if (this._config.show_jupiter === true) names.push("Jupiter");
    if (this._config.show_saturn === true) names.push("Saturn");

    const positions = names.map((name) => calculatePlanetPosition(name, date));
    const maxOrbit = names.length > 0 ? Math.max(...names.map((name) => PLANET_ELEMENTS[name].a)) * 1.06 : 1;
    const scale = radius / maxOrbit;
    const stars = buildStarFieldSvg(400, 400, 70, 84);

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .orrery-wrap { position: relative; margin: 0 12px 12px; }
        .orrery {
          border-radius: 18px;
          overflow: hidden;
          background: radial-gradient(circle at center, rgba(255,213,79,0.08) 0%, rgba(4,7,16,0.98) 48%, #03050c 100%);
          box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04);
        }
        .orrery-svg { width: 100%; display: block; }
        .orrery-zoom {
          position: absolute;
          top: 8px;
          right: 8px;
          display: flex;
          flex-direction: column;
          gap: 4px;
          z-index: 2;
        }
        .orrery-zoom button {
          width: 30px;
          height: 30px;
          border: none;
          border-radius: 8px;
          background: rgba(255,255,255,0.15);
          color: white;
          font-size: 1.1rem;
          font-weight: bold;
          cursor: pointer;
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.2s;
        }
        .orrery-zoom button:hover { background: rgba(255,255,255,0.28); }
        .orrery-footer { display: flex; flex-wrap: wrap; gap: 8px; padding: 0 12px 14px; }
        .orrery-pill {
          padding: 8px 12px;
          border-radius: 999px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.05);
          color: ${ASTRO.text2};
          font-size: 0.78rem;
        }
        .orrery-pill strong { color: ${ASTRO.text1}; margin-right: 4px; }
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:orbit"></ha-icon>
          <span class="astro-title">${esc(this._config.title || "Solar System Orrery")}</span>
          ${this._config.show_date !== false ? `<span class="astro-badge">${esc(formatDate(date))}</span>` : ""}
        </div>
        <div class="orrery-wrap">
          <div class="orrery-zoom">
            <button id="zoom-in">+</button>
            <button id="zoom-out">−</button>
          </div>
          <div class="orrery">
            <svg class="orrery-svg" viewBox="0 0 400 400" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Solar system orrery">
              ${stars}
              ${this._config.show_orbits !== false ? names.map((name) => `<path d="${buildOrbitPath(name, scale, center)}" fill="none" stroke="${PLANET_ELEMENTS[name].color}" stroke-width="1.4" stroke-opacity="0.55"></path>`).join("") : ""}
              <circle cx="${center}" cy="${center}" r="22" fill="rgba(255,202,40,0.14)"></circle>
              <circle cx="${center}" cy="${center}" r="12" fill="#ffd54f"></circle>
              <circle cx="${center}" cy="${center}" r="5" fill="#fff9c4"></circle>
              ${positions.map((planet) => {
                const px = center + planet.x * scale;
                const py = center + planet.y * scale;
                const pr = planet.name === "Mercury" ? 3.2 : planet.name === "Earth" ? 4.3 : planet.name === "Saturn" ? 5.2 : 4;
                const label = this._config.show_labels !== false
                  ? `<text x="${(px + 8).toFixed(2)}" y="${(py - 8).toFixed(2)}" fill="${planet.color}" font-size="10" font-weight="600">${planet.name}</text>`
                  : "";
                return `
                  <g>
                    <circle cx="${px.toFixed(2)}" cy="${py.toFixed(2)}" r="${pr}" fill="${planet.color}"></circle>
                    <circle cx="${px.toFixed(2)}" cy="${py.toFixed(2)}" r="${(pr + 2).toFixed(1)}" fill="none" stroke="${planet.color}" stroke-opacity="0.35"></circle>
                    ${label}
                  </g>
                `;
              }).join("")}
            </svg>
          </div>
        </div>
        ${this._config.show_stats !== false ? `
          <div class="orrery-footer">
            ${positions.map((p) => `<span class="orrery-pill"><strong>${p.name}</strong>${p.r.toFixed(3)} AU</span>`).join("")}
            <span class="orrery-pill"><strong>Scale</strong>Heliocentric</span>
          </div>
        ` : ""}
      </ha-card>
    `;

    this.shadowRoot.getElementById("zoom-in")?.addEventListener("click", () => this._zoomIn());
    this.shadowRoot.getElementById("zoom-out")?.addEventListener("click", () => this._zoomOut());
  }

  getCardSize() { return 6; }
}

class RocketLaunchCardEditor extends AstroEditorBase {
  setConfig(config) {
    super.setConfig({
      entity_prefix: "sensor.nasa_astronomy_suite_rocket_launch",
      max_launches: 5,
      title: "",
      show_countdown: true,
      show_weather: true,
      show_tags: true,
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <div class="astro-input-wrap"><label for="entity_prefix">Entity prefix</label><input type="text" id="entity_prefix" /></div>
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <div class="astro-input-wrap"><label for="max_launches">Max launches (1-5)</label><input type="number" id="max_launches" min="1" max="5" /></div>
      <label class="switch-row"><span>Show countdown</span><ha-switch id="show_countdown"></ha-switch></label>
      <label class="switch-row"><span>Show weather</span><ha-switch id="show_weather"></ha-switch></label>
      <label class="switch-row"><span>Show tags</span><ha-switch id="show_tags"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindText("entity_prefix", "entity_prefix", (value) => value.trim() || "sensor.nasa_astronomy_suite_rocket_launch");
    this._bindText("title", "title", (value) => value.trim());
    this._bindText("max_launches", "max_launches", (value) => clamp(parseInt(value, 10) || 5, 1, 5));
    ["show_countdown", "show_weather", "show_tags"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setTextValue(this.shadowRoot, "entity_prefix", this._config.entity_prefix || "sensor.nasa_astronomy_suite_rocket_launch");
    setTextValue(this.shadowRoot, "title", this._config.title || "");
    setTextValue(this.shadowRoot, "max_launches", this._config.max_launches || 5);
    setSwitchValue(this.shadowRoot, "show_countdown", this._config.show_countdown !== false);
    setSwitchValue(this.shadowRoot, "show_weather", this._config.show_weather !== false);
    setSwitchValue(this.shadowRoot, "show_tags", this._config.show_tags !== false);
  }
}

class RocketLaunchCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  static getConfigElement() { return document.createElement("rocket-launch-card-editor"); }
  static getStubConfig() {
    return {
      entity_prefix: "sensor.nasa_astronomy_suite_rocket_launch",
      max_launches: 5,
      title: "",
      show_countdown: true,
      show_weather: true,
      show_tags: true,
    };
  }

  setConfig(config) {
    this._config = { ...RocketLaunchCard.getStubConfig(), ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _parseLaunch(stateObj, fallbackName) {
    const attrs = stateObj.attributes || {};
    const launchDate = parseDate(
      attrs.window_start || attrs.net || attrs.target_date || attrs.launch_date || attrs.date || attrs.datetime || stateObj.state,
    );
    const padLocation = [
      attrs.pad_name,
      attrs.location_name,
      attrs.pad?.name,
      attrs.pad?.location?.name,
      attrs.pad,
      attrs.location,
    ].find(Boolean) || "Location TBD";
    const tags = [
      ...(safeArray(attrs.tags).map((tag) => (typeof tag === "string" ? tag : tag?.name)).filter(Boolean)),
      attrs.mission_type,
      attrs.orbit,
      attrs.status,
    ].filter(Boolean);
    return {
      mission: attrs.mission_name || attrs.name || attrs.mission || attrs.friendly_name || fallbackName,
      provider: attrs.provider || attrs.launch_service_provider || attrs.agency || attrs.organization || "Provider TBD",
      vehicle: attrs.vehicle || attrs.rocket || attrs.rocket_name || attrs.launcher || "Vehicle TBD",
      padLocation,
      countdown: launchDate ? formatCountdown(launchDate) : "Date TBD",
      dateLabel: launchDate ? formatDateTime(launchDate) : (attrs.window_start || attrs.net || stateObj.state || "Date TBD"),
      weather: attrs.weather_summary || attrs.launch_weather || attrs.weather || attrs.weather_condition || "",
      tags: [...new Set(tags)].slice(0, 4),
      media: attrs.media_link || attrs.video_url || attrs.stream_url || attrs.webcast || attrs.url || "",
      within24h: launchDate ? isWithinHours(launchDate, 24) : false,
      launchDate,
    };
  }

  _render() {
    if (!this._hass) return;
    const prefix = this._config.entity_prefix || "sensor.nasa_astronomy_suite_rocket_launch";
    const maxLaunches = clamp(parseInt(this._config.max_launches, 10) || 5, 1, 5);
    const launches = [];

    for (let index = 1; index <= 5; index += 1) {
      const entityId = `${prefix}_${index}`;
      const stateObj = getState(this._hass, entityId);
      if (!stateObj || ["unknown", "unavailable"].includes(String(stateObj.state).toLowerCase())) continue;
      launches.push(this._parseLaunch(stateObj, `Launch ${index}`));
    }

    launches.sort((a, b) => {
      if (!a.launchDate && !b.launchDate) return 0;
      if (!a.launchDate) return 1;
      if (!b.launchDate) return -1;
      return a.launchDate - b.launchDate;
    });

    const visible = launches.slice(0, maxLaunches);
    if (!visible.length) {
      this.shadowRoot.innerHTML = renderErrorCard(`No launch sensors found for prefix ${prefix}.`, "mdi:rocket-launch-outline");
      return;
    }

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .launch-list { display: flex; flex-direction: column; gap: 10px; padding: 0 12px 14px; }
        .launch-item {
          padding: 12px;
          border-radius: 16px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
          display: grid;
          grid-template-columns: auto 1fr;
          gap: 12px;
        }
        .launch-item.warn {
          box-shadow: 0 0 0 1px rgba(var(--rgb-warning-color, 255,152,0), 0.25), 0 0 20px rgba(255,152,0,0.12);
        }
        .launch-icon {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(var(--rgb-accent-color, 124,77,255), 0.12);
          color: ${ASTRO.accent};
          flex-shrink: 0;
        }
        .launch-main { min-width: 0; }
        .launch-top {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          align-items: flex-start;
        }
        .launch-mission { font-size: 0.86rem; font-weight: 700; color: ${ASTRO.text1}; line-height: 1.35; }
        .launch-provider { font-size: 0.74rem; color: ${ASTRO.text2}; margin-top: 3px; }
        .launch-when { text-align: right; }
        .launch-date { font-size: 0.76rem; color: ${ASTRO.text2}; }
        .launch-countdown {
          margin-top: 4px;
          display: inline-flex;
          padding: 4px 10px;
          border-radius: 999px;
          background: rgba(var(--rgb-warning-color, 255,152,0), 0.12);
          color: ${ASTRO.warning};
          font-size: 0.72rem;
          font-weight: 700;
        }
        .launch-row { margin-top: 10px; font-size: 0.78rem; color: ${ASTRO.text2}; }
        .launch-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
        .launch-tag {
          padding: 4px 9px;
          border-radius: 999px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.06);
          font-size: 0.68rem;
          color: ${ASTRO.text2};
        }
        .launch-actions { margin-top: 10px; }
        .launch-button {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 8px 12px;
          border-radius: 999px;
          text-decoration: none;
          background: rgba(var(--rgb-accent-color, 124,77,255), 0.1);
          color: ${ASTRO.accent};
          font-size: 0.78rem;
          font-weight: 700;
        }
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:rocket-launch-outline"></ha-icon>
          <span class="astro-title">${esc(this._config.title || "Upcoming Rocket Launches")}</span>
          <span class="astro-badge">${visible.length} shown</span>
        </div>
        <div class="launch-list">
          ${visible.map((launch) => `
            <div class="launch-item ${launch.within24h ? "warn" : ""}">
              <div class="launch-icon"><ha-icon icon="mdi:rocket-launch"></ha-icon></div>
              <div class="launch-main">
                <div class="launch-top">
                  <div>
                    <div class="launch-mission">${esc(launch.mission)}</div>
                    <div class="launch-provider">${esc(launch.provider)} · ${esc(launch.vehicle)}</div>
                  </div>
                  <div class="launch-when">
                    <div class="launch-date">${esc(launch.dateLabel)}</div>
                  </div>
                </div>
                <div class="launch-row">${launch.padLocation ? `📍 ${esc(launch.padLocation)}` : ""}${this._config.show_weather !== false && launch.weather ? ` · ☁️ ${esc(launch.weather)}` : ""}</div>
                ${this._config.show_countdown !== false ? `<div class="launch-countdown">${esc(launch.countdown)}</div>` : ""}
                ${this._config.show_tags !== false && launch.tags.length ? `<div class="launch-tags">${launch.tags.map((tag) => `<span class="launch-tag">${esc(tag)}</span>`).join("")}</div>` : ""}
                ${launch.media ? `<div class="launch-actions"><a class="launch-button" href="${esc(launch.media)}" target="_blank" rel="noopener">Media link ↗</a></div>` : ""}
              </div>
            </div>
          `).join("")}
        </div>
      </ha-card>
    `;
  }

  getCardSize() { return 5; }
}

class IssTrackerCardEditor extends AstroEditorBase {
  setConfig(config) {
    super.setConfig({
      entity: "sensor.nasa_astronomy_suite_iss_position",
      title: "ISS Tracker",
      stream_url: "https://www.youtube.com/watch?v=uwXgcTc8oY8",
      show_map: true,
      show_trail: true,
      show_stream_button: true,
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <ha-entity-picker id="entity" label="ISS position entity"></ha-entity-picker>
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <div class="astro-input-wrap"><label for="stream_url">ISS livestream URL</label><input type="text" id="stream_url" /></div>
      <label class="switch-row"><span>Show map</span><ha-switch id="show_map"></ha-switch></label>
      <label class="switch-row"><span>Show trail</span><ha-switch id="show_trail"></ha-switch></label>
      <label class="switch-row"><span>Show stream button</span><ha-switch id="show_stream_button"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindPicker("entity", "entity");
    this._bindText("title", "title", (value) => value.trim());
    this._bindText("stream_url", "stream_url", (value) => value.trim());
    ["show_map", "show_trail", "show_stream_button"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setPickerValue(this.shadowRoot, "entity", this._hass, this._config.entity || "sensor.nasa_astronomy_suite_iss_position");
    setTextValue(this.shadowRoot, "title", this._config.title || "ISS Tracker");
    setTextValue(this.shadowRoot, "stream_url", this._config.stream_url || "https://www.youtube.com/watch?v=uwXgcTc8oY8");
    setSwitchValue(this.shadowRoot, "show_map", this._config.show_map !== false);
    setSwitchValue(this.shadowRoot, "show_trail", this._config.show_trail !== false);
    setSwitchValue(this.shadowRoot, "show_stream_button", this._config.show_stream_button !== false);
  }
}

class IssTrackerCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._trail = [];
    this._trailKey = "";
    this._lastTrailStamp = "";
  }

  static getConfigElement() { return document.createElement("iss-tracker-card-editor"); }
  static getStubConfig() {
    return {
      entity: "sensor.nasa_astronomy_suite_iss_position",
      title: "ISS Tracker",
      stream_url: "https://www.youtube.com/watch?v=uwXgcTc8oY8",
      show_map: true,
      show_trail: true,
      show_stream_button: true,
    };
  }

  setConfig(config) {
    this._config = { ...IssTrackerCard.getStubConfig(), ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _parsePosition(stateObj) {
    const attrs = stateObj?.attributes || {};
    let latitude = toNumber(attrs.latitude, NaN);
    let longitude = toNumber(attrs.longitude, NaN);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      const parts = String(stateObj?.state || "").split(",").map((part) => parseFloat(part.trim()));
      latitude = parts[0];
      longitude = parts[1];
    }
    // Unix timestamp (seconds) → convert to ms for JS Date
    let ts = attrs.timestamp || stateObj?.last_changed || stateObj?.last_updated || "";
    if (typeof ts === "number" && ts < 9999999999) ts = ts * 1000;
    return {
      latitude,
      longitude,
      timestamp: ts,
      liveStreamUrl: this._config.stream_url || attrs.live_stream_url || "https://www.youtube.com/watch?v=uwXgcTc8oY8",
    };
  }

  _getTrailKey() {
    return `astronomy-cards:iss-trail:${this._config.entity || "sensor.nasa_astronomy_suite_iss_position"}`;
  }

  _loadTrail() {
    const key = this._getTrailKey();
    if (this._trailKey === key) return;
    this._trailKey = key;
    this._lastTrailStamp = "";
    try {
      const parsed = JSON.parse(localStorage.getItem(key) || "[]");
      this._trail = safeArray(parsed)
        .filter((item) => Number.isFinite(item?.latitude) && Number.isFinite(item?.longitude))
        .slice(-12);
      const latest = this._trail[this._trail.length - 1];
      this._lastTrailStamp = latest?.stamp || "";
    } catch (_error) {
      this._trail = [];
    }
  }

  _updateTrail(position) {
    this._loadTrail();
    if (!Number.isFinite(position.latitude) || !Number.isFinite(position.longitude)) return this._trail;
    const stamp = String(position.timestamp || `${position.latitude.toFixed(3)},${position.longitude.toFixed(3)}`);
    if (stamp === this._lastTrailStamp) return this._trail;
    this._lastTrailStamp = stamp;
    this._trail = [...this._trail.filter((item) => item.stamp !== stamp), {
      latitude: position.latitude,
      longitude: position.longitude,
      stamp,
    }].slice(-12);
    try {
      localStorage.setItem(this._trailKey, JSON.stringify(this._trail));
    } catch (_error) {
      // Ignore storage quota issues.
    }
    return this._trail;
  }

  _project(latitude, longitude) {
    return {
      x: clamp(((longitude + 180) / 360) * 100, 0, 100),
      y: clamp(((90 - latitude) / 180) * 100, 0, 100),
    };
  }

  _render() {
    if (!this._hass) return;
    const stateObj = getState(this._hass, this._config.entity);
    const position = this._parsePosition(stateObj);
    if (!stateObj || !Number.isFinite(position.latitude) || !Number.isFinite(position.longitude)) {
      this.shadowRoot.innerHTML = renderErrorCard(`No ISS position data available for ${this._config.entity}.`, "mdi:space-station");
      return;
    }

    const trail = this._updateTrail(position);
    const projected = this._project(position.latitude, position.longitude);
    const trailDots = this._config.show_trail !== false
      ? trail.slice(0, -1).map((item, index, items) => {
        const point = this._project(item.latitude, item.longitude);
        const opacity = ((index + 1) / Math.max(items.length, 1)) * 0.7;
        const size = 4 + ((index + 1) / Math.max(items.length, 1)) * 6;
        return `<div class="iss-trail-dot" style="left:${point.x.toFixed(2)}%;top:${point.y.toFixed(2)}%;width:${size.toFixed(1)}px;height:${size.toFixed(1)}px;background:rgba(255,107,107,${opacity.toFixed(2)});"></div>`;
      }).join("")
      : "";

    // Orbital path line (SVG polyline connecting trail + current position)
    let pathLine = "";
    if (this._config.show_trail !== false && trail.length > 1) {
      const allPoints = [...trail, { latitude: position.latitude, longitude: position.longitude }];
      const svgPoints = allPoints.map(p => {
        const pt = this._project(p.latitude, p.longitude);
        return `${pt.x.toFixed(2)},${pt.y.toFixed(2)}`;
      });
      // Only draw line segments between consecutive points that aren't too far apart (avoid wrapping lines)
      let segments = "";
      for (let i = 1; i < svgPoints.length; i++) {
        const [x1] = svgPoints[i-1].split(",").map(Number);
        const [x2] = svgPoints[i].split(",").map(Number);
        if (Math.abs(x2 - x1) < 40) { // skip wrap-around segments
          segments += `<line x1="${svgPoints[i-1].split(",")[0]}" y1="${svgPoints[i-1].split(",")[1]}" x2="${svgPoints[i].split(",")[0]}" y2="${svgPoints[i].split(",")[1]}" stroke="rgba(255,107,107,0.6)" stroke-width="1.5" stroke-dasharray="4,3"/>`;
        }
      }
      pathLine = `<svg class="iss-path-svg" viewBox="0 0 100 100" preserveAspectRatio="none">${segments}</svg>`;
    }

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .iss-body { padding: 0 12px 14px; display: flex; flex-direction: column; gap: 12px; }
        .iss-map {
          border-radius: 18px;
          overflow: hidden;
          position: relative;
          background: #f8f9fa;
          box-shadow: inset 0 0 0 1px rgba(0,0,0,0.06);
        }
        .iss-map img.iss-world { display: block; width: 100%; height: auto; }
        .iss-marker {
          position: absolute;
          transform: translate(-50%, -50%);
          pointer-events: none;
        }
        .iss-trail-dot {
          position: absolute;
          border-radius: 50%;
          transform: translate(-50%, -50%);
          pointer-events: none;
        }
        .iss-path-svg {
          position: absolute;
          top: 0; left: 0; width: 100%; height: 100%;
          pointer-events: none;
        }
        .iss-icon-svg { filter: drop-shadow(0 1px 3px rgba(0,0,0,0.4)); }
        .iss-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
        .iss-stat {
          border-radius: 14px;
          padding: 12px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
        }
        .iss-stat-label { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.05em; color: ${ASTRO.text2}; }
        .iss-stat-value { margin-top: 4px; font-size: 1rem; font-weight: 700; color: ${ASTRO.text1}; }
        .iss-footer { display: flex; justify-content: space-between; gap: 12px; align-items: center; flex-wrap: wrap; }
        .iss-time { font-size: 0.75rem; color: ${ASTRO.text2}; }
        .iss-button {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 9px 14px;
          border-radius: 999px;
          text-decoration: none;
          background: rgba(var(--rgb-error-color, 244,67,54), 0.12);
          color: ${ASTRO.error};
          font-size: 0.78rem;
          font-weight: 700;
        }
        .iss-dot-core { fill: #ff5252; }
        .iss-dot-pulse { fill: rgba(255,82,82,0.35); transform-origin: center; animation: iss-pulse 2s ease-out infinite; }
        @keyframes iss-pulse {
          0% { transform: scale(0.8); opacity: 0.9; }
          100% { transform: scale(2.4); opacity: 0; }
        }
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:space-station"></ha-icon>
          <span class="astro-title">${esc(this._config.title || "ISS Tracker")}</span>
          <span class="astro-badge">Live orbit</span>
        </div>
        <div class="iss-body">
          ${this._config.show_map !== false ? `
            <div class="iss-map">
              <img class="iss-world" src="/local/community/astronomy-cards/world-map.png" alt="World map" />
              ${pathLine}
              ${trailDots}
              <div class="iss-marker" style="left:${projected.x.toFixed(2)}%;top:${projected.y.toFixed(2)}%;">
                <svg class="iss-icon-svg" width="28" height="28" viewBox="0 0 24 24">
                  <path fill="#000000" d="M11.38 2l-1.75 5.25h4.75L12.62 2h-1.24m1.24 22l1.76-5.25H9.62L11.38 24h1.24M2 11.38v1.24l5.25 1.76V9.62L2 11.38m20 1.24v-1.24l-5.25-1.76v4.76L22 12.62M12 8a4 4 0 0 0-4 4 4 4 0 0 0 4 4 4 4 0 0 0 4-4 4 4 0 0 0-4-4m0 1.5a2.5 2.5 0 0 1 2.5 2.5 2.5 2.5 0 0 1-2.5 2.5A2.5 2.5 0 0 1 9.5 12 2.5 2.5 0 0 1 12 9.5Z"/>
                </svg>
              </div>
            </div>
          ` : ""}
          <div class="iss-grid">
            <div class="iss-stat"><div class="iss-stat-label">Latitude</div><div class="iss-stat-value">${position.latitude}°</div></div>
            <div class="iss-stat"><div class="iss-stat-label">Longitude</div><div class="iss-stat-value">${position.longitude}°</div></div>
          </div>
          <div class="iss-footer">
            <div class="iss-time">Updated ${esc(formatDateTime(position.timestamp))}</div>
            ${this._config.show_stream_button !== false ? `<a class="iss-button" href="${esc(position.liveStreamUrl)}" target="_blank" rel="noopener">Live Stream ↗</a>` : ""}
          </div>
        </div>
      </ha-card>
    `;
  }

  getCardSize() { return this._config.show_map === false ? 3 : 5; }
}

class EarthObservationCardEditor extends AstroEditorBase {
  setConfig(config) {
    super.setConfig({
      epic_entity: "camera.nasa_astronomy_suite_epic_earth",
      goes_entity: "camera.nasa_astronomy_suite_goes_16_earth",
      goes18_entity: "camera.nasa_astronomy_suite_goes_18_earth",
      himawari_entity: "camera.nasa_astronomy_suite_himawari8_earth",
      sdo_entity: "camera.nasa_astronomy_suite_sdo_sun",
      soho_entity: "camera.nasa_astronomy_suite_soho_sun",
      title: "Earth Observation",
      show_epic: true,
      show_goes: true,
      refresh_interval: 5,
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <ha-entity-picker id="epic_entity" label="EPIC camera entity"></ha-entity-picker>
      <ha-entity-picker id="goes_entity" label="GOES-16 camera entity"></ha-entity-picker>
      <ha-entity-picker id="goes18_entity" label="GOES-18 camera entity"></ha-entity-picker>
      <ha-entity-picker id="himawari_entity" label="Himawari-8 camera entity"></ha-entity-picker>
      <ha-entity-picker id="sdo_entity" label="SDO sun camera entity"></ha-entity-picker>
      <ha-entity-picker id="soho_entity" label="SOHO sun camera entity"></ha-entity-picker>
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <div class="astro-input-wrap"><label for="refresh_interval">Refresh interval (minutes)</label><input type="number" id="refresh_interval" min="1" max="60" /></div>
      <label class="switch-row"><span>Show EPIC</span><ha-switch id="show_epic"></ha-switch></label>
      <label class="switch-row"><span>Show GOES-16</span><ha-switch id="show_goes"></ha-switch></label>
    `;
  }

  _setupListeners() {
    ["epic_entity", "goes_entity", "goes18_entity", "himawari_entity", "sdo_entity", "soho_entity"].forEach((key) => this._bindPicker(key, key));
    this._bindText("title", "title", (value) => value.trim());
    this._bindText("refresh_interval", "refresh_interval", (value) => clamp(parseInt(value, 10) || 5, 1, 60));
    ["show_epic", "show_goes"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setPickerValue(this.shadowRoot, "epic_entity", this._hass, this._config.epic_entity || "camera.nasa_astronomy_suite_epic_earth");
    setPickerValue(this.shadowRoot, "goes_entity", this._hass, this._config.goes_entity || "camera.nasa_astronomy_suite_goes_16_earth");
    setPickerValue(this.shadowRoot, "goes18_entity", this._hass, this._config.goes18_entity || "camera.nasa_astronomy_suite_goes_18_earth");
    setPickerValue(this.shadowRoot, "himawari_entity", this._hass, this._config.himawari_entity || "camera.nasa_astronomy_suite_himawari8_earth");
    setPickerValue(this.shadowRoot, "sdo_entity", this._hass, this._config.sdo_entity || "camera.nasa_astronomy_suite_sdo_sun");
    setPickerValue(this.shadowRoot, "soho_entity", this._hass, this._config.soho_entity || "camera.nasa_astronomy_suite_soho_sun");
    setTextValue(this.shadowRoot, "title", this._config.title || "Earth Observation");
    setTextValue(this.shadowRoot, "refresh_interval", this._config.refresh_interval || 5);
    setSwitchValue(this.shadowRoot, "show_epic", this._config.show_epic !== false);
    setSwitchValue(this.shadowRoot, "show_goes", this._config.show_goes !== false);
  }
}

class EarthObservationCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._activeView = "epic";
    this._refreshHandle = 0;
    this._refreshToken = Date.now();
  }

  static getConfigElement() { return document.createElement("earth-observation-card-editor"); }
  static getStubConfig() {
    return {
      epic_entity: "camera.nasa_astronomy_suite_epic_earth",
      goes_entity: "camera.nasa_astronomy_suite_goes_16_earth",
      goes18_entity: "camera.nasa_astronomy_suite_goes_18_earth",
      himawari_entity: "camera.nasa_astronomy_suite_himawari8_earth",
      sdo_entity: "camera.nasa_astronomy_suite_sdo_sun",
      soho_entity: "camera.nasa_astronomy_suite_soho_sun",
      title: "Earth Observation",
      show_epic: true,
      show_goes: true,
      refresh_interval: 5,
    };
  }

  connectedCallback() {
    this._ensureRefreshTimer();
  }

  disconnectedCallback() {
    if (this._refreshHandle) {
      clearInterval(this._refreshHandle);
      this._refreshHandle = 0;
    }
  }

  setConfig(config) {
    this._config = { ...EarthObservationCard.getStubConfig(), ...config };
    this._selectDefaultView();
    this._ensureRefreshTimer();
  }

  set hass(hass) {
    this._hass = hass;
    this._selectDefaultView();
    this._render();
  }

  _getViews() {
    return [
      { key: "epic", title: "EPIC", group: "earth", entityId: this._config.epic_entity, enabled: this._config.show_epic !== false, fallbackSource: "NASA EPIC", fallbackDetail: "Daily Earth imagery from NASA EPIC." },
      { key: "goes", title: "GOES-16", group: "earth", entityId: this._config.goes_entity, enabled: this._config.show_goes !== false, fallbackSource: "NOAA GOES-16", fallbackDetail: "Geostationary Earth observation imagery." },
      { key: "goes18", title: "GOES-18", group: "earth", entityId: this._config.goes18_entity, enabled: true, fallbackSource: "NOAA GOES-18", fallbackDetail: "Pacific geostationary Earth observation imagery." },
      { key: "himawari", title: "Himawari", group: "earth", entityId: this._config.himawari_entity, enabled: true, fallbackSource: "Himawari-8", fallbackDetail: "Asia-Pacific Earth observation imagery." },
      { key: "sdo", title: "SDO", group: "sun", entityId: this._config.sdo_entity, enabled: true, fallbackSource: "NASA SDO", fallbackDetail: "Solar Dynamics Observatory imagery." },
      { key: "soho", title: "SOHO", group: "sun", entityId: this._config.soho_entity, enabled: true, fallbackSource: "ESA/NASA SOHO", fallbackDetail: "Solar coronagraph imagery." },
    ].filter((view) => view.enabled && view.entityId && (!this._hass || getState(this._hass, view.entityId)));
  }

  _selectDefaultView() {
    const views = this._getViews();
    if (!views.some((view) => view.key === this._activeView)) {
      this._activeView = views[0]?.key || "epic";
    }
  }

  _ensureRefreshTimer() {
    if (this._refreshHandle) {
      clearInterval(this._refreshHandle);
      this._refreshHandle = 0;
    }
    if (!this.isConnected) return;
    const intervalMinutes = clamp(parseInt(this._config.refresh_interval, 10) || 5, 1, 60);
    this._refreshHandle = window.setInterval(() => {
      this._refreshToken = Date.now();
      this._render();
    }, intervalMinutes * 60 * 1000);
  }

  _getImageUrl(entityId, stateObj) {
    const picture = stateObj?.attributes?.entity_picture;
    if (picture) return `${picture}${picture.includes("?") ? "&" : "?"}t=${this._refreshToken}`;
    return `/api/camera_proxy/${entityId}?t=${this._refreshToken}`;
  }

  _getViewData(view) {
    const stateObj = getState(this._hass, view.entityId);
    if (!stateObj) return null;
    const attrs = stateObj.attributes || {};
    return {
      ...view,
      stateObj,
      imageUrl: this._getImageUrl(view.entityId, stateObj),
      source: attrs.source_info || attrs.source || attrs.attribution || view.fallbackSource,
      headline: formatDateTime(attrs.date || attrs.timestamp || stateObj.last_updated || stateObj.last_changed),
      detail: attrs.caption || attrs.description || attrs.summary || attrs.sector || attrs.view || view.fallbackDetail,
    };
  }

  _render() {
    if (!this._hass) return;
    const views = this._getViews();
    if (!views.length) {
      this.shadowRoot.innerHTML = renderErrorCard("Enable at least one configured Earth or Sun camera in the card editor.", "mdi:earth");
      return;
    }

    this._selectDefaultView();
    const dataOptions = views.map((view) => this._getViewData(view)).filter(Boolean);
    const earthViews = dataOptions.filter((view) => view.group === "earth");
    const sunViews = dataOptions.filter((view) => view.group === "sun");
    const active = dataOptions.find((view) => view.key === this._activeView) || dataOptions[0];
    if (!active) {
      this.shadowRoot.innerHTML = renderErrorCard("No configured Earth or Sun cameras are currently available.", "mdi:earth");
      return;
    }
    this._activeView = active.key;

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .earth-body { padding: 0 12px 14px; }
        .earth-tabs {
          display: flex;
          gap: 10px;
          padding-bottom: 12px;
          flex-wrap: wrap;
          scrollbar-width: thin;
        }
        .earth-tab-section { display: flex; align-items: center; gap: 8px; flex-wrap: nowrap; width: 100%; }
        .earth-tab-label {
          font-size: 0.7rem;
          font-weight: 700;
          color: ${ASTRO.text2};
          text-transform: uppercase;
          letter-spacing: 0.05em;
          white-space: nowrap;
        }
        .earth-tab-row { display: flex; gap: 8px; }
        .earth-tab-divider {
          width: 1px;
          align-self: stretch;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.08);
        }
        .earth-tab {
          border: none;
          cursor: pointer;
          border-radius: 999px;
          padding: 8px 12px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.06);
          color: ${ASTRO.text2};
          font: inherit;
          font-size: 0.78rem;
          font-weight: 700;
          white-space: nowrap;
        }
        .earth-tab.active { background: rgba(var(--rgb-accent-color, 124,77,255), 0.14); color: ${ASTRO.accent}; }
        .earth-frame {
          border-radius: 18px;
          overflow: hidden;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
          box-shadow: inset 0 0 0 1px rgba(var(--rgb-primary-text-color, 0,0,0), 0.06);
        }
        .earth-frame img { display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; }
        .earth-frame.sun img { object-fit: contain; background: #000; }
        .earth-meta { padding: 12px 2px 0; display: flex; flex-direction: column; gap: 8px; }
        .earth-headline { font-size: 0.84rem; font-weight: 700; color: ${ASTRO.text1}; }
        .earth-detail { font-size: 0.78rem; line-height: 1.45; color: ${ASTRO.text2}; }
        .earth-source { font-size: 0.74rem; color: ${ASTRO.text2}; }
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:earth"></ha-icon>
          <span class="astro-title">${esc(this._config.title || "Earth Observation")}</span>
          <span class="astro-badge">${clamp(parseInt(this._config.refresh_interval, 10) || 5, 1, 60)}m refresh</span>
        </div>
        <div class="earth-body">
          ${dataOptions.length > 1 ? `
            <div class="earth-tabs">
              ${earthViews.length ? `
                <div class="earth-tab-section">
                  <div class="earth-tab-label">🌍 Earth</div>
                  <div class="earth-tab-row">
                    ${earthViews.map((view) => `<button type="button" class="earth-tab ${view.key === active.key ? "active" : ""}" data-view="${view.key}">${esc(view.title)}</button>`).join("")}
                  </div>
                </div>
              ` : ""}
              ${earthViews.length && sunViews.length ? `</div><div class="earth-tabs">` : ""}
              ${sunViews.length ? `
                <div class="earth-tab-section">
                  <div class="earth-tab-label">☀️ Sun</div>
                  <div class="earth-tab-row">
                    ${sunViews.map((view) => `<button type="button" class="earth-tab ${view.key === active.key ? "active" : ""}" data-view="${view.key}">${esc(view.title)}</button>`).join("")}
                  </div>
                </div>
              ` : ""}
            </div>
          ` : ""}
          <div class="earth-frame ${active.group === "sun" ? "sun" : "earth"}"><img src="${esc(active.imageUrl)}" alt="${esc(active.title)} ${active.group === "sun" ? "Sun" : "Earth"} observation"></div>
          <div class="earth-meta">
            <div class="earth-headline">${esc(active.headline)}</div>
            <div class="earth-detail">${esc(active.detail)}</div>
            <div class="earth-source">Source: ${esc(active.source)}</div>
          </div>
        </div>
      </ha-card>
    `;

    this.shadowRoot.querySelectorAll(".earth-tab").forEach((button) => {
      button.addEventListener("click", () => {
        this._activeView = button.dataset.view;
        this._render();
      });
    });
  }

  getCardSize() { return 5; }
}

function defineElement(name, ctor) {
  if (!customElements.get(name)) customElements.define(name, ctor);
}

function registerCustomCard(type, name, description) {
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === type)) {
    window.customCards.push({ type, name, description, preview: true, documentationURL: DOCS_URL });
  }
}

defineElement("apod-card-editor", ApodCardEditor);
defineElement("neo-threat-card-editor", NeoThreatCardEditor);
defineElement("solar-activity-card-editor", SolarActivityCardEditor);
defineElement("astro-horizon-card-editor", AstroHorizonCardEditor);
defineElement("astro-lunar-card-editor", AstroLunarCardEditor);
defineElement("solar-system-card-editor", SolarSystemCardEditor);
defineElement("rocket-launch-card-editor", RocketLaunchCardEditor);
defineElement("iss-tracker-card-editor", IssTrackerCardEditor);
defineElement("earth-observation-card-editor", EarthObservationCardEditor);

// ─── Night Sky Highlights Card ───────────────────────────────────────────────
class NightSkyHighlightsEditor extends AstroEditorBase {
  static get properties() { return { _config: {} }; }
  setConfig(config) { this._config = { ...config }; }
  get _title() { return this._config.title || "Night Sky Highlights"; }
  get _telescope_mode() { return this._config.telescope_mode || false; }
  render() {
    if (!this._hass) return html``;
    return html`
      <style>${EDITOR_STYLES}</style>
      <div class="astro-editor">
        <div class="astro-input-wrap">
          <label>Card Title</label>
          <input type="text" .value="${this._title}" @input="${(e) => this._valueChanged('title', e.target.value)}" @change="${(e) => this._valueChanged('title', e.target.value)}">
        </div>
        <div style="display:flex;align-items:center;gap:8px;margin:8px 0;">
          <ha-switch .checked="${this._telescope_mode}" @change="${(e) => this._valueChanged('telescope_mode', e.target.checked)}"></ha-switch>
          <span>Telescope Mode (alt &gt; 30°)</span>
        </div>
      </div>
    `;
  }
  _valueChanged(key, value) {
    this._config = { ...this._config, [key]: value };
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
  }
}

class NightSkyHighlightsCard extends HTMLElement {
  static getConfigElement() { return document.createElement("night-sky-highlights-card-editor"); }
  static getStubConfig() { return { title: "Night Sky Highlights", telescope_mode: false }; }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._lastStateHash = "";
  }

  setConfig(config) {
    this._config = { title: "Night Sky Highlights", telescope_mode: false, ...config };
  }

  set hass(hass) {
    this._hass = hass;
    const hash = this._computeHash();
    if (hash !== this._lastStateHash) {
      this._lastStateHash = hash;
      this._render();
    }
  }

  _computeHash() {
    const bodies = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"];
    let h = "";
    for (const b of bodies) {
      const alt = this._hass.states[`sensor.nasa_astronomy_ephemeris_${b}_altitude`];
      if (alt) h += alt.state + ";";
    }
    const tw = this._hass.states["sensor.nasa_astronomy_ephemeris_sky_twilight_phase"];
    if (tw) h += tw.state;
    return h;
  }

  _getBodyData() {
    const bodies = ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"];
    const minAlt = this._config.telescope_mode ? 30 : 20;
    const visible = [];
    for (const b of bodies) {
      const altEntity = this._hass.states[`sensor.nasa_astronomy_ephemeris_${b}_altitude`];
      const illEntity = this._hass.states[`sensor.nasa_astronomy_ephemeris_${b}_illumination_pct`];
      const visStart = this._hass.states[`sensor.nasa_astronomy_ephemeris_${b}_visibility_start`];
      const visEnd = this._hass.states[`sensor.nasa_astronomy_ephemeris_${b}_visibility_end`];
      if (!altEntity) continue;
      const alt = parseFloat(altEntity.state);
      if (isNaN(alt)) continue;
      visible.push({
        name: b.charAt(0).toUpperCase() + b.slice(1),
        altitude: alt,
        illumination: illEntity ? parseFloat(illEntity.state) : null,
        visStart: visStart ? visStart.state : null,
        visEnd: visEnd ? visEnd.state : null,
        aboveMin: alt >= minAlt,
      });
    }
    visible.sort((a, b) => b.altitude - a.altitude);
    return visible;
  }

  _getMoonData() {
    const alt = this._hass.states["sensor.nasa_astronomy_ephemeris_moon_altitude"];
    const ill = this._hass.states["sensor.nasa_astronomy_ephemeris_moon_illumination_pct"];
    const phase = this._hass.states["sensor.nasa_astronomy_ephemeris_moon_phase_angle"];
    return {
      altitude: alt ? parseFloat(alt.state) : null,
      illumination: ill ? parseFloat(ill.state) : null,
      phase: phase ? parseFloat(phase.state) : null,
      visible: alt ? parseFloat(alt.state) > 0 : false,
    };
  }

  _getTwilightPhase() {
    const tw = this._hass.states["sensor.nasa_astronomy_ephemeris_sky_twilight_phase"];
    return tw ? tw.state : "unknown";
  }

  _getSunAlt() {
    const s = this._hass.states["sensor.nasa_astronomy_ephemeris_sun_altitude"];
    return s ? parseFloat(s.state) : null;
  }

  _getBodyIcon(name) {
    const icons = { Mercury: "☿", Venus: "♀", Mars: "♂", Jupiter: "♃", Saturn: "♄", Uranus: "⛢", Neptune: "♆" };
    return icons[name] || "●";
  }

  _render() {
    const sunAlt = this._getSunAlt();
    const isDark = sunAlt !== null && sunAlt < -12;
    const moon = this._getMoonData();
    const planets = this._getBodyData();
    const minAlt = this._config.telescope_mode ? 30 : 20;
    const top3 = planets.filter(p => p.aboveMin).slice(0, 3);
    const hasSensors = planets.length > 0 || moon.altitude !== null;

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .nsh-body { padding: 0 12px 14px; display: flex; flex-direction: column; gap: 12px; }
        .nsh-section-title { font-size:0.72rem; text-transform:uppercase; letter-spacing:0.05em; color:${ASTRO.text2}; margin-bottom:6px; }
        .nsh-moon { display:flex; gap:12px; align-items:center; padding:10px 14px; border-radius:14px; background:rgba(var(--rgb-primary-text-color,0,0,0),0.04); }
        .nsh-moon-icon { font-size:1.6em; }
        .nsh-moon-info { display:flex; flex-direction:column; gap:2px; }
        .nsh-moon-label { font-size:0.78rem; color:${ASTRO.text2}; }
        .nsh-top3 { display:flex; gap:8px; flex-wrap:wrap; }
        .nsh-top3-item { flex:1; min-width:80px; padding:12px 8px; border-radius:14px; text-align:center; background:rgba(var(--rgb-primary-text-color,0,0,0),0.04); }
        .nsh-top3-icon { font-size:1.5em; margin-bottom:4px; }
        .nsh-top3-name { font-size:0.82rem; font-weight:600; color:${ASTRO.text1}; }
        .nsh-top3-alt { font-size:0.72rem; color:${ASTRO.text2}; }
        .nsh-planet-row { display:flex; align-items:center; gap:10px; padding:8px 14px; border-radius:14px; background:rgba(var(--rgb-primary-text-color,0,0,0),0.04); margin-bottom:4px; }
        .nsh-planet-icon { font-size:1.2em; width:24px; text-align:center; }
        .nsh-planet-name { flex:1; font-weight:600; font-size:0.9rem; color:${ASTRO.text1}; }
        .nsh-planet-vis { font-size:0.72rem; color:${ASTRO.text2}; }
        .nsh-planet-alt { font-size:0.85rem; color:${ASTRO.text2}; min-width:45px; text-align:right; }
        .nsh-no-data { padding:20px; text-align:center; color:${ASTRO.text2}; font-style:italic; }
        .nsh-badge { display:inline-block; padding:2px 8px; border-radius:99px; font-size:0.7em; font-weight:700; margin-left:auto; }
        .nsh-badge-dark { background:rgba(76,175,80,0.15); color:#66bb6a; }
        .nsh-badge-light { background:rgba(255,152,0,0.15); color:#ffa726; }
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:telescope"></ha-icon>
          <span class="astro-title">${esc(this._config.title || "Night Sky Highlights")}</span>
          ${isDark ? '<span class="nsh-badge nsh-badge-dark">Dark Sky</span>' : sunAlt !== null ? '<span class="nsh-badge nsh-badge-light">Daylight</span>' : ''}
        </div>
        <div class="nsh-body">
          ${!hasSensors ? '<div class="nsh-no-data">Enable ephemeris sensors in integration options to see night sky data.</div>' : `
            ${moon.altitude !== null ? `
            <div>
              <div class="nsh-section-title">Moon</div>
              <div class="nsh-moon">
                <span class="nsh-moon-icon">🌙</span>
                <div class="nsh-moon-info">
                  <span style="font-weight:600;color:${ASTRO.text1}">${moon.visible ? 'Above Horizon' : 'Below Horizon'} — ${moon.altitude !== null ? moon.altitude.toFixed(1) + '°' : ''}</span>
                  <span class="nsh-moon-label">Illumination: ${moon.illumination !== null ? moon.illumination.toFixed(0) + '%' : 'N/A'}</span>
                </div>
              </div>
            </div>` : ''}

            ${top3.length > 0 ? `
            <div>
              <div class="nsh-section-title">Top Objects Tonight</div>
              <div class="nsh-top3">
                ${top3.map(p => `
                  <div class="nsh-top3-item">
                    <div class="nsh-top3-icon">${this._getBodyIcon(p.name)}</div>
                    <div class="nsh-top3-name">${p.name}</div>
                    <div class="nsh-top3-alt">${p.altitude.toFixed(1)}° alt</div>
                  </div>
                `).join('')}
              </div>
            </div>` : ''}

            <div>
              <div class="nsh-section-title">All Planets ${this._config.telescope_mode ? '(Telescope: &gt;30°)' : '(&gt;' + minAlt + '°)'}</div>
              ${planets.length > 0 ? planets.map(p => `
                <div class="nsh-planet-row" style="opacity:${p.aboveMin ? 1 : 0.5}">
                  <span class="nsh-planet-icon">${this._getBodyIcon(p.name)}</span>
                  <span class="nsh-planet-name">${p.name}</span>
                  ${p.visStart && p.visEnd && p.visStart !== "unknown" && p.visEnd !== "unknown" ? `<span class="nsh-planet-vis">${p.visStart}–${p.visEnd}</span>` : ''}
                  <span class="nsh-planet-alt">${p.altitude.toFixed(1)}°</span>
                </div>
              `).join('') : '<div style="padding:8px;color:' + ASTRO.text2 + '">No planet sensors available</div>'}
            </div>
          `}
        </div>
      </ha-card>
    `;
  }

  _twilightColor(phase) {
    const colors = { "Day": "#fdd835", "Civil Twilight": "#ff8f00", "Nautical Twilight": "#5c6bc0", "Astronomical Twilight": "#283593", "Night": "#0d1b2a" };
    return colors[phase] || "#666";
  }

  getCardSize() { return 5; }
}

// ─── End Night Sky Highlights Card ──────────────────────────────────────────

defineElement("apod-card", ApodCard);
defineElement("neo-threat-card", NeoThreatCard);
defineElement("solar-activity-card", SolarActivityCard);
defineElement("astro-horizon-card", AstroHorizonCard);
defineElement("astro-lunar-card", AstroLunarCard);
defineElement("solar-system-card", SolarSystemCard);
defineElement("rocket-launch-card", RocketLaunchCard);
defineElement("iss-tracker-card", IssTrackerCard);
defineElement("earth-observation-card", EarthObservationCard);
defineElement("night-sky-highlights-card-editor", NightSkyHighlightsEditor);
defineElement("night-sky-highlights-card", NightSkyHighlightsCard);

registerCustomCard("apod-card", "ASS APOD Card", "Astronomy Picture of the Day card with editor");
registerCustomCard("neo-threat-card", "ASS NEO Threat Card", "Near-Earth object tracker with editor");
registerCustomCard("solar-activity-card", "ASS Solar Activity Card", "Solar activity monitor with editor");
registerCustomCard("astro-horizon-card", "ASS Horizon Card", "Sun arc horizon visualization with editor");
registerCustomCard("astro-lunar-card", "ASS Lunar Card", "Moon phase visualization with editor");
registerCustomCard("solar-system-card", "ASS Solar System Card", "Client-side heliocentric orrery with editor");
registerCustomCard("rocket-launch-card", "ASS Rocket Launch Card", "Upcoming rocket launches list with editor");
registerCustomCard("iss-tracker-card", "ASS ISS Tracker Card", "International Space Station position tracker with editor");
registerCustomCard("earth-observation-card", "ASS Earth Observation Card", "NASA EPIC and NOAA GOES Earth imagery viewer with editor");
registerCustomCard("night-sky-highlights-card", "ASS Night Sky Highlights Card", "Best visible objects tonight based on ephemeris with editor");

console.info(
  "%c Astronomy Space Suite Cards v1.8.1 %c",
  "color:white;background:#1a237e;font-weight:bold;padding:2px 8px;border-radius:4px 0 0 4px;",
  "color:#1a237e;background:#e8eaf6;font-weight:bold;padding:2px 8px;border-radius:0 4px 4px 0;",
);
