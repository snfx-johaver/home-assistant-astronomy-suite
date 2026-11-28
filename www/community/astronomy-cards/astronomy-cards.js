/**
 * Astronomy Space Suite Cards v1.19.1
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
  :host([glass-mode]) {
    contain: layout style;
    --_astronomy-card-background: var(--astronomy-card-background, transparent);
    --_astronomy-card-backdrop-filter: var(--astronomy-card-backdrop-filter, blur(16px) saturate(135%));
    --_astronomy-card-border: var(--astronomy-card-border, 1px solid rgba(var(--rgb-primary-text-color, 255,255,255), 0.14));
    --_astronomy-card-box-shadow: var(--astronomy-card-box-shadow, 0 10px 32px rgba(0,0,0,0.18), 0 0 18px rgba(var(--rgb-primary-color, 3,169,244), 0.08));
  }
  .astro-card {
    background: var(--_astronomy-card-background, var(--astronomy-card-background, ${ASTRO.surface}));
    border-radius: ${ASTRO.radius};
    border: var(--_astronomy-card-border, var(--astronomy-card-border, var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color, #e0e0e0))));
    box-shadow: var(--_astronomy-card-box-shadow, var(--astronomy-card-box-shadow, ${ASTRO.shadow}));
    backdrop-filter: var(--_astronomy-card-backdrop-filter, var(--astronomy-card-backdrop-filter, none));
    -webkit-backdrop-filter: var(--_astronomy-card-backdrop-filter, var(--astronomy-card-backdrop-filter, none));
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
const VERSION = "1.19.1";
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
  Uranus: { a: 19.191, e: 0.0472, L: 313.23, wBar: 170.96, daily: 0.0117, color: "#80deea" },
  Neptune: { a: 30.069, e: 0.0086, L: 304.88, wBar: 44.97, daily: 0.0060, color: "#7986cb" },
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

// Accept only strings that actually look like a date. The legacy V8 date parser is
// extremely permissive and happily turns free-form text into a real Date — e.g.
// new Date("EOS-05 (ISRO)") === 2001-05-01 and new Date("Progress MS-35 (...)") === 2035-01-01.
// Requiring date-ish characters plus a 4-digit year keeps mission names out.
const DATE_LIKE_RE = /^[0-9A-Za-z:\-/+.,\s]+$/;
const DATE_YEAR_RE = /(^|\D)\d{4}(\D|$)/;

function parseDate(value) {
  if (value === null || value === undefined || value === "") return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;
  if (typeof value === "number") {
    if (!Number.isFinite(value) || value <= 0) return null;
    // Epoch seconds (e.g. the ISS feed) vs. epoch milliseconds.
    const numeric = new Date(value < 1e11 ? value * 1000 : value);
    return Number.isNaN(numeric.getTime()) ? null : numeric;
  }
  if (typeof value !== "string") return null;
  const text = value.trim();
  if (!DATE_LIKE_RE.test(text) || !DATE_YEAR_RE.test(text)) return null;
  const date = new Date(text);
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

function updateCardHass(card, hass, entityIds, clock = null) {
  card._hass = hass;
  // HA replaces changed state objects; retain references rather than hashing attributes.
  const inputs = [
    card._config, hass.config, hass.themes, hass.locale, clock,
    ...entityIds.map((id) => hass.states[id]),
  ];
  const previous = card._renderInputs;
  card._renderInputs = inputs;
  return !previous || inputs.length !== previous.length
    || inputs.some((value, index) => value !== previous[index]);
}

function configuredEntities(config) {
  return Object.entries(config)
    .filter(([key]) => key === "entity" || key.endsWith("_entity"))
    .map(([, value]) => value);
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
  if (picker.hass !== hass) picker.hass = hass;
  if (picker.value !== (value || "")) picker.value = value || "";
}

function setTextValue(root, id, value) {
  const field = root.getElementById(id);
  const text = value == null ? "" : String(value);
  if (field && field.value !== text) field.value = text;
}

function setSwitchValue(root, id, checked) {
  const sw = root.getElementById(id);
  if (sw && sw.checked !== Boolean(checked)) sw.checked = Boolean(checked);
}

function setSelectValue(root, id, value) {
  const select = root.getElementById(id);
  if (select && select.value !== String(value)) select.value = String(value);
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

function buildOrbitPath(name, scale, center, samples = 180, compressed = false) {
  const planet = PLANET_ELEMENTS[name];
  const wBar = degToRad(planet.wBar);
  const points = [];
  for (let i = 0; i <= samples; i += 1) {
    const trueAnomaly = (Math.PI * 2 * i) / samples;
    const radius = (planet.a * (1 - planet.e * planet.e)) / (1 + planet.e * Math.cos(trueAnomaly));
    const angle = trueAnomaly + wBar;
    const displayRadius = compressed ? Math.sqrt(radius) : radius;
    const x = center + displayRadius * Math.cos(angle) * scale;
    const y = center + displayRadius * Math.sin(angle) * scale;
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
    if (this._rendered) {
      this.shadowRoot.querySelectorAll("ha-entity-picker").forEach((picker) => {
        if (picker.hass !== hass) picker.hass = hass;
      });
    }
    else this._render();
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>${EDITOR_STYLES}</style>
      <div class="editor">
        ${this._editorTemplate()}
        <label class="switch-row"><span>Glass appearance</span><ha-switch id="glass_mode"></ha-switch></label>
      </div>
    `;
    this._rendered = true;
    this._setupListeners();
    this._bindSwitch("glass_mode", "glass_mode");
    this._updateValues();
  }

  _updateValues() {
    setSwitchValue(this.shadowRoot, "glass_mode", this._config.glass_mode === true);
    this._syncValues();
  }

  _setValue(key, value) {
    if (this._config[key] === value) return;
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
      entity: "sensor.astronomy_space_suite_apod",
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
  }

  static getConfigElement() { return document.createElement("apod-card-editor"); }
  static getStubConfig() {
    return {
      entity: "sensor.astronomy_space_suite_apod",
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
  }

  set hass(hass) {
    if (updateCardHass(this, hass, [this._config.entity])) this._render();
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
          <video src="${esc(url)}" title="${esc(mediaTitle)}" controls playsinline preload="metadata"${hdurl ? ` poster="${esc(hdurl)}"` : ""}></video>
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
        .apod-video video {
          width: 100%;
          height: 100%;
          display: block;
          border: 0;
          object-fit: contain;
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
      entity: "sensor.astronomy_space_suite_neo_count_today",
      largest_entity: "sensor.astronomy_space_suite_largest_neo",
      max_items: 5,
      sort_by: "distance",
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
      <div class="astro-input-wrap"><label for="sort_by">Sort approaches</label><select id="sort_by"><option value="distance">Closest first</option><option value="date">Soonest first</option><option value="diameter">Largest first</option><option value="velocity">Fastest first</option></select></div>
      <p>Data covers the current UTC calendar day, not the full asteroid catalogue. Potentially hazardous is NASA's classification, not an impact warning.</p>
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
    this._bindSelect("sort_by", "sort_by");
    ["show_hazardous_only", "show_stats", "show_velocity", "show_diameter"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setPickerValue(this.shadowRoot, "entity", this._hass, this._config.entity);
    setPickerValue(this.shadowRoot, "largest_entity", this._hass, this._config.largest_entity || "");
    setTextValue(this.shadowRoot, "title", this._config.title || "");
    setTextValue(this.shadowRoot, "max_items", this._config.max_items || 5);
    setTextValue(this.shadowRoot, "sort_by", this._config.sort_by || "distance");
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
      entity: "sensor.astronomy_space_suite_neo_count_today",
      largest_entity: "sensor.astronomy_space_suite_largest_neo",
      max_items: 5,
      sort_by: "distance",
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
    if (updateCardHass(this, hass, configuredEntities(this._config))) this._render();
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

    const sorters = {
      distance: { label: "Closest first", key: (item) => toNumber(item.miss_distance_km ?? Infinity, Infinity) },
      date: { label: "Soonest first", key: (item) => toNumber(item.close_approach_timestamp ?? Infinity, Infinity) },
      diameter: { label: "Largest first", key: (item) => -toNumber(item.diameter_max_m, 0) },
      velocity: { label: "Fastest first", key: (item) => -toNumber(item.velocity_kmh, 0) },
    };
    const sorter = Object.hasOwn(sorters, this._config.sort_by) ? sorters[this._config.sort_by] : sorters.distance;
    const sorted = [...neoList].sort((a, b) => sorter.key(a) - sorter.key(b));
    const displayed = sorted.slice(0, clamp(parseInt(this._config.max_items, 10) || 5, 1, 20));
    const hazardousCount = sorted.filter((item) => item.hazardous).length;
    const totalCount = sorted.length;
    const closest = [...sorted].sort((a, b) => toNumber(a.miss_distance_km ?? Infinity, Infinity) - toNumber(b.miss_distance_km ?? Infinity, Infinity))[0];
    const fastest = [...sorted].sort((a, b) => toNumber(b.velocity_kmh, 0) - toNumber(a.velocity_kmh, 0))[0];
    const title = this._config.title || "Near-Earth Objects";

    const largest = [...sorted].sort((a, b) => toNumber(b.diameter_max_m, 0) - toNumber(a.diameter_max_m, 0))[0];
    const largestState = this._config.largest_entity ? getState(this._hass, this._config.largest_entity) : null;
    const largestName = largest?.name || (!Array.isArray(attrs.neo_list) && !this._config.show_hazardous_only ? largestState?.state : null) || "—";
    const range = attrs.start_date
      ? `${attrs.start_date}${attrs.end_date && attrs.end_date !== attrs.start_date ? ` to ${attrs.end_date}` : ""} (${attrs.date_timezone || "feed time"})`
      : "Date range unavailable — update the integration";

    const listHtml = displayed.length
      ? displayed.map((neo) => {
          const detail = [];
          if (this._config.show_diameter !== false) detail.push(`⌀ ${formatMeters(neo.diameter_max_m || neo.diameter_min_m)}`);
          if (this._config.show_velocity !== false) detail.push(formatSpeedKmh(neo.velocity_kmh));
          const approach = parseDate(neo.close_approach_timestamp);
          if (approach) detail.push(`${approach.toISOString().slice(0, 16).replace("T", " ")} UTC`);
          else if (neo.close_approach_date) detail.push(`${neo.close_approach_date} UTC`);
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
        ha-card { display: block; container-type: inline-size; }
        .astro-header { flex-wrap: wrap; }
        .astro-title { flex: 1 1 160px; min-width: 0; overflow-wrap: anywhere; }
        .neo-context { padding: 0 16px 12px; color: ${ASTRO.text2}; font-size: 0.75rem; line-height: 1.5; }
        .neo-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .neo-stats .astro-stat { min-width: 0; }
        .neo-stats .astro-stat-value {
          font-size: 1rem;
          overflow-wrap: anywhere;
          display: -webkit-box;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 2;
          overflow: hidden;
        }
        @container (min-width: 600px) {
          .neo-stats { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        }
        .neo-list { display: flex; flex-direction: column; gap: 8px; padding: 0 12px 14px; }
        .neo-item {
          display: grid;
          grid-template-columns: auto minmax(0, 1fr);
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
        .neo-distance { grid-column: 2; font-size: 0.8rem; font-weight: 600; color: ${ASTRO.text1}; }
        @container (min-width: 450px) {
          .neo-item { grid-template-columns: auto minmax(0, 1fr) auto; }
          .neo-distance { grid-column: auto; text-align: right; }
        }
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
          <span class="astro-badge ${hazardousCount > 0 ? "danger" : ""}">${hazardousCount} potentially hazardous</span>
        </div>
        <div class="neo-context">
          <div>Approaches: ${esc(range)}</div>
          <div>${esc(sorter.label)} · Showing ${displayed.length} of ${totalCount}${this._config.show_hazardous_only ? " potentially hazardous objects" : " objects"}</div>
          <div>NASA's potentially hazardous classification is not an impact warning.</div>
        </div>
        ${this._config.show_stats !== false ? `
          <div class="astro-stat-grid neo-stats">
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
      cme_entity: "sensor.astronomy_space_suite_coronal_mass_ejections",
      flare_entity: "sensor.astronomy_space_suite_solar_flares",
      storm_entity: "sensor.astronomy_space_suite_geomagnetic_storms",
      kp_entity: "sensor.astronomy_space_suite_planetary_kp_index",
      forecast_entity: "sensor.astronomy_space_suite_space_weather_forecast",
      observing_entity: "sensor.astronomy_space_suite_observing_score",
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
      <ha-entity-picker id="forecast_entity" label="Space-weather forecast entity"></ha-entity-picker>
      <ha-entity-picker id="observing_entity" label="Observing forecast (local aurora conditions)"></ha-entity-picker>
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
    ["cme_entity", "flare_entity", "storm_entity", "kp_entity", "sdo_entity", "soho_entity", "forecast_entity", "observing_entity"].forEach((key) => this._bindPicker(key, key));
    this._bindText("title", "title", (value) => value.trim());
    ["show_cme", "show_flares", "show_storms", "show_kp_gauge", "show_live_sun", "show_sdo", "show_soho"].forEach((key) => this._bindSwitch(key, key));
    this._bindSelect("time_range", "time_range", (value) => (String(value) === "30" ? 30 : 7));
  }

  _syncValues() {
    ["cme_entity", "flare_entity", "storm_entity", "kp_entity", "sdo_entity", "soho_entity", "forecast_entity", "observing_entity"].forEach((key) => setPickerValue(this.shadowRoot, key, this._hass, this._config[key]));
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
  }

  static getConfigElement() { return document.createElement("solar-activity-card-editor"); }
  static getStubConfig() {
    return {
      cme_entity: "sensor.astronomy_space_suite_coronal_mass_ejections",
      flare_entity: "sensor.astronomy_space_suite_solar_flares",
      storm_entity: "sensor.astronomy_space_suite_geomagnetic_storms",
      kp_entity: "sensor.astronomy_space_suite_planetary_kp_index",
      forecast_entity: "sensor.astronomy_space_suite_space_weather_forecast",
      observing_entity: "sensor.astronomy_space_suite_observing_score",
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
  }

  set hass(hass) {
    if (updateCardHass(this, hass, configuredEntities(this._config), Math.floor(Date.now() / 60000))) this._render();
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
        ${INTELLIGENCE_STYLES}
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
        /* Same rule as .earth-frame img: SDO and SOHO publish square full-disc
           frames, so a fixed 4/3 box cropped ~25% of the disc (object-fit:
           cover) — the top and bottom of the Sun were sliced off. Size the tile
           to the image instead. The grid is auto-fit/minmax, so a taller square
           tile reflows without breaking the layout. */
        .live-sun-card img {
          display: block;
          width: 100%;
          height: auto;
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
        ${this._renderForecast()}
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

  _renderForecast() {
    const data=getState(this._hass,this._config.forecast_entity)?.attributes;
    if(!data) return "";
    const rows=safeArray(data.kp).filter(row=>row && parseDate(row.time) && finiteValue(row.kp,0,9)!==null).slice(-56);
    const first=rows.length?parseDate(rows[0].time).getTime():0;
    const span=rows.length?Math.max(1,parseDate(rows.at(-1).time).getTime()-first):1;
    const points=rows.map(row=>[20+(parseDate(row.time).getTime()-first)/span*280,110-row.kp/9*90,row]);
    const solar=safeArray(data.solar?.days)[0]||{};
    const aurora=finiteValue(data.aurora?.probability,0,100);
    const weather=safeArray(getState(this._hass,this._config.observing_entity)?.attributes?.forecast).find(row=>{
      const at=parseDate(row.time); return at && Math.abs(at.getTime()-(parseDate(data.aurora?.time)?.getTime()??0))<3600000;
    });
    const conditions=weather && finiteValue(weather.cloud_cover,0,100)!==null && finiteValue(weather.sun_altitude,-90,90)!==null;
    const guidance=aurora===null?"Aurora guidance unavailable":aurora<10?"Aurora unlikely from this location":!conditions?"Aurora may reach this location · Viewing conditions unknown":weather.sun_altitude>=-12?"Aurora activity · Too light to view":weather.cloud_cover>50?"Clouds may obscure aurora":weather.moon_interference>70?"Aurora possible · Bright moonlight":"Aurora plausibly observable";
    const months=safeArray(data.solar_cycle).slice(-12).filter(row=>row && typeof row.month==="string" && finiteValue(row.sunspots,0,1000)!==null && finiteValue(row.solar_flux_sfu,0,1000)!==null);
    const trend=months.length>1?`<svg viewBox="0 0 320 90" role="img" aria-label="Monthly sunspot number and solar radio flux, shared zero to maximum scale">${["sunspots","solar_flux_sfu"].map((field,index)=>{
      const maximum=Math.max(1,...months.flatMap(row=>[row.sunspots,row.solar_flux_sfu]));
      return `<polyline points="${months.map((row,i)=>`${20+i*280/(months.length-1)},${65-row[field]/maximum*50}`).join(" ")}" fill="none" stroke="${index?ASTRO.info:ASTRO.accent}" stroke-width="2"/>`;
    }).join("")}<text x="20" y="85">${esc(months[0].month)}</text><text x="300" y="85" text-anchor="end">${esc(months.at(-1).month)}</text></svg><div class="intel-copy">Monthly observations · <span style="color:${ASTRO.accent}">Sunspots</span> · <span style="color:${ASTRO.info}">Radio flux (sfu)</span></div>`:"";
    return `<div class="intel-panel"><div class="intel-row"><strong>Space weather · Forecast</strong><span class="intel-copy">${data.stale?"Cached data":"NOAA SWPC"}</span></div>
      ${points.length?`<svg viewBox="0 0 320 145" role="img" aria-label="Observed and predicted planetary Kp"><path d="M20 110H300M20 60H300" stroke="${ASTRO.divider}" stroke-dasharray="3 3"/><text x="0" y="63">5</text><text x="0" y="113">0</text>${points.slice(1).map(([x,y,row],index)=>`<path d="M${points[index][0]} ${points[index][1]}L${x} ${y}" fill="none" stroke="${row.kind==="predicted"?ASTRO.accent:ASTRO.info}" stroke-width="3" ${row.kind==="predicted"?'stroke-dasharray="4 3"':""}/>`).join("")}${points.map(([x,y,row])=>`<circle cx="${x}" cy="${y}" r="2" fill="${ASTRO.info}"><title>${esc(localStamp(this._hass,row.time))} · Kp ${row.kp} · ${esc(row.kind)}</title></circle>`).join("")}<text x="20" y="138">${esc(localStamp(this._hass,rows[0].time))}</text><text x="300" y="138" text-anchor="end">${esc(localStamp(this._hass,rows.at(-1).time))}</text></svg><div class="intel-copy">Solid: recent Kp · Dashed: forecast</div>`:'<div class="intel-copy">Kp forecast unavailable</div>'}
      <div class="intel-phases">${[["M-class",solar.m_class_probability],["X-class",solar.x_class_probability],["Radiation",solar.radiation_probability]].map(([label,value])=>`<div><strong>${finiteValue(value,0,100)??"—"}${finiteValue(value,0,100)===null?"":"%"}</strong><div class="intel-copy">${label} · First forecast day</div></div>`).join("")}</div>
      <div class="intel-targets">${["R","S","G"].map(scale=>{const value=finiteValue(safeArray(data.scales)[0]?.[scale],0,5);return `<span title="${scale==="R"?"Radio blackout":scale==="S"?"Radiation storm":"Geomagnetic storm"}">${scale}${value??"—"}</span>`;}).join("")}</div>
      <div class="intel-copy">${esc(guidance)}</div>
      ${trend}
      ${safeArray(data.solar_cycle).length?`<div class="intel-copy">Monthly solar trend · ${esc(data.solar_cycle.at(-1).month)} · ${finiteValue(data.solar_cycle.at(-1).sunspots,0,1000)??"—"} sunspots · ${finiteValue(data.solar_cycle.at(-1).solar_flux_sfu,0,1000)??"—"} sfu</div>`:""}
    </div>`;
  }
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
    if (updateCardHass(this, hass, [this._config.sun_entity])) this._render();
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
      intelligence_entity: "sensor.nasa_astronomy_ephemeris_moon_illumination_pct",
      title: "",
      show_next_phases: true,
      show_illumination: true,
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <ha-entity-picker id="moon_entity" label="Moon phase entity"></ha-entity-picker>
      <ha-entity-picker id="intelligence_entity" label="Moon intelligence (illumination entity)"></ha-entity-picker>
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <label class="switch-row"><span>Show next phases</span><ha-switch id="show_next_phases"></ha-switch></label>
      <label class="switch-row"><span>Show illumination</span><ha-switch id="show_illumination"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindPicker("moon_entity", "moon_entity");
    this._bindPicker("intelligence_entity", "intelligence_entity");
    this._bindText("title", "title", (value) => value.trim());
    ["show_next_phases", "show_illumination"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setPickerValue(this.shadowRoot, "moon_entity", this._hass, this._config.moon_entity || "sensor.moon_phase");
    setPickerValue(this.shadowRoot, "intelligence_entity", this._hass, this._config.intelligence_entity || "sensor.nasa_astronomy_ephemeris_moon_illumination_pct");
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
      intelligence_entity: "sensor.nasa_astronomy_ephemeris_moon_illumination_pct",
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
    if (updateCardHass(this, hass, configuredEntities(this._config))) this._render();
  }

  _render() {
    if (!this._hass) return;
    const stateObj = getState(this._hass, this._config.moon_entity);
    const intelligence = getState(this._hass, this._config.intelligence_entity);
    const details = intelligence?.attributes || {};
    if (!stateObj && !intelligence) {
      this.shadowRoot.innerHTML = renderErrorCard(`Entity not found: ${this._config.moon_entity}`);
      return;
    }

    const longitude = finiteValue(details.phase_longitude, 0, 360);
    const phase = longitude !== null ? MOON_PHASE_ORDER[Math.floor((longitude + 22.5) / 45) % 8] : normalizePhase(stateObj?.state);
    const phaseData = getMoonPhaseData(phase);
    const illumination = finiteValue(details.illumination_pct, 0, 100) ?? toNumber(stateObj?.attributes?.illumination, phaseData.illumination);
    if (longitude !== null) {
      phaseData.fraction = illumination / 100;
      phaseData.waxing = longitude < 180;
    }
    const currentIndex = MOON_PHASE_ORDER.indexOf(phase);
    const upcoming = [];
    if (this._config.show_next_phases !== false && safeArray(details.phases).length) {
      for (const item of details.phases.slice(0, 4)) {
        if (!parseDate(item.time)) continue;
        upcoming.push({ name: item.title, icon: MOON_ICONS[MOON_PHASE_ORDER[item.angle / 45]], time: item.time });
      }
    } else if (this._config.show_next_phases !== false && currentIndex >= 0) {
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
        ha-card { container-type: inline-size; }
        @container (max-width: 340px) { .lunar-next-grid { grid-template-columns: repeat(2,minmax(0,1fr)); } }
        ${INTELLIGENCE_STYLES}
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
                <span class="lunar-next-days">${item.time ? esc(localStamp(this._hass, item.time)) : `~${item.days}d`}</span>
              </div>
            `).join("")}
          </div>
        ` : ""}
        ${renderLunarIntelligence(details, this._hass)}
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
      show_uranus: false,
      show_neptune: false,
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
      <label class="switch-row"><span>Show Uranus</span><ha-switch id="show_uranus"></ha-switch></label>
      <label class="switch-row"><span>Show Neptune</span><ha-switch id="show_neptune"></ha-switch></label>
      <label class="switch-row"><span>Show stats</span><ha-switch id="show_stats"></ha-switch></label>
      <label class="switch-row"><span>Show date</span><ha-switch id="show_date"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindText("title", "title", (value) => value.trim());
    ["show_labels", "show_orbits", "show_mercury", "show_venus", "show_earth", "show_mars", "show_jupiter", "show_saturn", "show_uranus", "show_neptune", "show_stats", "show_date"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setTextValue(this.shadowRoot, "title", this._config.title || "");
    ["show_labels", "show_orbits", "show_mercury", "show_venus", "show_earth", "show_mars", "show_stats", "show_date"].forEach((key) => setSwitchValue(this.shadowRoot, key, this._config[key] !== false));
    setSwitchValue(this.shadowRoot, "show_jupiter", this._config.show_jupiter === true);
    setSwitchValue(this.shadowRoot, "show_saturn", this._config.show_saturn === true);
    setSwitchValue(this.shadowRoot, "show_uranus", this._config.show_uranus === true);
    setSwitchValue(this.shadowRoot, "show_neptune", this._config.show_neptune === true);
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
      show_uranus: false,
      show_neptune: false,
      show_stats: true,
      show_date: true,
    };
  }

  setConfig(config) {
    this._config = { ...SolarSystemCard.getStubConfig(), ...config };
  }

  set hass(hass) {
    if (updateCardHass(this, hass, [], Math.floor(Date.now() / 60000))) this._render();
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
    if (this._config.show_uranus === true) names.push("Uranus");
    if (this._config.show_neptune === true) names.push("Neptune");

    const positions = names.map((name) => calculatePlanetPosition(name, date));
    const compressed = names.includes("Uranus") || names.includes("Neptune");
    const maxOrbit = names.length > 0
      ? Math.max(...names.map((name) => PLANET_ELEMENTS[name].a * (compressed ? 1 + PLANET_ELEMENTS[name].e : 1))) * 1.06 : 1;
    const scale = radius / (compressed ? Math.sqrt(maxOrbit) : maxOrbit);
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
        .orrery-scale-note { display:flex; align-items:center; justify-content:center; gap:4px; padding-top:6px; font-size:0.7rem; color:${ASTRO.text2}; }
        .orrery-scale-note ha-icon { --mdc-icon-size:14px; }
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
              ${this._config.show_orbits !== false ? names.map((name) => `<path d="${buildOrbitPath(name, scale, center, 180, compressed)}" fill="none" stroke="${PLANET_ELEMENTS[name].color}" stroke-width="1.4" stroke-opacity="0.55"></path>`).join("") : ""}
              <circle cx="${center}" cy="${center}" r="22" fill="rgba(255,202,40,0.14)"></circle>
              <circle cx="${center}" cy="${center}" r="12" fill="#ffd54f"></circle>
              <circle cx="${center}" cy="${center}" r="5" fill="#fff9c4"></circle>
              ${positions.map((planet) => {
                const radialScale = compressed ? scale / Math.sqrt(planet.r) : scale;
                const px = center + planet.x * radialScale;
                const py = center + planet.y * radialScale;
                const pr = planet.name === "Mercury" ? 3.2 : planet.name === "Earth" ? 4.3 : planet.name === "Saturn" ? 5.2 : 4;
                const labelLeft = compressed && px > center + 100;
                const label = this._config.show_labels !== false
                  ? `<text x="${(px + (labelLeft ? -8 : 8)).toFixed(2)}" y="${(py - 8).toFixed(2)}" text-anchor="${labelLeft ? "end" : "start"}" fill="${planet.color}" font-size="10" font-weight="600">${planet.name}</text>`
                  : "";
                return `
                  <g data-planet="${planet.name}">
                    <circle cx="${px.toFixed(2)}" cy="${py.toFixed(2)}" r="${pr}" fill="${planet.color}"></circle>
                    <circle cx="${px.toFixed(2)}" cy="${py.toFixed(2)}" r="${(pr + 2).toFixed(1)}" fill="none" stroke="${planet.color}" stroke-opacity="0.35"></circle>
                    ${label}
                  </g>
                `;
              }).join("")}
            </svg>
          </div>
          ${compressed ? '<div class="orrery-scale-note"><ha-icon icon="mdi:arrow-collapse-horizontal"></ha-icon>Compressed spacing · not to scale</div>' : ""}
        </div>
        ${this._config.show_stats !== false ? `
          <div class="orrery-footer">
            ${positions.map((p) => `<span class="orrery-pill"><strong>${p.name}</strong>${p.r.toFixed(3)} AU</span>`).join("")}
            <span class="orrery-pill"><strong>Scale</strong>${compressed ? "Compressed" : "Heliocentric"}</span>
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
      entity_prefix: "sensor.astronomy_space_suite_rocket_launch",
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
    this._bindText("entity_prefix", "entity_prefix", (value) => value.trim() || "sensor.astronomy_space_suite_rocket_launch");
    this._bindText("title", "title", (value) => value.trim());
    this._bindText("max_launches", "max_launches", (value) => clamp(parseInt(value, 10) || 5, 1, 5));
    ["show_countdown", "show_weather", "show_tags"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setTextValue(this.shadowRoot, "entity_prefix", this._config.entity_prefix || "sensor.astronomy_space_suite_rocket_launch");
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
      entity_prefix: "sensor.astronomy_space_suite_rocket_launch",
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
    const prefix = this._config.entity_prefix || "sensor.astronomy_space_suite_rocket_launch";
    const count = clamp(parseInt(this._config.max_launches, 10) || 5, 1, 5);
    const entities = Array.from({ length: count }, (_, index) => `${prefix}_${index + 1}`);
    if (updateCardHass(this, hass, entities, Math.floor(Date.now() / 60000))) this._render();
  }

  _parseLaunch(stateObj, fallbackName) {
    const attrs = stateObj.attributes || {};
    // Only ever parse attributes that hold a timestamp. The entity state is the
    // mission name ("EOS-05 (ISRO)") and must never be fed to a date parser.
    const launchDate = parseDate(
      attrs.launch_target || attrs.t0 || attrs.win_open || attrs.window_start
      || attrs.net || attrs.target_date || attrs.launch_date || attrs.datetime,
    );
    const padLocation = [
      attrs.launch_pad,
      attrs.pad_name,
      attrs.location_name,
      attrs.pad?.name,
      attrs.pad?.location?.name,
      typeof attrs.pad === "string" ? attrs.pad : null,
      attrs.launch_location,
      typeof attrs.location === "string" ? attrs.location : null,
    ].map((value) => (typeof value === "string" ? value.trim() : value))
      .find((value) => value && value !== "()") || "Location TBD";
    const tags = [
      ...(safeArray(attrs.tags).map((tag) => (typeof tag === "string" ? tag : tag?.name || tag?.text)).filter(Boolean)),
      ...(typeof attrs.tags === "string" ? attrs.tags.split("|").map((tag) => tag.trim()).filter(Boolean) : []),
      attrs.mission_type,
      attrs.orbit,
      attrs.status,
    ].filter(Boolean);
    // Human-readable date that is NOT a parsed timestamp (e.g. "Sep 03"), used
    // when the provider has not published a T-0 yet.
    const approximateDate = [attrs.date_str, attrs.window_start, attrs.net]
      .find((value) => typeof value === "string" && value.trim());
    return {
      mission: attrs.mission_name || attrs.name || attrs.mission || attrs.friendly_name || fallbackName,
      provider: attrs.provider || attrs.launch_service_provider || attrs.agency || attrs.organization || "Provider TBD",
      vehicle: attrs.vehicle || attrs.rocket || attrs.rocket_name || attrs.launcher || "Vehicle TBD",
      padLocation,
      countdown: launchDate ? formatCountdown(launchDate) : "Date TBD",
      dateLabel: launchDate ? formatDateTime(launchDate) : (approximateDate ? `${approximateDate} (estimated)` : "Date TBD"),
      weather: this._formatWeather(attrs),
      tags: [...new Set(tags)].slice(0, 4),
      media: attrs.media_link || attrs.video_url || attrs.stream_url || attrs.webcast || attrs.url || "",
      within24h: launchDate ? isWithinHours(launchDate, 24) : false,
      launchDate,
    };
  }

  _formatWeather(attrs) {
    const metric = !String(this._hass?.config?.unit_system?.temperature || "°C").toUpperCase().includes("F");
    const parts = [];
    if (attrs.weather_condition) parts.push(String(attrs.weather_condition));

    const tempC = toNumber(attrs.weather_temp_c, NaN);
    const tempF = toNumber(attrs.weather_temp_f, NaN);
    if (metric && Number.isFinite(tempC)) parts.push(`${Math.round(tempC)} °C`);
    else if (Number.isFinite(tempF)) parts.push(`${Math.round(tempF)} °F`);
    else if (Number.isFinite(tempC)) parts.push(`${Math.round(tempC)} °C`);

    const windKph = toNumber(attrs.weather_wind_kph, NaN);
    const windMph = toNumber(attrs.weather_wind_mph, NaN);
    if (metric && Number.isFinite(windKph)) parts.push(`Wind ${Math.round(windKph)} km/h`);
    else if (Number.isFinite(windMph)) parts.push(`Wind ${Math.round(windMph)} mph`);
    else if (Number.isFinite(windKph)) parts.push(`Wind ${Math.round(windKph)} km/h`);

    if (parts.length) return parts.join(" · ");

    // Fallback for older integration versions: only show the provider's summary
    // when it is not a bare unit-less reading such as "Temp: 79".
    const summary = attrs.weather_summary || attrs.launch_weather || attrs.weather || "";
    const text = String(summary).replace(/\s*\n\s*/g, " · ").replace(/\s*·\s*$/, "").trim();
    if (!text || text === "TBD") return "";
    return /(?:^|[^A-Za-z])Temp:\s*-?\d+(?:\.\d+)?(?![°\dCFcf])/.test(text) ? "" : text;
  }

  _render() {
    if (!this._hass) return;
    const prefix = this._config.entity_prefix || "sensor.astronomy_space_suite_rocket_launch";
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
      entity: "sensor.astronomy_space_suite_iss_position",
      title: "ISS Tracker",
      stream_url: "https://www.youtube.com/nasa/live",
      show_map: true,
      show_trail: true,
      show_stream_button: true,
      map_zoom: 0,
      trail_hours: 6,
      mode: "iss",
      satellite_entities: "",
      ...config,
    });
  }

  _editorTemplate() {
    return `
      <ha-entity-picker id="entity" label="ISS position entity"></ha-entity-picker>
      <div class="astro-input-wrap"><label for="mode">Tracker mode</label><select id="mode"><option value="iss">ISS</option><option value="satellites">Selected satellites</option></select></div>
      <div class="astro-input-wrap"><label for="satellite_entities">Satellite entity IDs (comma separated, maximum 8)</label><input id="satellite_entities" type="text"/></div>
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <div class="astro-input-wrap"><label for="stream_url">ISS livestream URL</label><input type="text" id="stream_url" /></div>
      <div class="astro-input-wrap"><label for="map_zoom">Map zoom level (0-18)</label><input type="number" id="map_zoom" min="0" max="18" /></div>
      <div class="astro-input-wrap"><label for="trail_hours">Trail history (hours)</label><input type="number" id="trail_hours" min="1" max="24" /></div>
      <label class="switch-row"><span>Show map</span><ha-switch id="show_map"></ha-switch></label>
      <label class="switch-row"><span>Show trail</span><ha-switch id="show_trail"></ha-switch></label>
      <label class="switch-row"><span>Show stream button</span><ha-switch id="show_stream_button"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindPicker("entity", "entity");
    this._bindSelect("mode", "mode");
    this._bindText("satellite_entities", "satellite_entities", value=>value.trim());
    this._bindText("title", "title", (value) => value.trim());
    this._bindText("stream_url", "stream_url", (value) => value.trim());
    this._bindText("map_zoom", "map_zoom", (value) => clamp(parseInt(value, 10) || 0, 0, 18));
    this._bindText("trail_hours", "trail_hours", (value) => clamp(parseInt(value, 10) || 6, 1, 24));
    ["show_map", "show_trail", "show_stream_button"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setPickerValue(this.shadowRoot, "entity", this._hass, this._config.entity || "sensor.astronomy_space_suite_iss_position");
    setSelectValue(this.shadowRoot, "mode", this._config.mode || "iss");
    setTextValue(this.shadowRoot, "satellite_entities", this._config.satellite_entities || "");
    setTextValue(this.shadowRoot, "title", this._config.title || "ISS Tracker");
    setTextValue(this.shadowRoot, "stream_url", this._config.stream_url || "https://www.youtube.com/nasa/live");
    setTextValue(this.shadowRoot, "map_zoom", String(this._config.map_zoom ?? 0));
    setTextValue(this.shadowRoot, "trail_hours", String(this._config.trail_hours ?? 6));
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
    this._nativeMap = null;
    this._nativeMapConfig = "";
    this._nativeMapToken = 0;
    this._nativeMapResizeObserver = null;
    this._nativeMapResizeFrame = 0;
  }

  static getConfigElement() { return document.createElement("iss-tracker-card-editor"); }
  static getStubConfig() {
    return {
      entity: "sensor.astronomy_space_suite_iss_position",
      title: "ISS Tracker",
      stream_url: "https://www.youtube.com/nasa/live",
      show_map: true,
      show_trail: true,
      show_stream_button: true,
      map_zoom: 0,
      trail_hours: 6,
      mode: "iss",
      satellite_entities: "",
    };
  }

  setConfig(config) {
    this._config = { ...IssTrackerCard.getStubConfig(), ...config };
  }

  set hass(hass) {
    if (updateCardHass(this, hass, this._satelliteEntities())) this._render();
    else if (this._nativeMap && this._displayPosition) {
      this._nativeMap.hass = this._mapHass(this._displayPosition, this._mapIsStale);
    }
  }

  disconnectedCallback() {
    this._nativeMapResizeObserver?.disconnect();
    this._nativeMapResizeObserver = null;
    if (this._nativeMapResizeFrame) {
      cancelAnimationFrame(this._nativeMapResizeFrame);
      this._nativeMapResizeFrame = 0;
    }
  }

  _satelliteEntities() {
    if(this._config.mode!=="satellites") return [this._config.entity];
    const extra=Array.isArray(this._config.satellite_entities)?this._config.satellite_entities:String(this._config.satellite_entities||"").split(",");
    return [...new Set([this._config.entity,...extra.map(value=>String(value).trim()).filter(value=>/^sensor\.[a-z0-9_]+$/.test(value))])].slice(0,8);
  }

  _entityId() {
    const entities=this._satelliteEntities();
    return entities.includes(this._selectedSatellite)?this._selectedSatellite:entities[0];
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
    let ts = attrs.timestamp || stateObj?.last_changed || stateObj?.last_updated || "";
    if (typeof ts === "number" && ts < 9999999999) ts = ts * 1000;
    return {
      latitude,
      longitude,
      timestamp: ts,
      liveStreamUrl: this._config.stream_url || attrs.live_stream_url || "https://www.youtube.com/nasa/live",
    };
  }

  _mapHass(displayPos, isStale) {
    if (!isStale) return this._hass;
    const entityId = this._entityId();
    const current = getState(this._hass, entityId);
    const currentLatitude = toNumber(current?.attributes?.latitude, NaN);
    const currentLongitude = toNumber(current?.attributes?.longitude, NaN);
    if (Number.isFinite(currentLatitude) && Number.isFinite(currentLongitude)) {
      return this._hass;
    }
    const timestampValue = displayPos.timestamp || Date.now();
    const timestamp = typeof timestampValue === "number"
      ? new Date(timestampValue < 9999999999 ? timestampValue * 1000 : timestampValue).toISOString()
      : timestampValue;
    const fallbackKey = `${entityId}:${displayPos.latitude}:${displayPos.longitude}:${timestamp}`;
    if (this._fallbackMapHass && this._fallbackMapKey === fallbackKey) {
      return this._fallbackMapHass;
    }
    const fallbackState = {
      ...(current || {}),
      entity_id: entityId,
      state: `${displayPos.latitude}, ${displayPos.longitude}`,
      attributes: {
        ...(current?.attributes || {}),
        latitude: displayPos.latitude,
        longitude: displayPos.longitude,
        friendly_name: current?.attributes?.friendly_name || "ISS Position",
      },
      last_changed: current?.last_changed || timestamp,
      last_updated: current?.last_updated || timestamp,
    };
    const mapHass = {
      ...this._hass,
      states: { ...this._hass.states, [entityId]: fallbackState },
    };
    this._fallbackMapHass = mapHass;
    this._fallbackMapKey = fallbackKey;
    return mapHass;
  }

  async _renderNativeMap(displayPos, isStale) {
    this._displayPosition = displayPos;
    this._mapIsStale = isStale;
    const container = this.shadowRoot.querySelector("#iss-native-map");
    if (!container) return;
    if (typeof window.loadCardHelpers !== "function") {
      container.textContent = "Home Assistant map renderer is unavailable.";
      container.classList.add("iss-map-error");
      return;
    }

    const mapConfig = {
      type: "map",
      show_all: false,
      entities: [{
        entity: this._entityId(),
        name: getState(this._hass,this._entityId())?.attributes?.name || "ISS",
        label_mode: "icon",
      }],
      hours_to_show: this._config.show_trail === false ? 0 : (this._config.trail_hours ?? 6),
      default_zoom: this._config.map_zoom ?? 0,
      auto_fit: true,
      fit_zones: true,
      theme_mode: "dark",
      scale_ruler: true,
      aspect_ratio: "16:9",
    };
    const mapHass = this._mapHass(displayPos, isStale);
    const serialized = JSON.stringify(mapConfig);
    if (this._nativeMap && this._nativeMapConfig === serialized) {
      this._styleNativeMap(this._nativeMap);
      this._nativeMap.hass = mapHass;
      this._observeNativeMap(container);
      return;
    }

    const token = ++this._nativeMapToken;
    try {
      const helpers = await window.loadCardHelpers();
      if (token !== this._nativeMapToken) return;
      const mapCard = helpers.createCardElement(mapConfig);
      mapCard.layout = "grid";
      mapCard.hass = mapHass;
      mapCard.style.display = "block";
      mapCard.style.width = "100%";
      mapCard.style.height = "100%";
      mapCard.style.setProperty("--ha-card-border-width", "0px");
      mapCard.style.setProperty("--ha-card-border-radius", "18px");
      this._styleNativeMap(mapCard);
      container.replaceChildren(mapCard);
      this._nativeMap = mapCard;
      this._nativeMapConfig = serialized;
      this._observeNativeMap(container);
    } catch (error) {
      container.textContent = `Map unavailable: ${error?.message || error}`;
      container.classList.add("iss-map-error");
    }
  }

  _styleNativeMap(mapCard) {
    for (const property of ["--ha-card-background", "--card-background-color"]) {
      if (this._config.glass_mode === true) {
        mapCard.style.setProperty(property, "transparent");
      } else {
        mapCard.style.removeProperty(property);
      }
    }
  }

  _observeNativeMap(container) {
    if (typeof ResizeObserver !== "function") return;
    if (this._nativeMapResizeContainer === container && this._nativeMapResizeObserver) return;
    this._nativeMapResizeObserver?.disconnect();
    this._nativeMapResizeContainer = container;
    this._nativeMapResizeObserver = new ResizeObserver(() => {
      if (this._nativeMapResizeFrame) cancelAnimationFrame(this._nativeMapResizeFrame);
      this._nativeMapResizeFrame = requestAnimationFrame(() => {
        this._nativeMapResizeFrame = requestAnimationFrame(() => {
          this._nativeMapResizeFrame = 0;
          const map = this._nativeMap?.shadowRoot?.querySelector("ha-map");
          map?.fitMap?.({ unpause_autofit: true });
        });
      });
    });
    this._nativeMapResizeObserver.observe(container);
  }

  async _render() {
    if (!this._hass) return;
    const stateObj = getState(this._hass, this._entityId());
    const position = this._parsePosition(stateObj);
    const posValid = Number.isFinite(position.latitude) && Number.isFinite(position.longitude);

    const cacheKey = `astronomy-cards:iss-last-pos:${this._entityId() || "default"}`;
    if (posValid) {
      try { localStorage.setItem(cacheKey, JSON.stringify({ latitude: position.latitude, longitude: position.longitude, timestamp: position.timestamp })); } catch (_) {}
    }

    let displayPos = position;
    let isStale = stateObj?.attributes?.stale === true;
    if (!posValid) {
      try {
        const cached = JSON.parse(localStorage.getItem(cacheKey) || "null");
        if (cached && Number.isFinite(cached.latitude) && Number.isFinite(cached.longitude)) {
          displayPos = { ...position, latitude: cached.latitude, longitude: cached.longitude, timestamp: cached.timestamp };
          isStale = true;
        }
      } catch (_) {}
    }

    if (!stateObj || (!Number.isFinite(displayPos.latitude) || !Number.isFinite(displayPos.longitude))) {
      this.shadowRoot.innerHTML = renderErrorCard("Satellite position unavailable. Enable selected satellites in integration options.", "mdi:space-station");
      return;
    }

    // Only do full DOM rebuild if structure doesn't exist yet
    if (!this.shadowRoot.querySelector(".astro-card")) {
      this.shadowRoot.innerHTML = `
        <style>
          ${BASE_STYLES}
          ${INTELLIGENCE_STYLES}
          .iss-body {
            padding: 0 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            container-type: inline-size;
          }
          .iss-map-container {
            border-radius: 18px;
            overflow: hidden;
            height: clamp(240px, 56.25cqw, 360px);
            min-height: 240px;
            position: relative;
            box-shadow: inset 0 0 0 1px rgba(0,0,0,0.06);
          }
          #iss-native-map { width: 100%; height: 100%; min-height: 240px; }
          .iss-map-error {
            min-height: 240px; display: grid; place-items: center; padding: 16px;
            color: ${ASTRO.error}; background: rgba(var(--rgb-error-color, 244,67,54), 0.08);
          }
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
            display: inline-flex; align-items: center; gap: 6px; padding: 9px 14px;
            border-radius: 999px; text-decoration: none;
            background: rgba(var(--rgb-error-color, 244,67,54), 0.12);
            color: ${ASTRO.error}; font-size: 0.78rem; font-weight: 700;
          }
          .iss-stale-banner {
            padding: 6px 12px; border-radius: 8px; font-size: 0.75rem; font-weight: 500;
            background: rgba(var(--rgb-warning-color, 255,152,0), 0.12);
            color: var(--warning-color, #ff9800); text-align: center;
          }
          :host([glass-mode]) .iss-map-container,
          :host([glass-mode]) .iss-stat {
            background: transparent;
            box-shadow: none;
          }
          @container (max-width: 360px) {
            .iss-map-container { height: 220px; min-height: 220px; border-radius: 14px; }
            #iss-native-map, .iss-map-error { min-height: 220px; }
            .iss-grid { grid-template-columns: 1fr; }
            .iss-footer { align-items: stretch; }
            .iss-button { justify-content: center; }
          }
        </style>
        <ha-card class="astro-card">
          <div class="astro-header">
            <ha-icon icon="mdi:space-station"></ha-icon>
            <span class="astro-title">${esc(this._config.title || "ISS Tracker")}</span>
            <span class="astro-badge iss-badge"></span>
          </div>
          <div class="iss-body">
            <div class="iss-selector"></div>
            <div class="iss-stale-banner" style="display:none"></div>
            ${this._config.show_map !== false ? `<div class="iss-map-container"><div id="iss-native-map"></div></div>` : ""}
            <div class="iss-grid">
              <div class="iss-stat"><div class="iss-stat-label">Latitude</div><div class="iss-stat-value iss-lat"></div></div>
              <div class="iss-stat"><div class="iss-stat-label">Longitude</div><div class="iss-stat-value iss-lon"></div></div>
            </div>
            <div class="iss-pass"></div>
            <div class="iss-footer">
              <div class="iss-time"></div>
              ${this._config.show_stream_button !== false ? `<a class="iss-button iss-stream-link" href="${esc(displayPos.liveStreamUrl)}" target="_blank" rel="noopener">Live Stream ↗</a>` : ""}
            </div>
          </div>
        </ha-card>
      `;
    }

    // Update dynamic values
    const badge = this.shadowRoot.querySelector(".iss-badge");
    if (badge) badge.textContent = isStale ? "Last known" : "Live orbit";

    const staleBanner = this.shadowRoot.querySelector(".iss-stale-banner");
    if (staleBanner) {
      staleBanner.style.display = isStale ? "block" : "none";
      staleBanner.textContent = isStale ? "⚠ Position data unavailable — showing last known location" : "";
    }

    const latEl = this.shadowRoot.querySelector(".iss-lat");
    const lonEl = this.shadowRoot.querySelector(".iss-lon");
    if (latEl) latEl.textContent = `${displayPos.latitude.toFixed(4)}°`;
    if (lonEl) lonEl.textContent = `${displayPos.longitude.toFixed(4)}°`;

    const timeEl = this.shadowRoot.querySelector(".iss-time");
    if (timeEl) timeEl.textContent = isStale ? "⚠ Last known position" : `Updated ${formatDateTime(displayPos.timestamp)}`;
    const selector = this.shadowRoot.querySelector(".iss-selector");
    if(selector && this._config.mode==="satellites") {
      const markup=`<select class="intel-select" aria-label="Select satellite">${this._satelliteEntities().map(id=>`<option value="${esc(id)}" ${id===this._entityId()?"selected":""}>${esc(getState(this._hass,id)?.attributes?.name || getState(this._hass,id)?.attributes?.friendly_name || id)}</option>`).join("")}</select>`;
      if(this._selectorMarkup!==markup) {
        this._selectorMarkup=markup; selector.innerHTML=markup;
        selector.querySelector("select")?.addEventListener("change",event=>{
          this._selectedSatellite=event.target.value; this._render();
        });
      }
    }
    const passHost=this.shadowRoot.querySelector(".iss-pass");
    const passes=stateObj?.attributes?.passes;
    const trail=stateObj?.attributes?.ground_track;
    if(passHost && (this._passesInput!==passes || this._trailInput!==trail)) {
      this._passesInput=passes;
      this._trailInput=trail;
      const next=safeArray(passes).find(pass=>pass && parseDate(pass.end)?.getTime()>Date.now());
      const visibility=next?.observer_dark===false?"Daylight pass":next?.sunlit===false?"Spacecraft in shadow":next?.observer_dark===true && next?.sunlit===true?"Potentially visible":next?.visibility||"Visibility unknown";
      const track=safeArray(trail).slice(0,60).filter(point=>point && finiteValue(point.latitude,-90,90)!==null && finiteValue(point.longitude,-180,180)!==null);
      const ground=track.length>1?`<div class="intel-panel"><svg viewBox="0 0 360 180" role="img" aria-label="Locally propagated satellite ground track"><image href="/local/community/astronomy-cards/world-map.png" width="360" height="180" opacity=".5"/>${track.slice(1).map((point,index)=>{
        const previous=track[index];
        return Math.abs(point.longitude-previous.longitude)>180?"":`<path d="M${previous.longitude+180} ${90-previous.latitude}L${point.longitude+180} ${90-point.latitude}" stroke="${ASTRO.accent}" stroke-width="2" fill="none"/>`;
      }).join("")}</svg><div class="intel-copy">Predicted ground track · From ${esc(localStamp(this._hass,track[0].time))}</div></div>`:"";
      passHost.innerHTML=ground+(next?`<div class="intel-panel"><div class="intel-row"><strong>Next pass</strong><span class="intel-copy">${esc(visibility)}</span></div>${renderSkyPath(next.sky_path,"Next satellite pass sky path")}<div class="intel-copy">${esc(localStamp(this._hass,next.start))}–${esc(localStamp(this._hass,next.end,false))} · Peak ${finiteValue(next.max_elevation,0,90)??"—"}°</div><div class="intel-copy">${next.clipped?"Window clipped · ":""}Brightness and weather may limit visibility</div></div>`:Array.isArray(passes)?'<div class="intel-panel"><div class="intel-copy">No passes above 10° in this forecast</div></div>':"");
    }
    const stream=this.shadowRoot.querySelector(".iss-stream-link");
    if(stream) stream.style.display=this._entityId()===this._config.entity?"":"none";

    if (this._config.show_map !== false) {
      await this._renderNativeMap(displayPos, isStale);
    }
  }

  getCardSize() { return this._config.show_map === false ? 3 : 6; }
}

class EarthObservationCardEditor extends AstroEditorBase {
  setConfig(config) {
    super.setConfig({
      epic_entity: "camera.astronomy_space_suite_epic_earth",
      goes_entity: "camera.astronomy_space_suite_goes_16_earth",
      goes18_entity: "camera.astronomy_space_suite_goes_18_earth",
      himawari_entity: "camera.astronomy_space_suite_himawari_8_earth",
      meteosat_entity: "camera.astronomy_space_suite_meteosat_12_earth",
      sdo_entity: "camera.astronomy_space_suite_sdo_sun",
      soho_entity: "camera.astronomy_space_suite_soho_sun",
      title: "Earth Observation",
      show_epic: true,
      show_goes: true,
      default_view: "epic",
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
      <ha-entity-picker id="meteosat_entity" label="Meteosat-12 camera entity"></ha-entity-picker>
      <ha-entity-picker id="sdo_entity" label="SDO sun camera entity"></ha-entity-picker>
      <ha-entity-picker id="soho_entity" label="SOHO sun camera entity"></ha-entity-picker>
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" placeholder="Leave empty for default" /></div>
      <div class="astro-input-wrap"><label for="refresh_interval">Refresh interval (minutes)</label><input type="number" id="refresh_interval" min="1" max="60" /></div>
      <div class="astro-input-wrap"><label for="default_view">Default view</label><select id="default_view">
        <option value="epic">EPIC</option>
        <option value="goes">GOES-16</option>
        <option value="goes18">GOES-18</option>
        <option value="himawari">Himawari</option>
        <option value="meteosat">Meteosat-12</option>
        <option value="sdo">SDO</option>
        <option value="soho">SOHO</option>
      </select></div>
      <label class="switch-row"><span>Show EPIC</span><ha-switch id="show_epic"></ha-switch></label>
      <label class="switch-row"><span>Show GOES-16</span><ha-switch id="show_goes"></ha-switch></label>
    `;
  }

  _setupListeners() {
    ["epic_entity", "goes_entity", "goes18_entity", "himawari_entity", "meteosat_entity", "sdo_entity", "soho_entity"].forEach((key) => this._bindPicker(key, key));
    this._bindText("title", "title", (value) => value.trim());
    this._bindText("refresh_interval", "refresh_interval", (value) => clamp(parseInt(value, 10) || 5, 1, 60));
    this._bindSelect("default_view", "default_view");
    ["show_epic", "show_goes"].forEach((key) => this._bindSwitch(key, key));
  }

  _syncValues() {
    setPickerValue(this.shadowRoot, "epic_entity", this._hass, this._config.epic_entity || "camera.astronomy_space_suite_epic_earth");
    setPickerValue(this.shadowRoot, "goes_entity", this._hass, this._config.goes_entity || "camera.astronomy_space_suite_goes_16_earth");
    setPickerValue(this.shadowRoot, "goes18_entity", this._hass, this._config.goes18_entity || "camera.astronomy_space_suite_goes_18_earth");
    setPickerValue(this.shadowRoot, "himawari_entity", this._hass, this._config.himawari_entity || "camera.astronomy_space_suite_himawari_8_earth");
    setPickerValue(this.shadowRoot, "meteosat_entity", this._hass, this._config.meteosat_entity || "camera.astronomy_space_suite_meteosat_12_earth");
    setPickerValue(this.shadowRoot, "sdo_entity", this._hass, this._config.sdo_entity || "camera.astronomy_space_suite_sdo_sun");
    setPickerValue(this.shadowRoot, "soho_entity", this._hass, this._config.soho_entity || "camera.astronomy_space_suite_soho_sun");
    setTextValue(this.shadowRoot, "title", this._config.title || "Earth Observation");
    setTextValue(this.shadowRoot, "refresh_interval", this._config.refresh_interval || 5);
    setSelectValue(this.shadowRoot, "default_view", this._config.default_view || "epic");
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
    this._defaultApplied = false;
    this._refreshHandle = 0;
    this._refreshToken = Date.now();
  }

  static getConfigElement() { return document.createElement("earth-observation-card-editor"); }
  static getStubConfig() {
    return {
      epic_entity: "camera.astronomy_space_suite_epic_earth",
      goes_entity: "camera.astronomy_space_suite_goes_16_earth",
      goes18_entity: "camera.astronomy_space_suite_goes_18_earth",
      himawari_entity: "camera.astronomy_space_suite_himawari_8_earth",
      meteosat_entity: "camera.astronomy_space_suite_meteosat_12_earth",
      sdo_entity: "camera.astronomy_space_suite_sdo_sun",
      soho_entity: "camera.astronomy_space_suite_soho_sun",
      title: "Earth Observation",
      show_epic: true,
      show_goes: true,
      default_view: "epic",
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
    if (!this._defaultApplied) {
      this._activeView = this._config.default_view;
      this._defaultApplied = true;
    }
    this._selectDefaultView();
    this._ensureRefreshTimer();
  }

  set hass(hass) {
    if (!updateCardHass(this, hass, configuredEntities(this._config))) return;
    this._selectDefaultView();
    this._render();
  }

  _getViews() {
    return [
      { key: "epic", title: "EPIC", group: "earth", entityId: this._config.epic_entity, enabled: this._config.show_epic !== false, fallbackSource: "NASA EPIC", fallbackDetail: "Daily Earth imagery from NASA EPIC." },
      { key: "goes", title: "GOES-16", group: "earth", entityId: this._config.goes_entity, enabled: this._config.show_goes !== false, fallbackSource: "NOAA GOES-16", fallbackDetail: "Geostationary Earth observation imagery." },
      { key: "goes18", title: "GOES-18", group: "earth", entityId: this._config.goes18_entity, enabled: true, fallbackSource: "NOAA GOES-18", fallbackDetail: "Pacific geostationary Earth observation imagery." },
      { key: "himawari", title: "Himawari", group: "earth", entityId: this._config.himawari_entity, enabled: true, fallbackSource: "Himawari-8", fallbackDetail: "Asia-Pacific Earth observation imagery." },
      { key: "meteosat", title: "Meteosat-12", group: "earth", entityId: this._config.meteosat_entity, enabled: true, fallbackSource: "EUMETSAT / NASA", fallbackDetail: "GeoColour RGB full-disc imagery of Europe and Africa." },
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
      source: attrs.attribution || attrs.source_info || attrs.source || view.fallbackSource,
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
        .earth-tab-row {
          display: flex;
          gap: 8px;
          flex: 1;
          min-width: 0;
          overflow-x: auto;
          overscroll-behavior-x: contain;
          scrollbar-width: thin;
          padding-bottom: 2px;
        }
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
          aspect-ratio: 1 / 1;
          border-radius: 18px;
          overflow: hidden;
          background: #000;
          box-shadow: inset 0 0 0 1px rgba(var(--rgb-primary-text-color, 0,0,0), 0.06);
          line-height: 0;
        }
        .earth-frame img {
          display: block;
          width: 100%;
          height: 100%;
          object-fit: contain;
          background: #000;
        }
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

const INTELLIGENCE_STYLES = `
  ha-card { display:block; container-type:inline-size; }
  .intel-panel { margin:0 12px 12px; padding:12px; border-radius:14px; background:${ASTRO.chipBg}; color:${ASTRO.text1}; min-width:0; }
  .intel-row { display:flex; flex-wrap:wrap; gap:8px; align-items:center; justify-content:space-between; }
  .intel-copy { font-size:.78rem; color:${ASTRO.text2}; line-height:1.5; overflow-wrap:anywhere; }
  .intel-panel strong { font-size:.86rem; font-weight:600; }
  .intel-panel svg { display:block; width:100%; height:auto; overflow:visible; }
  .intel-panel svg text { fill:${ASTRO.text2}; font:12px sans-serif; }
  .intel-tabs { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:12px; }
  .intel-tabs button, .intel-select { font:inherit; font-size:.75rem; color:${ASTRO.text1}; background:${ASTRO.chipBg}; border:1px solid ${ASTRO.divider}; border-radius:16px; padding:6px 10px; max-width:100%; }
  .intel-tabs button[aria-pressed="true"] { color:${ASTRO.accent}; border-color:${ASTRO.accent}; }
  .intel-scroll { overflow-x:auto; overscroll-behavior:contain; padding:4px 0; }
  .intel-scroll svg { min-width:700px; }
  .intel-score { display:flex; align-items:center; gap:12px; }
  .intel-score svg { width:90px; flex:none; }
  .intel-status { color:var(--intel-status); font-weight:700; }
  .intel-phases { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:8px; text-align:center; margin-top:12px; }
  .intel-targets { display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; }
  .intel-targets span { font-size:.72rem; color:${ASTRO.text2}; padding:5px 8px; background:${ASTRO.chipBg}; border-radius:12px; }
  @container (max-width:340px) { .intel-phases { grid-template-columns:1fr; text-align:left; } .intel-score { gap:6px; } }
  @media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation:none!important; transition:none!important; } }
`;

function finiteValue(value, min = -Infinity, max = Infinity) {
  if (value == null || value === "" || typeof value === "boolean") return null;
  const number = Number(value);
  return Number.isFinite(number) && number >= min && number <= max ? number : null;
}

function localStamp(hass, value, date = true) {
  const parsed = parseDate(value);
  if (!parsed) return "Time unavailable";
  return new Intl.DateTimeFormat(hass?.locale?.language || undefined, {
    timeZone: hass?.config?.time_zone || "UTC",
    ...(hass?.locale?.time_format === "24" ? {hourCycle:"h23"} : hass?.locale?.time_format === "12" ? {hourCycle:"h12"} : {}),
    ...(date ? { month:"short", day:"numeric" } : {}),
    hour:"2-digit", minute:"2-digit",
  }).format(parsed);
}

function statusColor(score) {
  return score == null ? ASTRO.text2 : score >= 70 ? ASTRO.success : score >= 40 ? ASTRO.warning : ASTRO.error;
}

function renderLunarIntelligence(details, hass) {
  const distance = finiteValue(details.distance_km, 300000, 450000);
  if (distance === null) return "";
  const marker = 20 + clamp((distance - 356000) / 51000, 0, 1) * 260;
  const angular = finiteValue(details.angular_diameter_arcmin, 25, 40);
  const impact = finiteValue(details.moonlight_impact, 0, 100);
  const path = safeArray(details.sky_path).slice(0,25).filter(point=>point && parseDate(point.time) && finiteValue(point.altitude,-90,90)!==null);
  return `<div class="intel-panel">
    <div class="intel-row"><strong>${Math.round(distance).toLocaleString()} km</strong><span class="intel-copy">${finiteValue(details.age_days,0,31) ?? "—"} days old</span></div>
    <svg viewBox="0 0 300 60" role="img" aria-label="Moon distance, scale 356,000 to 407,000 kilometres">
      <path d="M20 25H280" stroke="${ASTRO.divider}" stroke-width="6" stroke-linecap="round"/>
      <circle cx="${marker}" cy="25" r="7" fill="${ASTRO.accent}"/>
      <text x="20" y="52">356,000 km</text><text x="280" y="52" text-anchor="end">407,000 km</text>
    </svg>
    <div class="intel-copy">Perigee ${esc(localStamp(hass, details.perigee?.time))} · Apogee ${esc(localStamp(hass, details.apogee?.time))}</div>
    ${path.length>1?`<svg viewBox="0 0 300 110" role="img" aria-label="Moon altitude over the next 24 hours, horizon at the dashed line"><path d="M20 55H280" stroke="${ASTRO.divider}" stroke-dasharray="3 3"/><polyline points="${path.map((point,index)=>`${20+260*index/(path.length-1)},${55-point.altitude/90*40}`).join(" ")}" fill="none" stroke="${ASTRO.accent}" stroke-width="3"/>${path.map((point,index)=>`<circle cx="${20+260*index/(path.length-1)}" cy="${55-point.altitude/90*40}" r="2" fill="${point.altitude>=0?ASTRO.info:ASTRO.text2}"><title>${esc(localStamp(hass,point.time))} · ${point.altitude}°</title></circle>`).join("")}<text x="20" y="104">${esc(localStamp(hass,path[0].time,false))}</text><text x="280" y="104" text-anchor="end">${esc(localStamp(hass,path.at(-1).time,false))} +1 day</text></svg>`:""}
    <div class="intel-phases">${[["Next rise",details.rise_time],["Next transit",details.transit_time],["Next set",details.set_time]].map(([label,time]) => `<div><strong>${esc(localStamp(hass,time,false))}</strong><div class="intel-copy">${label}</div></div>`).join("")}</div>
    ${angular === null ? "" : `<div class="intel-row"><svg viewBox="0 0 150 55" style="max-width:150px" role="img" aria-label="Apparent Moon diameter ${angular} arcminutes compared with 30 arcminutes"><circle cx="35" cy="27" r="20" fill="none" stroke="${ASTRO.divider}" stroke-dasharray="3 3"/><circle cx="35" cy="27" r="${20*angular/30}" fill="${ASTRO.text2}" opacity=".5"/><text x="70" y="30">${angular.toFixed(1)} arcmin</text></svg><span class="intel-copy">Dashed: 30 arcmin</span></div>`}
    ${impact === null ? "" : `<div class="intel-copy">Moonlight impact ${impact}% ${impact > 50 ? "· Lower deep-sky contrast" : ""}</div>`}
  </div>`;
}

function renderSkyPath(points, title = "Sky path") {
  const valid = safeArray(points).slice(0, 30).filter(point => finiteValue(point.altitude,0,90) !== null && finiteValue(point.azimuth,0,360) !== null);
  if (!valid.length) return "";
  const projected = valid.map(point => {
    const radius = 90 * (1 - point.altitude / 90);
    const angle = point.azimuth * Math.PI / 180;
    return [110 + radius * Math.sin(angle), 110 - radius * Math.cos(angle)];
  });
  return `<svg viewBox="0 0 220 220" style="max-width:220px;margin:auto" role="img" aria-label="${esc(title)}">
    <title>${esc(title)} · zenith at centre, north at top</title>
    <circle cx="110" cy="110" r="90" fill="none" stroke="${ASTRO.divider}"/>
    <circle cx="110" cy="110" r="45" fill="none" stroke="${ASTRO.divider}" stroke-dasharray="3 3"/>
    <text x="110" y="13" text-anchor="middle">N</text><text x="210" y="114">E</text><text x="110" y="218" text-anchor="middle">S</text><text x="1" y="114">W</text>
    <polyline points="${projected.map(pair => pair.join(",")).join(" ")}" fill="none" stroke="${ASTRO.accent}" stroke-width="3"/>
    ${projected.map(([x,y],index) => `<circle cx="${x}" cy="${y}" r="${index===0?5:2}" fill="${ASTRO.info}"/>`).join("")}
  </svg>`;
}

class ObservationPlannerEditor extends AstroEditorBase {
  setConfig(config) { super.setConfig({...ObservationPlannerCard.getStubConfig(),...config}); }
  _editorTemplate() {
    return `<ha-entity-picker id="entity" label="Observing score entity"></ha-entity-picker>
      <div class="astro-input-wrap"><label for="title">Card title</label><input id="title" type="text"/></div>
      <div class="astro-input-wrap"><label for="mode">Observing style</label><select id="mode"><option value="stargazing">Stargazing</option><option value="deep_sky">Visual deep sky</option><option value="astrophotography">Astrophotography</option></select></div>
      <div class="astro-input-wrap"><label for="hours">Forecast hours</label><input id="hours" type="number" min="24" max="48"/></div>
      <label class="switch-row"><span>Show targets</span><ha-switch id="show_targets"></ha-switch></label>`;
  }
  _setupListeners() {
    this._bindPicker("entity","entity"); this._bindText("title","title");
    this._bindSelect("mode","mode"); this._bindText("hours","hours",value=>clamp(parseInt(value,10)||48,24,48)); this._bindSwitch("show_targets","show_targets");
  }
  _syncValues() {
    setPickerValue(this.shadowRoot,"entity",this._hass,this._config.entity);
    setTextValue(this.shadowRoot,"title",this._config.title);
    setSelectValue(this.shadowRoot,"mode",this._config.mode); setTextValue(this.shadowRoot,"hours",this._config.hours);
    setSwitchValue(this.shadowRoot,"show_targets",this._config.show_targets!==false);
  }
}

class ObservationPlannerCard extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:"open"}); this._config = {}; }
  static getConfigElement() { return document.createElement("observation-planner-card-editor"); }
  static getStubConfig() { return {entity:"sensor.astronomy_space_suite_observing_score",title:"Observation Planner",mode:"stargazing",hours:48,show_targets:true}; }
  setConfig(config) { this._config = {...ObservationPlannerCard.getStubConfig(),...config}; }
  set hass(hass) { if(updateCardHass(this,hass,[this._config.entity])) this._render(); }
  _render() {
    const state = getState(this._hass,this._config.entity);
    const data = state?.attributes || {};
    const mode = ["stargazing","deep_sky","astrophotography"].includes(this._config.mode) ? this._config.mode : "stargazing";
    if (this._series !== data.forecast || this._seriesHours !== this._config.hours) {
      this._series = data.forecast; this._seriesHours = this._config.hours;
      this._rows = safeArray(data.forecast).slice(0,clamp(Number(this._config.hours)||48,24,48)).filter(row=>row && parseDate(row.time));
    }
    const rows = this._rows;
    const score = rows.length ? finiteValue(rows[0].scores?.[mode],0,100) : null;
    const window = data.windows?.[mode] || (mode === "stargazing" ? data.best_window : null);
    const width = 680 / Math.max(1,rows.length);
    const targets = safeArray(data.targets).slice(0,5).filter(target=>target && parseDate(target.peak));
    const targetRibbon = this._config.show_targets!==false && window && mode==="stargazing" && targets.length ? `<svg viewBox="0 0 800 ${35+targets.length*28}" role="img" aria-label="Best Tonight target peaks within the highlighted observing window"><text x="0" y="16">Target peaks</text>${targets.map((target,index)=>{
      const hour=(parseDate(target.peak).getTime()-parseDate(rows[0]?.time).getTime())/3600000;
      const x=clamp(100+(hour+.5)*width,100,780), y=38+index*28;
      return `<path d="M100 ${y}H780" stroke="${ASTRO.divider}"/><circle cx="${x}" cy="${y}" r="5" fill="${ASTRO.accent}"><title>${esc(target.name)} · ${esc(localStamp(this._hass,target.peak))} · ${finiteValue(target.altitude,0,90)??"—"}°</title></circle><text x="${x<500?x+10:x-10}" y="${y+4}" text-anchor="${x<500?"start":"end"}">${esc(target.name)}</text>`;
    }).join("")}</svg>`:"";
    const strips = [
      ["Clouds", row=>finiteValue(row.cloud_cover,0,100), true],
      ["Low", row=>finiteValue(row.cloud_cover_low,0,100), true],
      ["Mid", row=>finiteValue(row.cloud_cover_mid,0,100), true],
      ["High", row=>finiteValue(row.cloud_cover_high,0,100), true],
      ["Seeing*", row=>finiteValue(row.seeing_estimate,0,100), false],
      ["Clarity*", row=>finiteValue(row.transparency_estimate,0,100), false],
      ["Moonlight", row=>finiteValue(row.moon_interference,0,100), true],
    ];
    const ribbon = rows.length ? `<div class="intel-scroll" tabindex="0" aria-label="Scrollable hourly observing forecast"><svg viewBox="0 0 800 275" role="img" aria-label="Hourly darkness, cloud layers, seeing, clarity and moonlight">
      ${rows.map((row,index)=>{
        const x=100+index*width;
        const value=finiteValue(row.scores?.[mode],0,100);
        const good=window && row.time>=window.start && row.time<window.end;
        const sun=finiteValue(row.sun_altitude,-90,90);
        return `<rect x="${x}" y="20" width="${width}" height="30" fill="${sun===null?ASTRO.divider:row.astronomical_darkness===true ? "#151d39" : sun < -6 ? "#5c6bc0" : "#ffc107"}" opacity=".8"><title>${esc(localStamp(this._hass,row.time))} · ${sun===null?"Unknown darkness":row.astronomical_darkness ? "Dark sky" : "Twilight or daylight"}</title></rect>
          <rect x="${x}" y="58" width="${width-1}" height="25" fill="${statusColor(value)}" opacity="${good?1:.55}"><title>${value===null?"Unknown":value+"/100"} · ${esc(row.limiting_factor)}</title></rect>
          ${good?`<path d="M${x} 89h${width}" stroke="${ASTRO.success}" stroke-width="4"/>`:""}
          ${index%4===0?`<text x="${x}" y="14">${esc(localStamp(this._hass,row.time,false))}</text>`:""}`;
      }).join("")}
      <text x="0" y="39">Darkness</text><text x="0" y="76">Quality</text>
      ${strips.map(([label,get,inverse],line)=>`<text x="0" y="${111+line*22}">${label}</text>${rows.map((row,index)=>{
        const value=get(row), severity=value===null?null:inverse?value:100-value;
        return `<rect x="${100+index*width}" y="${98+line*22}" width="${width-1}" height="17" rx="2" fill="${severity===null?ASTRO.divider:severity>70?ASTRO.warning:ASTRO.info}" opacity="${severity===null?.3:.2+severity/125}"><title>${esc(localStamp(this._hass,row.time))} · ${label}: ${value===null?"Unknown":value+"%"}</title></rect>`;
      }).join("")}`).join("")}
      ${rows.map((row,index)=>(finiteValue(row.fog_risk,0,100)>=50 || finiteValue(row.wind_gusts_10m,0,150)>=10 || finiteValue(row.precipitation_probability,0,100)>=50)?`<text x="${100+index*width}" y="265" fill="${ASTRO.warning}">!<title>Wind, fog or rain risk</title></text>`:"").join("")}
    </svg>${targetRibbon}</div>`:"";
    this.shadowRoot.innerHTML=`<style>${BASE_STYLES}${INTELLIGENCE_STYLES}</style><ha-card class="astro-card">
      <div class="astro-header"><ha-icon icon="mdi:telescope"></ha-icon><span class="astro-title">${esc(this._config.title)}</span>${data.stale?'<span class="astro-badge warn">Cached forecast</span>':""}</div>
      <div class="intel-panel">
        <div class="intel-score" style="--intel-status:${statusColor(score)}"><svg viewBox="0 0 100 100" role="img" aria-label="${score===null?"Observing quality unknown":score+" out of 100"}"><circle cx="50" cy="50" r="40" fill="none" stroke="${ASTRO.divider}" stroke-width="7"/><circle cx="50" cy="50" r="40" fill="none" stroke="${statusColor(score)}" stroke-width="7" stroke-dasharray="${(score??0)*2.513} 251.3" transform="rotate(-90 50 50)"/><text x="50" y="57" text-anchor="middle" style="font-size:24px;fill:${ASTRO.text1}">${score??"—"}</text></svg>
          <div><strong class="intel-status">${score===null?"Forecast unavailable":score>=70?"GO":score>=40?"MARGINAL":"NO-GO"}</strong><div class="intel-copy">${score===null?"Enable observing conditions in integration options.":esc(rows[0].limiting_factor)}</div>
          <div class="intel-copy">${window?`Best viewing: ${esc(localStamp(this._hass,window.start))}–${esc(localStamp(this._hass,window.end,false))}`:"No clear viewing window"}</div></div>
        </div>${ribbon}
        ${rows.length?'<div class="intel-copy">*Seeing and clarity are estimates · Open-Meteo · Hourly forecast</div>':""}
        ${this._config.show_targets!==false?safeArray(data.targets).slice(0,5).map(target=>`<div class="intel-targets"><span>${esc(target.name)} · ${esc(localStamp(this._hass,target.peak,false))} · ${finiteValue(target.altitude,0,90)??"—"}°</span></div>`).join(""):""}
      </div></ha-card>`;
  }
  getCardSize() { return 5; }
}

function defineElement(name, ctor) {
  if (customElements.get(name)) return;
  if (!name.endsWith("-editor") && typeof ctor.prototype.setConfig === "function") {
    const setConfig = ctor.prototype.setConfig;
    ctor.prototype.setConfig = function setCardConfig(config) {
      if (typeof this.toggleAttribute === "function") {
        this.toggleAttribute("glass-mode", config?.glass_mode === true);
      }
      return setConfig.call(this, config);
    };
  }
  customElements.define(name, ctor);
}

function registerCustomCard(type, name, description) {
  window.customCards = window.customCards || [];
  if (!window.customCards.some((card) => card.type === type)) {
    window.customCards.push({ type, name, description, preview: false, documentationURL: DOCS_URL });
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
defineElement("observation-planner-card-editor", ObservationPlannerEditor);
defineElement("observation-planner-card", ObservationPlannerCard);
registerCustomCard("observation-planner-card", "ASS Observation Planner", "Darkness, weather and best viewing windows with editor");

// ─── Night Sky Highlights Card ───────────────────────────────────────────────
class NightSkyHighlightsEditor extends AstroEditorBase {
  _editorTemplate() {
    return `
      <div class="astro-input-wrap"><label for="title">Card title</label><input type="text" id="title" /></div>
      <label class="switch-row"><span>Telescope Mode (alt &gt; 30°)</span><ha-switch id="telescope_mode"></ha-switch></label>
      <label class="switch-row"><span>Show upcoming eclipses</span><ha-switch id="show_eclipses"></ha-switch></label>
      <ha-entity-picker id="events_entity" label="Celestial events entity"></ha-entity-picker>
      <label class="switch-row"><span>Show celestial events</span><ha-switch id="show_events"></ha-switch></label>
    `;
  }

  _setupListeners() {
    this._bindText("title", "title");
    this._bindSwitch("telescope_mode", "telescope_mode");
    this._bindSwitch("show_eclipses", "show_eclipses");
    this._bindPicker("events_entity", "events_entity");
    this._bindSwitch("show_events", "show_events");
  }

  _syncValues() {
    setTextValue(this.shadowRoot, "title", this._config.title || "Night Sky Highlights");
    setSwitchValue(this.shadowRoot, "telescope_mode", this._config.telescope_mode === true);
    setSwitchValue(this.shadowRoot, "show_eclipses", this._config.show_eclipses !== false);
    setPickerValue(this.shadowRoot, "events_entity", this._hass, this._config.events_entity || "sensor.astronomy_space_suite_next_celestial_event");
    setSwitchValue(this.shadowRoot, "show_events", this._config.show_events !== false);
  }
}

class NightSkyHighlightsCard extends HTMLElement {
  static getConfigElement() { return document.createElement("night-sky-highlights-card-editor"); }
  static getStubConfig() { return { title: "Night Sky Highlights", telescope_mode: false, show_eclipses: true, show_events: true, events_entity: "sensor.astronomy_space_suite_next_celestial_event" }; }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  setConfig(config) {
    this._config = { ...NightSkyHighlightsCard.getStubConfig(), ...config };
  }

  set hass(hass) {
    const bodies = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune"];
    const entities = bodies.flatMap((body) => ["altitude", "illumination_pct", "phase_angle", "visibility_start", "visibility_end"]
      .map((suffix) => `sensor.nasa_astronomy_ephemeris_${body}_${suffix}`));
    entities.push("sensor.nasa_astronomy_ephemeris_sky_twilight_phase");
    if (this._config.show_events !== false) entities.push(this._config.events_entity);
    if (this._config.show_eclipses !== false) {
      entities.push("sensor.nasa_astronomy_ephemeris_eclipses_solar", "sensor.nasa_astronomy_ephemeris_eclipses_lunar");
    }
    if (updateCardHass(this, hass, entities, Math.floor(Date.now() / 60000))) this._render();
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

  _eclipseIcon(type, kind, index) {
    const solar = type === "solar";
    const id = `nsh-eclipse-${type}-${index}`;
    const base = solar ? "#ffd166" : "#cbd5e1";
    const shadow = solar ? "#182033" : "#a94b43";
    const disc = kind === "total" ? shadow : base;
    return `<svg class="nsh-eclipse-icon" viewBox="0 0 48 48" role="img" aria-label="${kind} ${type} eclipse illustration">
      <title>Schematic eclipse illustration, not a sky map</title>
      <defs><clipPath id="${id}"><circle cx="24" cy="24" r="17"/></clipPath></defs>
      ${solar && kind === "total" ? '<circle cx="24" cy="24" r="20" fill="none" stroke="#ffd166" stroke-width="2" opacity="0.6"/>' : ""}
      <circle cx="24" cy="24" r="17" fill="${disc}"/>
      ${kind === "annular" ? `<circle cx="24" cy="24" r="14" fill="${shadow}"/>` : ""}
      ${kind === "partial" ? `<circle cx="35" cy="17" r="17" fill="${shadow}" clip-path="url(#${id})"/>` : ""}
      ${kind === "penumbral" ? `<circle cx="31" cy="20" r="22" fill="#64748b" opacity="0.3" clip-path="url(#${id})"/>` : ""}
    </svg>`;
  }

  _renderEclipses() {
    if (this._config.show_eclipses === false) return "";
    const timeZone = this._hass.config?.time_zone || "UTC";
    const formatter = new Intl.DateTimeFormat(this._hass.locale?.language || undefined, {
      timeZone, year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
    const stamp = (value) => {
      const date = parseDate(value);
      return date ? esc(formatter.format(date)) : "Unknown";
    };
    const shortDate = (value) => {
      const date = parseDate(value);
      return date ? esc(date.toLocaleDateString(this._hass.locale?.language || undefined, {
        timeZone, day: "numeric", month: "short", year: "numeric",
      })) : "Unknown";
    };
    const states = ["solar", "lunar"].map((type) =>
      getState(this._hass, `sensor.nasa_astronomy_ephemeris_eclipses_${type}`));
    const metadata = states.find((state) => state && !["unknown", "unavailable"].includes(state.state))?.attributes || {};
    const latitude = metadata.latitude == null ? NaN : toNumber(metadata.latitude, NaN);
    const longitude = metadata.longitude == null ? NaN : toNumber(metadata.longitude, NaN);
    const location = Number.isFinite(latitude) && Number.isFinite(longitude)
      ? `${latitude.toFixed(2)}, ${longitude.toFixed(2)}` : "Location unavailable";
    const now = Date.now();
    return `
      <div class="nsh-eclipses">
        <div class="nsh-section-title">Upcoming Eclipses</div>
        <div class="nsh-eclipse-meta">
          <span><ha-icon icon="mdi:map-marker-outline"></ha-icon>${esc(location)}</span>
          <span><ha-icon icon="mdi:clock-outline"></ha-icon>${esc(timeZone)}</span>
        </div>
        ${["solar", "lunar"].map((type, typeIndex) => {
          const state = states[typeIndex];
          const title = type === "solar" ? "Solar" : "Lunar";
          if (!state || ["unknown", "unavailable"].includes(state.state)) {
            return `<div class="nsh-eclipse-empty" title="Update the integration and enable ephemeris sensors."><ha-icon icon="mdi:cloud-off-outline"></ha-icon>${title}: eclipse data unavailable</div>`;
          }
          const attrs = state.attributes || {};
          const events = safeArray(attrs.events).filter((event) => {
            const end = parseDate(event.visible_end || event.end);
            return !end || end.getTime() > now;
          });
          const horizon = toNumber(attrs.horizon_months, NaN);
          return `
            <div class="nsh-eclipse-heading"><strong><ha-icon icon="${type === "solar" ? "mdi:white-balance-sunny" : "mdi:moon-full"}"></ha-icon>${title}</strong>
              <span class="nsh-moon-label">${Number.isFinite(horizon) ? horizon + " months · " : ""}Until ${shortDate(attrs.search_end)}</span>
            </div>
            ${events.length ? events.slice(0, 3).map((event, index) => {
              const begin = parseDate(event.visible_begin);
              const end = parseDate(event.visible_end);
              const visibleNow = begin && end && now >= begin.getTime() && now < end.getTime();
              const coverage = event.obscuration_pct == null ? NaN : toNumber(event.obscuration_pct, NaN);
              const duration = event.duration_minutes == null ? NaN : toNumber(event.duration_minutes, NaN);
              const kinds = { total: "Total", partial: "Partial", annular: "Annular", penumbral: "Penumbral" };
              const kind = Object.hasOwn(kinds, event.kind) ? kinds[event.kind] : "Unknown type";
              return `<div class="nsh-eclipse">
                <div class="nsh-eclipse-main">
                  ${this._eclipseIcon(type, kind.toLowerCase(), index)}
                  <div class="nsh-eclipse-copy">
                    <strong>${kind} ${type} eclipse</strong>
                    <div class="nsh-moon-label">${stamp(event.peak)}</div>
                    <div class="nsh-eclipse-meta">
                      ${visibleNow ? '<span class="nsh-eclipse-live"><ha-icon icon="mdi:eye-outline"></ha-icon>Visible now</span>' : ""}
                      ${event.peak_visible === false ? '<span><ha-icon icon="mdi:eye-off-outline"></ha-icon>Peak below horizon</span>' : ""}
                      ${Number.isFinite(duration) ? `<span title="Full eclipse duration${type === "lunar" ? ", including penumbral phases" : ""}"><ha-icon icon="mdi:timer-outline"></ha-icon>${duration.toFixed(0)} min</span>` : ""}
                    </div>
                  </div>
                  <div class="nsh-eclipse-coverage" title="${type === "solar" ? "Sun covered" : "Moon in Earth's umbra"} at peak${event.peak_visible === false ? " (below horizon)" : ""}">
                    <strong>${Number.isFinite(coverage) ? coverage.toFixed(1) + "%" : "—"}</strong>
                    <span>${type === "solar" ? "covered" : "umbra"}</span>
                  </div>
                </div>
                <details class="nsh-eclipse-details">
                  <summary><ha-icon icon="mdi:information-outline"></ha-icon>Details</summary>
                  <div class="nsh-moon-label">Above horizon: ${stamp(event.visible_begin)} – ${stamp(event.visible_end)}</div>
                  ${event.kind === "penumbral" ? '<div class="nsh-moon-label">Penumbral shading only; no part of the Moon enters the umbra.</div>' : ""}
                  ${event.central_begin && event.central_end ? `<div class="nsh-moon-label">${event.kind === "annular" ? "Annular" : "Total"} phase: ${stamp(event.central_begin)} – ${stamp(event.central_end)}</div>` : ""}
                  <div class="nsh-moon-label">Illustration is schematic. Coverage is at peak, which may be below your horizon.</div>
                </details>
              </div>`;
            }).join("") : `<div class="nsh-eclipse-empty" title="No locally visible ${type} eclipses in this search window."><ha-icon icon="mdi:calendar-check-outline"></ha-icon>None in this window</div>`}
          `;
        }).join("")}
        <div class="nsh-eclipse-meta">
          <span title="Up to 3 locally visible events per type. Geometric horizon only; weather, terrain and refraction are not included."><ha-icon icon="mdi:eye-outline"></ha-icon>Horizon only</span>
          <span title="For solar viewing, use certified eclipse glasses or proper solar filters."><ha-icon icon="mdi:alert-outline"></ha-icon>Solar protection required</span>
        </div>
      </div>`;
  }

  _renderEvents() {
    if(this._config.show_events===false) return "";
    const state=getState(this._hass,this._config.events_entity);
    if(!state) return "";
    const input=state.attributes?.events;
    if(this._eventArray!==input || !this._events) {
      this._eventArray=input;
      this._events=safeArray(input).filter(event=>event && parseDate(event.peak) && parseDate(event.end)).slice(0,48);
    }
    const events=this._events.filter(event=>parseDate(event.end).getTime()>Date.now());
    const filtered=events.filter(event=>!this._eventFilter || event.event_type===this._eventFilter);
    const next=filtered[0];
    if(!next) return `<div class="intel-panel"><div class="intel-copy">No upcoming events in this category</div>${this._eventTabs()}</div>`;
    const display=filtered.slice(0,6);
    const first=parseDate(display[0].peak).getTime();
    const span=Math.max(DAY_MS,parseDate(display.at(-1).peak).getTime()-first);
    const altitude=finiteValue(next.altitude_at_peak,-90,90), azimuth=finiteValue(next.azimuth_at_peak,0,360);
    const remaining=Math.max(0,Math.ceil((parseDate(next.peak).getTime()-Date.now())/DAY_MS));
    const visibility={
      above_horizon_in_darkness:"Above horizon in darkness",below_horizon_or_daylight:"Peak below horizon or in daylight",
      global_event:"Seasonal turning point",radiant_rises:"Radiant rises at your location",radiant_below_horizon:"Radiant stays below your horizon",
      above_horizon:"Locally visible",partial_window_only:"Part of the eclipse is above your horizon",
    };
    return `<div class="intel-panel">${this._eventTabs()}<div class="intel-row"><strong>${esc(next.title)}</strong><span class="astro-badge">${remaining?`${remaining}d`:"Peaking today"}</span></div>
      ${altitude!==null && altitude>=0 && azimuth!==null?renderSkyPath([{altitude,azimuth}],`${next.title} position at peak`):`<svg viewBox="0 0 300 70" role="img" aria-label="${esc(next.title)} event timing"><path d="M20 35H280" stroke="${ASTRO.divider}" stroke-width="4"/><circle cx="150" cy="35" r="14" fill="${ASTRO.accent}"/><text x="150" y="40" text-anchor="middle" style="fill:white">${next.event_type==="season"?"☀":"◉"}</text></svg>`}
      <div class="intel-copy">Peak: ${esc(localStamp(this._hass,next.peak))}${next.peak_estimate?" · Calendar estimate":""}</div>
      <div class="intel-copy">${esc(visibility[next.visibility_from_location]||"Visibility unknown")}${altitude!==null?` · ${altitude}° at peak`:""}</div>
      ${finiteValue(next.moon_interference,0,100)!==null?`<div class="intel-copy">Moon ${next.moon_interference}% illuminated · Ideal rate up to ${finiteValue(next.expected_rate,0,1000)??"—"}/h</div>`:""}
      ${next.best_viewing && parseDate(next.best_viewing.time)?`<div class="intel-copy">Best local hour: ${esc(localStamp(this._hass,next.best_viewing.time))} · Radiant ${finiteValue(next.best_viewing.altitude,0,90)??"—"}°</div><svg viewBox="0 0 300 28" role="img" aria-label="Moonlight interference during the best local meteor viewing hour"><rect x="0" y="8" width="300" height="8" rx="4" fill="${ASTRO.divider}"/><rect x="0" y="8" width="${3*(finiteValue(next.best_viewing.moon_interference,0,100)??0)}" height="8" rx="4" fill="${ASTRO.warning}"/><title>Moonlight interference ${finiteValue(next.best_viewing.moon_interference,0,100)??"unknown"}%</title></svg>`:""}
      <svg viewBox="0 0 320 60" role="img" aria-label="Upcoming celestial event timeline"><path d="M20 20H300" stroke="${ASTRO.divider}" stroke-width="3"/>${display.map(event=>`<circle cx="${20+(parseDate(event.peak).getTime()-first)/span*280}" cy="20" r="5" fill="${ASTRO.accent}"><title>${esc(event.title)} · ${esc(localStamp(this._hass,event.peak))}</title></circle>`).join("")}<text x="20" y="50">${esc(localStamp(this._hass,display[0].peak))}</text><text x="300" y="50" text-anchor="end">${esc(localStamp(this._hass,display.at(-1).peak))}</text></svg>
    </div>`;
  }

  _eventTabs() {
    return `<div class="intel-tabs">${[["","Upcoming"],["meteor_shower","Showers"],["opposition","Oppositions"],["elongation","Elongations"]].map(([key,label])=>`<button type="button" data-event-filter="${key}" aria-pressed="${(this._eventFilter||"")===key}">${label}</button>`).join("")}</div>`;
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
        .nsh-eclipses { display:flex; flex-direction:column; gap:8px; min-width:0; }
        .nsh-eclipse-heading { display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:4px 10px; margin-top:6px; }
        .nsh-eclipse-heading strong { display:flex; align-items:center; gap:5px; color:${ASTRO.text1}; }
        .nsh-eclipse-heading ha-icon { --mdc-icon-size:18px; }
        .nsh-eclipse { padding:10px; border-radius:14px; background:rgba(var(--rgb-primary-text-color,0,0,0),0.04); overflow-wrap:anywhere; }
        .nsh-eclipse strong { color:${ASTRO.text1}; font-size:0.85rem; }
        .nsh-eclipse-main { display:flex; align-items:center; gap:8px; }
        .nsh-eclipse-icon { width:44px; height:44px; flex:none; }
        .nsh-eclipse-copy { flex:1; min-width:0; }
        .nsh-eclipse-coverage { display:flex; flex-direction:column; align-items:center; flex:none; }
        .nsh-eclipse-coverage strong { font-size:1rem; }
        .nsh-eclipse-coverage span { font-size:0.65rem; color:${ASTRO.text2}; }
        .nsh-eclipse-meta { display:flex; flex-wrap:wrap; gap:4px 10px; font-size:0.7rem; color:${ASTRO.text2}; }
        .nsh-eclipse-meta span { display:inline-flex; align-items:center; gap:3px; }
        .nsh-eclipse-meta ha-icon, .nsh-eclipse-empty ha-icon, .nsh-eclipse-details ha-icon { --mdc-icon-size:14px; }
        .nsh-eclipse-live { color:#66bb6a; }
        .nsh-eclipse-empty { display:flex; align-items:center; gap:5px; padding:4px 0; color:${ASTRO.text2}; font-size:0.78rem; }
        .nsh-eclipse-details { margin-top:6px; }
        .nsh-eclipse-details summary { width:fit-content; cursor:pointer; color:${ASTRO.text2}; font-size:0.7rem; }
        .nsh-eclipse-details .nsh-moon-label { margin-top:4px; }
        ${INTELLIGENCE_STYLES}
      </style>
      <ha-card class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:telescope"></ha-icon>
          <span class="astro-title">${esc(this._config.title || "Night Sky Highlights")}</span>
          ${isDark ? '<span class="nsh-badge nsh-badge-dark">Dark Sky</span>' : sunAlt !== null ? '<span class="nsh-badge nsh-badge-light">Daylight</span>' : ''}
        </div>
        <div class="nsh-body">
          ${this._renderEvents()}
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
          ${this._renderEclipses()}
        </div>
      </ha-card>
    `;
    this.shadowRoot.querySelectorAll("[data-event-filter]").forEach(button=>button.addEventListener("click",()=>{
      this._eventFilter=button.dataset.eventFilter; this._render();
    }));
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
registerCustomCard("earth-observation-card", "ASS Earth Observation Card", "EPIC, GOES, Himawari and Meteosat Earth imagery viewer with editor");
registerCustomCard("night-sky-highlights-card", "ASS Night Sky Highlights Card", "Best visible objects tonight based on ephemeris with editor");

console.info(
  "%c Astronomy Space Suite Cards v1.19.1 %c",
  "color:white;background:#1a237e;font-weight:bold;padding:2px 8px;border-radius:4px 0 0 4px;",
  "color:#1a237e;background:#e8eaf6;font-weight:bold;padding:2px 8px;border-radius:0 4px 4px 0;",
);
