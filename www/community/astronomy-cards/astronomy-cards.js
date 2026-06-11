/**
 * NASA Astronomy Cards v1.2.5
 * Pre-built bundle - place in /config/www/community/astronomy-cards/
 *
 * Cards: <apod-card>, <neo-threat-card>, <solar-activity-card>,
 *        <astro-horizon-card>, <astro-lunar-card>
 * All cards feature:
 *  - Visual UI config editor (no YAML needed)
 *  - Full light/dark mode support via HA CSS variables
 *  - Mushroom-aligned design language
 */

// ============================================================
// SHARED THEME - Uses HA CSS custom properties for light/dark
// ============================================================
const ASTRO = {
  // All colors reference HA theme variables so they auto-adapt
  radius: "var(--ha-card-border-radius, 12px)",
  shadow: "var(--ha-card-box-shadow, none)",
  surface: "var(--ha-card-background, var(--card-background-color, white))",
  text1: "var(--primary-text-color)",
  text2: "var(--secondary-text-color)",
  bg2: "var(--card-background-color, var(--secondary-background-color))",
  divider: "var(--divider-color)",
  // Mushroom-style chip/badge background
  chipBg: "rgba(var(--rgb-primary-text-color, 0,0,0), 0.05)",
  // Status colors from HA theme
  success: "var(--success-color, #4caf50)",
  warning: "var(--warning-color, #ff9800)",
  error: "var(--error-color, #f44336)",
  info: "var(--info-color, #42a5f5)",
  // Accent from HA theme
  accent: "var(--accent-color, #7c4dff)",
  stateIcon: "var(--state-icon-color, #7c4dff)",
  // Category colors (work well in both modes)
  cme: "#ff6b35",
  flare: "#ffc107",
  storm: "#ab47bc",
  neo: "var(--info-color, #42a5f5)",
};

// Shared base styles - Mushroom-inspired, HA theme adaptive
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

// Shared config editor styles
const EDITOR_STYLES = `
  :host { display: block; }
  .editor { padding: 16px; }
  .editor ha-entity-picker,
  .editor ha-textfield,
  .editor ha-switch,
  .editor ha-formfield { display: block; margin-bottom: 12px; }
  .editor label { display:flex; align-items:center; gap:8px; margin-bottom:12px; font-size:0.9rem; color:var(--primary-text-color); }
`;

// Helper: escape HTML
function esc(str) { const d = document.createElement("div"); d.textContent = str || ""; return d.innerHTML; }

// ============================================================
// APOD CARD CONFIG EDITOR
// ============================================================
class ApodCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  setConfig(config) { this._config = { ...config }; this._render(); }

  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;
    this.shadowRoot.innerHTML = `
      <style>${EDITOR_STYLES}</style>
      <div class="editor">
        <ha-entity-picker
          .hass=${null}
          label="APOD Entity"
          value="${this._config.entity || ""}"
          id="entity"
        ></ha-entity-picker>
        <label>
          <ha-switch id="show_explanation" ${this._config.show_explanation !== false ? "checked" : ""}></ha-switch>
          Show Explanation
        </label>
        <label>
          <ha-switch id="show_copyright" ${this._config.show_copyright !== false ? "checked" : ""}></ha-switch>
          Show Copyright
        </label>
        <label>
          <ha-switch id="show_hd_link" ${this._config.show_hd_link ? "checked" : ""}></ha-switch>
          Show HD Link
        </label>
      </div>
    `;

    // Wire up entity picker
    const picker = this.shadowRoot.getElementById("entity");
    picker.hass = this._hass;
    picker.addEventListener("value-changed", (e) => {
      this._config = { ...this._config, entity: e.detail.value };
      this._dispatch();
    });

    // Wire up switches
    ["show_explanation", "show_copyright", "show_hd_link"].forEach(key => {
      const sw = this.shadowRoot.getElementById(key);
      sw.addEventListener("change", (e) => {
        this._config = { ...this._config, [key]: e.target.checked };
        this._dispatch();
      });
    });
  }

  _dispatch() {
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
  }
}
customElements.define("apod-card-editor", ApodCardEditor);

// ============================================================
// APOD CARD
// ============================================================
class ApodCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  static getConfigElement() { return document.createElement("apod-card-editor"); }

  static getStubConfig() {
    return { entity: "sensor.nasa_astronomy_suite_apod", show_explanation: true, show_copyright: true, show_hd_link: false };
  }

  setConfig(config) {
    if (!config.entity) throw new Error("You must define an entity");
    this._config = { show_explanation: true, show_copyright: true, show_hd_link: false, ...config };
  }

  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass || !this._config.entity) return;
    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj) {
      this.shadowRoot.innerHTML = `<ha-card><div style="padding:24px;text-align:center;color:${ASTRO.text2}">Entity not found: ${esc(this._config.entity)}</div></ha-card>`;
      return;
    }

    const a = stateObj.attributes;
    const title = a.title || stateObj.state || "";
    const explanation = a.explanation || "";
    const url = a.url || "";
    const hdurl = a.hdurl || "";
    const date = a.date || "";
    const mediaType = a.media_type || "image";
    const copyright = a.copyright || "";

    const mediaHtml = mediaType === "image"
      ? `<div class="apod-media">
           <img src="${esc(url)}" alt="${esc(title)}" loading="lazy" />
           <div class="apod-badge-wrap"><span class="astro-badge">NASA APOD</span></div>
           <div class="apod-overlay">
             <p class="apod-title">${esc(title)}</p>
             <span class="apod-date">${esc(date)}</span>
           </div>
         </div>`
      : `<div class="apod-video"><iframe src="${esc(url)}" allowfullscreen></iframe></div>
         <div class="apod-text-header">
           <span class="astro-badge">NASA APOD</span>
           <p class="apod-title-text">${esc(title)}</p>
           <span class="apod-date-text">${esc(date)}</span>
         </div>`;

    const explanationHtml = this._config.show_explanation && explanation
      ? `<div class="apod-explanation">${esc(explanation)}</div>` : "";
    const copyrightHtml = this._config.show_copyright && copyright
      ? `<div class="apod-footer">© ${esc(copyright)}</div>` : "";
    const hdHtml = this._config.show_hd_link && hdurl
      ? `<div class="apod-hd"><a href="${esc(hdurl)}" target="_blank" rel="noopener">View HD Image ↗</a></div>` : "";

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .apod-media { position:relative; width:100%; min-height:200px; overflow:hidden; }
        .apod-media img { width:100%; height:auto; display:block; object-fit:cover; max-height:420px; }
        .apod-badge-wrap { position:absolute; top:12px; left:12px; }
        .apod-badge-wrap .astro-badge { background: rgba(0,0,0,0.5); color: white; backdrop-filter: blur(4px); }
        .apod-overlay { position:absolute; bottom:0; left:0; right:0; background:linear-gradient(transparent, rgba(0,0,0,0.85)); padding:48px 16px 16px; color:white; }
        .apod-title { font-size:1.05rem; font-weight:500; margin:0 0 4px; text-shadow:0 1px 2px rgba(0,0,0,0.4); }
        .apod-date { font-size:0.78rem; opacity:0.75; }
        .apod-video { position:relative; width:100%; padding-bottom:56.25%; }
        .apod-video iframe { position:absolute; top:0; left:0; width:100%; height:100%; border:none; border-radius:${ASTRO.radius} ${ASTRO.radius} 0 0; }
        .apod-text-header { padding:12px; }
        .apod-title-text { font-size:1rem; font-weight:500; color:${ASTRO.text1}; margin:8px 0 4px; }
        .apod-date-text { font-size:0.78rem; color:${ASTRO.text2}; }
        .apod-explanation { padding:12px; font-size:0.84rem; line-height:1.5; color:${ASTRO.text2}; max-height:120px; overflow-y:auto; }
        .apod-footer { padding:8px 12px 12px; font-size:0.72rem; color:${ASTRO.text2}; opacity:0.7; }
        .apod-hd { padding:4px 12px 14px; }
        .apod-hd a { font-size:0.78rem; color:${ASTRO.accent}; text-decoration:none; font-weight:500; }
        .apod-hd a:hover { text-decoration:underline; }
      </style>
      <div class="astro-card">${mediaHtml}${explanationHtml}${hdHtml}${copyrightHtml}</div>
    `;
  }

  getCardSize() { return 6; }
}

// ============================================================
// NEO THREAT CARD CONFIG EDITOR
// ============================================================
class NeoThreatCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;
    this.shadowRoot.innerHTML = `
      <style>${EDITOR_STYLES}</style>
      <div class="editor">
        <ha-entity-picker
          label="NEO Count Entity"
          value="${this._config.entity || ""}"
          id="entity"
        ></ha-entity-picker>
        <ha-textfield
          label="Max Items to Display"
          type="number"
          value="${this._config.max_items || 8}"
          id="max_items"
        ></ha-textfield>
        <label>
          <ha-switch id="show_hazardous_only" ${this._config.show_hazardous_only ? "checked" : ""}></ha-switch>
          Show Hazardous Only
        </label>
        <label>
          <ha-switch id="show_stats" ${this._config.show_stats !== false ? "checked" : ""}></ha-switch>
          Show Statistics Row
        </label>
      </div>
    `;

    const picker = this.shadowRoot.getElementById("entity");
    picker.hass = this._hass;
    picker.addEventListener("value-changed", (e) => {
      this._config = { ...this._config, entity: e.detail.value }; this._dispatch();
    });
    this.shadowRoot.getElementById("max_items").addEventListener("change", (e) => {
      this._config = { ...this._config, max_items: parseInt(e.target.value) || 8 }; this._dispatch();
    });
    ["show_hazardous_only", "show_stats"].forEach(key => {
      this.shadowRoot.getElementById(key).addEventListener("change", (e) => {
        this._config = { ...this._config, [key]: e.target.checked }; this._dispatch();
      });
    });
  }

  _dispatch() {
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
  }
}
customElements.define("neo-threat-card-editor", NeoThreatCardEditor);

// ============================================================
// NEO THREAT CARD
// ============================================================
class NeoThreatCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  static getConfigElement() { return document.createElement("neo-threat-card-editor"); }

  static getStubConfig() {
    return { entity: "sensor.nasa_astronomy_suite_neo_count_today", max_items: 8, show_hazardous_only: false, show_stats: true };
  }

  setConfig(config) {
    if (!config.entity) throw new Error("You must define an entity");
    this._config = { max_items: 8, show_hazardous_only: false, show_stats: true, ...config };
  }

  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass || !this._config.entity) return;
    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj) {
      this.shadowRoot.innerHTML = `<div class="astro-card" style="padding:24px;text-align:center;color:${ASTRO.text2}">Entity not found</div>`;
      return;
    }

    const attrs = stateObj.attributes;
    let neoList = attrs.neo_list || [];
    const hazardousCount = attrs.hazardous_count || 0;
    const totalCount = attrs.total_count || parseInt(stateObj.state) || 0;

    if (this._config.show_hazardous_only) {
      neoList = neoList.filter(n => n.hazardous);
    }

    const sorted = [...neoList].sort((a, b) => (a.miss_distance_km || Infinity) - (b.miss_distance_km || Infinity));
    const displayed = sorted.slice(0, this._config.max_items);
    const closest = sorted[0];
    const fastest = [...neoList].sort((a, b) => (b.velocity_kmh || 0) - (a.velocity_kmh || 0))[0];

    const badgeClass = hazardousCount > 0 ? "danger" : "";
    const badgeText = hazardousCount > 0 ? `⚠ ${hazardousCount} hazardous` : `${totalCount} tracked`;

    const statsHtml = this._config.show_stats ? `
      <div class="astro-stat-grid cols-3">
        <div class="astro-stat"><div class="astro-stat-value">${totalCount}</div><div class="astro-stat-label">Total</div></div>
        <div class="astro-stat"><div class="astro-stat-value">${closest ? this._fmtDist(closest.miss_distance_km) : '—'}</div><div class="astro-stat-label">Closest</div></div>
        <div class="astro-stat"><div class="astro-stat-value">${fastest ? this._fmtSpeed(fastest.velocity_kmh) : '—'}</div><div class="astro-stat-label">Fastest</div></div>
      </div>
    ` : "";

    const listHtml = displayed.map(neo => `
      <div class="neo-item">
        <div class="neo-dot ${neo.hazardous ? 'danger' : ''}"></div>
        <div class="neo-info">
          <div class="neo-name">${esc(neo.name || '')}</div>
          <div class="neo-detail">⌀ ${neo.diameter_max_m ? neo.diameter_max_m.toFixed(0) : '?'}m · ${this._fmtSpeed(neo.velocity_kmh)}</div>
        </div>
        <div class="neo-dist">${this._fmtDist(neo.miss_distance_km)}</div>
      </div>
    `).join("");

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .neo-body { padding: 0 12px 12px; }
        .neo-item {
          display: grid; grid-template-columns: auto 1fr auto;
          align-items: center; gap: 10px; padding: 10px 12px;
          border-radius: var(--ha-card-border-radius, 12px);
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
          margin-bottom: 6px; transition: background 0.15s;
        }
        .neo-item:hover { background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.08); }
        .neo-dot {
          width: 8px; height: 8px; border-radius: 50%;
          background: ${ASTRO.success};
          flex-shrink: 0;
        }
        .neo-dot.danger {
          background: ${ASTRO.error};
          animation: neo-pulse 2s infinite;
        }
        @keyframes neo-pulse { 0%,100%{opacity:1} 50%{opacity:0.35} }
        .neo-info { min-width: 0; }
        .neo-name {
          font-size: 0.84rem; font-weight: 500; color: ${ASTRO.text1};
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .neo-detail { font-size: 0.72rem; color: ${ASTRO.text2}; margin-top: 2px; }
        .neo-dist {
          font-size: 0.8rem; font-weight: 500; color: ${ASTRO.text1};
          text-align: right; white-space: nowrap;
        }
      </style>
      <div class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:meteor"></ha-icon>
          <span class="astro-title">Near Earth Objects</span>
          <span class="astro-badge ${badgeClass}">${badgeText}</span>
        </div>
        ${statsHtml}
        <div class="neo-body">${listHtml}</div>
      </div>
    `;
  }

  _fmtDist(km) {
    if (!km) return "—";
    if (km > 1000000) return `${(km/1000000).toFixed(1)}M km`;
    if (km > 1000) return `${(km/1000).toFixed(0)}K km`;
    return `${km.toFixed(0)} km`;
  }

  _fmtSpeed(kmh) {
    if (!kmh) return "—";
    return `${(kmh/1000).toFixed(0)}K km/h`;
  }

  getCardSize() { return 5; }
}

// ============================================================
// SOLAR ACTIVITY CARD CONFIG EDITOR
// ============================================================
class SolarActivityCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;
    this.shadowRoot.innerHTML = `
      <style>${EDITOR_STYLES}</style>
      <div class="editor">
        <ha-entity-picker
          label="CME Entity"
          value="${this._config.cme_entity || ""}"
          id="cme_entity"
        ></ha-entity-picker>
        <ha-entity-picker
          label="Solar Flare Entity"
          value="${this._config.flare_entity || ""}"
          id="flare_entity"
        ></ha-entity-picker>
        <ha-entity-picker
          label="Geomagnetic Storm Entity"
          value="${this._config.storm_entity || ""}"
          id="storm_entity"
        ></ha-entity-picker>
        <label>
          <ha-switch id="show_timeline" ${this._config.show_timeline !== false ? "checked" : ""}></ha-switch>
          Show Event Timeline
        </label>
        <label>
          <ha-switch id="show_status_bar" ${this._config.show_status_bar !== false ? "checked" : ""}></ha-switch>
          Show Status Indicator
        </label>
        <ha-textfield
          label="Max Timeline Events"
          type="number"
          value="${this._config.max_events || 6}"
          id="max_events"
        ></ha-textfield>
      </div>
    `;

    ["cme_entity", "flare_entity", "storm_entity"].forEach(key => {
      const picker = this.shadowRoot.getElementById(key);
      picker.hass = this._hass;
      picker.addEventListener("value-changed", (e) => {
        this._config = { ...this._config, [key]: e.detail.value }; this._dispatch();
      });
    });

    ["show_timeline", "show_status_bar"].forEach(key => {
      this.shadowRoot.getElementById(key).addEventListener("change", (e) => {
        this._config = { ...this._config, [key]: e.target.checked }; this._dispatch();
      });
    });

    this.shadowRoot.getElementById("max_events").addEventListener("change", (e) => {
      this._config = { ...this._config, max_events: parseInt(e.target.value) || 6 }; this._dispatch();
    });
  }

  _dispatch() {
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
  }
}
customElements.define("solar-activity-card-editor", SolarActivityCardEditor);

// ============================================================
// SOLAR ACTIVITY CARD
// ============================================================
class SolarActivityCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  static getConfigElement() { return document.createElement("solar-activity-card-editor"); }

  static getStubConfig() {
    return {
      cme_entity: "sensor.nasa_astronomy_suite_coronal_mass_ejections",
      flare_entity: "sensor.nasa_astronomy_suite_solar_flares",
      storm_entity: "sensor.nasa_astronomy_suite_geomagnetic_storms",
      show_timeline: true,
      show_status_bar: true,
      max_events: 6,
    };
  }

  setConfig(config) {
    if (!config.cme_entity || !config.flare_entity || !config.storm_entity) {
      throw new Error("You must define cme_entity, flare_entity, and storm_entity");
    }
    this._config = { show_timeline: true, show_status_bar: true, max_events: 6, ...config };
  }

  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;
    const cmeState = this._hass.states[this._config.cme_entity];
    const flareState = this._hass.states[this._config.flare_entity];
    const stormState = this._hass.states[this._config.storm_entity];

    const cmeCount = cmeState ? parseInt(cmeState.state) || 0 : 0;
    const flareCount = flareState ? parseInt(flareState.state) || 0 : 0;
    const stormCount = stormState ? parseInt(stormState.state) || 0 : 0;
    const total = cmeCount + flareCount + stormCount;

    const statusClass = total > 10 ? "intense" : total > 3 ? "active" : "calm";
    const statusText = total > 10 ? "⚠ Intense Solar Activity" : total > 3 ? "☀ Elevated Activity" : "✓ Solar Conditions Calm";

    const statusHtml = this._config.show_status_bar ? `
      <div class="solar-status ${statusClass}">${statusText}</div>
    ` : "";

    const timelineEvents = this._buildTimeline(cmeState, flareState, stormState);
    const maxEvt = this._config.max_events || 6;
    const timelineHtml = this._config.show_timeline && timelineEvents.length > 0 ? `
      <div class="solar-timeline">
        <div class="solar-tl-title">Recent Events</div>
        <div class="solar-tl-list">
          ${timelineEvents.slice(0, maxEvt).map(e => `
            <div class="solar-evt">
              <div class="solar-evt-dot ${e.category}"></div>
              <div class="solar-evt-info">
                <div class="solar-evt-type">${esc(e.label)}</div>
                <div class="solar-evt-time">${esc(e.time)}</div>
              </div>
              ${e.classType ? `<span class="solar-evt-class">${esc(e.classType)}</span>` : ""}
            </div>
          `).join("")}
        </div>
      </div>
    ` : "";

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .solar-body { padding: 0 12px 12px; }
        .solar-status {
          display: flex; align-items: center; gap: 6px;
          padding: 8px 12px; border-radius: var(--ha-card-border-radius, 12px);
          margin: 0 12px 12px; font-size: 0.8rem; font-weight: 500;
        }
        .solar-status.calm { background: rgba(var(--rgb-success-color, 76,175,80), 0.1); color: ${ASTRO.success}; }
        .solar-status.active { background: rgba(var(--rgb-warning-color, 255,152,0), 0.1); color: ${ASTRO.warning}; }
        .solar-status.intense { background: rgba(var(--rgb-error-color, 244,67,54), 0.1); color: ${ASTRO.error}; }
        .solar-metric {
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
          border-radius: var(--ha-card-border-radius, 12px);
          padding: 14px 10px; text-align: center;
          position: relative; overflow: hidden;
        }
        .solar-metric::before {
          content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        }
        .solar-metric.cme::before { background: ${ASTRO.cme}; }
        .solar-metric.flare::before { background: ${ASTRO.flare}; }
        .solar-metric.storm::before { background: ${ASTRO.storm}; }
        .solar-metric-icon { font-size: 1.3rem; margin-bottom: 4px; }
        .solar-metric-value { font-size: 1.5rem; font-weight: 600; color: ${ASTRO.text1}; }
        .solar-metric-label { font-size: 0.68rem; color: ${ASTRO.text2}; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.3px; font-weight: 500; }
        .solar-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; padding: 0 12px; margin-bottom: 14px; }
        .solar-timeline { border-top: 1px solid ${ASTRO.divider}; margin: 0 12px; padding-top: 12px; padding-bottom: 4px; }
        .solar-tl-title { font-size: 0.72rem; font-weight: 500; color: ${ASTRO.text2}; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
        .solar-tl-list { display: flex; flex-direction: column; gap: 6px; }
        .solar-evt {
          display: flex; align-items: center; gap: 10px;
          padding: 9px 12px; border-radius: var(--ha-card-border-radius, 12px);
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
        }
        .solar-evt-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
        .solar-evt-dot.cme { background: ${ASTRO.cme}; }
        .solar-evt-dot.flare { background: ${ASTRO.flare}; }
        .solar-evt-dot.storm { background: ${ASTRO.storm}; }
        .solar-evt-info { flex: 1; min-width: 0; }
        .solar-evt-type { font-size: 0.78rem; font-weight: 500; color: ${ASTRO.text1}; }
        .solar-evt-time { font-size: 0.7rem; color: ${ASTRO.text2}; }
        .solar-evt-class {
          font-size: 0.72rem; font-weight: 500; padding: 3px 8px;
          border-radius: 8px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.06);
          color: ${ASTRO.text1};
        }
      </style>
      <div class="astro-card">
        <div class="astro-header">
          <ha-icon icon="mdi:white-balance-sunny"></ha-icon>
          <span class="astro-title">Solar Activity Monitor</span>
        </div>
        ${statusHtml}
        <div class="solar-grid">
          <div class="solar-metric cme">
            <div class="solar-metric-icon">💥</div>
            <div class="solar-metric-value">${cmeCount}</div>
            <div class="solar-metric-label">CMEs (7d)</div>
          </div>
          <div class="solar-metric flare">
            <div class="solar-metric-icon">☀️</div>
            <div class="solar-metric-value">${flareCount}</div>
            <div class="solar-metric-label">Flares (7d)</div>
          </div>
          <div class="solar-metric storm">
            <div class="solar-metric-icon">🌊</div>
            <div class="solar-metric-value">${stormCount}</div>
            <div class="solar-metric-label">Storms (30d)</div>
          </div>
        </div>
        ${timelineHtml}
      </div>
    `;
  }

  _buildTimeline(cmeState, flareState, stormState) {
    const events = [];
    if (cmeState?.attributes?.events) {
      for (const e of cmeState.attributes.events) {
        events.push({ category: "cme", label: "Coronal Mass Ejection", time: this._fmtTime(e.start_time), sortTime: e.start_time || "" });
      }
    }
    if (flareState?.attributes?.events) {
      for (const e of flareState.attributes.events) {
        events.push({ category: "flare", label: "Solar Flare", time: this._fmtTime(e.begin_time), classType: e.class_type, sortTime: e.begin_time || "" });
      }
    }
    if (stormState?.attributes?.events) {
      for (const e of stormState.attributes.events) {
        events.push({ category: "storm", label: `Geomagnetic Storm${e.kp_index ? ' (Kp' + e.kp_index + ')' : ''}`, time: this._fmtTime(e.start_time), sortTime: e.start_time || "" });
      }
    }
    events.sort((a, b) => b.sortTime > a.sortTime ? 1 : -1);
    return events;
  }

  _fmtTime(t) {
    if (!t) return "Unknown";
    try { const d = new Date(t); return d.toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }); }
    catch { return t; }
  }

  getCardSize() { return 5; }
}

// ============================================================
// ASTRO HORIZON CARD CONFIG EDITOR
// ============================================================
class AstroHorizonCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;
    this.shadowRoot.innerHTML = `
      <style>${EDITOR_STYLES}</style>
      <div class="editor">
        <ha-entity-picker
          label="Sun Entity"
          value="${this._config.sun_entity || "sun.sun"}"
          id="sun_entity"
        ></ha-entity-picker>
        <ha-entity-picker
          label="Moon Entity (optional)"
          value="${this._config.moon_entity || ""}"
          id="moon_entity"
        ></ha-entity-picker>
        <label>
          <ha-switch id="show_moon" ${this._config.show_moon !== false ? "checked" : ""}></ha-switch>
          Show Moon
        </label>
        <label>
          <ha-switch id="show_azimuth" ${this._config.show_azimuth !== false ? "checked" : ""}></ha-switch>
          Show Azimuth
        </label>
        <label>
          <ha-switch id="show_elevation" ${this._config.show_elevation !== false ? "checked" : ""}></ha-switch>
          Show Elevation
        </label>
        <label>
          <ha-switch id="show_noon_line" ${this._config.show_noon_line !== false ? "checked" : ""}></ha-switch>
          Show Noon Line
        </label>
        <label>
          <ha-switch id="dark_mode" ${this._config.dark_mode !== false ? "checked" : ""}></ha-switch>
          Dark Mode
        </label>
      </div>
    `;

    ["sun_entity", "moon_entity"].forEach(key => {
      const picker = this.shadowRoot.getElementById(key);
      picker.hass = this._hass;
      picker.addEventListener("value-changed", (e) => {
        this._config = { ...this._config, [key]: e.detail.value }; this._dispatch();
      });
    });
    ["show_moon", "show_azimuth", "show_elevation", "show_noon_line", "dark_mode"].forEach(key => {
      this.shadowRoot.getElementById(key).addEventListener("change", (e) => {
        this._config = { ...this._config, [key]: e.target.checked }; this._dispatch();
      });
    });
  }

  _dispatch() {
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
  }
}
customElements.define("astro-horizon-card-editor", AstroHorizonCardEditor);

// ============================================================
// ASTRO HORIZON CARD
// ============================================================
class AstroHorizonCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  static getConfigElement() { return document.createElement("astro-horizon-card-editor"); }

  static getStubConfig() {
    return { sun_entity: "sun.sun", moon_entity: "sensor.moon_phase", show_moon: true, show_azimuth: true, show_elevation: true, show_noon_line: true, dark_mode: true };
  }

  setConfig(config) {
    this._config = { sun_entity: "sun.sun", moon_entity: "sensor.moon_phase", show_moon: true, show_azimuth: true, show_elevation: true, show_noon_line: true, dark_mode: true, ...config };
  }

  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;
    const sun = this._hass.states[this._config.sun_entity];
    if (!sun) {
      this.shadowRoot.innerHTML = `<div class="astro-card" style="padding:24px;text-align:center;color:${ASTRO.text2}">Sun entity not found</div>`;
      return;
    }

    const elevation = parseFloat(sun.attributes.elevation) || 0;
    const azimuth = parseFloat(sun.attributes.azimuth) || 0;
    const rising = sun.attributes.rising || false;
    const nextRise = sun.attributes.next_rising || "";
    const nextSet = sun.attributes.next_setting || "";
    const nextNoon = sun.attributes.next_noon || "";

    // Calculate sun position on the arc
    // Map elevation: -90 to 90 -> 0% to 100% of arc height
    const normalizedElevation = (elevation + 90) / 180;
    // Map azimuth 0-360 to horizontal position on arc
    const sunX = (azimuth / 360) * 100;
    // SVG arc position
    const arcCenterX = 200;
    const arcRadius = 160;
    const arcStartY = 180;
    const sunAngle = Math.PI * (1 - sunX / 100);
    const svgSunX = arcCenterX + arcRadius * Math.cos(sunAngle);
    const svgSunY = arcStartY - arcRadius * Math.sin(sunAngle) * (elevation > 0 ? 1 : 0.3);

    // If below horizon, place below the horizon line
    const effectiveSunY = elevation >= 0
      ? arcStartY - (elevation / 90) * arcRadius
      : arcStartY + (Math.abs(elevation) / 90) * 40;

    // Time formatting
    const fmtTime = (iso) => {
      if (!iso) return "--:--";
      try { return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); }
      catch { return "--:--"; }
    };

    const riseTime = fmtTime(nextRise);
    const setTime = fmtTime(nextSet);
    const noonTime = fmtTime(nextNoon);

    // Moon data
    let moonHtml = "";
    if (this._config.show_moon) {
      const moonEntity = this._hass.states[this._config.moon_entity];
      const moonPhase = moonEntity ? moonEntity.state : "";
      const moonIcon = this._getMoonIcon(moonPhase);
      moonHtml = `
        <div class="hz-moon">
          <span class="hz-moon-icon">${moonIcon}</span>
          <span class="hz-moon-phase">${esc(moonPhase || "Unknown")}</span>
        </div>
      `;
    }

    const darkBg = "var(--ha-card-background, var(--card-background-color, #1e1e2e))";
    const skyGradient = elevation > 0
      ? (elevation > 20 ? "linear-gradient(180deg, #1a3a5c 0%, #4a90d9 50%, #87CEEB 100%)" : "linear-gradient(180deg, #1a237e 0%, #ff6b35 40%, #ffd700 100%)")
      : "linear-gradient(180deg, #0a0e1a 0%, #1a237e 60%, #2a1a4e 100%)";

    const elevLabel = this._config.show_elevation ? `<div class="hz-data-item"><span class="hz-data-label">Elevation</span><span class="hz-data-value">${elevation.toFixed(1)}°</span></div>` : "";
    const azLabel = this._config.show_azimuth ? `<div class="hz-data-item"><span class="hz-data-label">Azimuth</span><span class="hz-data-value">${azimuth.toFixed(1)}°</span></div>` : "";

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .hz-sky {
          position: relative;
          width: 100%;
          height: 200px;
          background: ${skyGradient};
          overflow: hidden;
          border-radius: ${ASTRO.radius} ${ASTRO.radius} 0 0;
        }
        .hz-svg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
        .hz-horizon-line {
          stroke: rgba(255,255,255,0.3);
          stroke-width: 1;
          stroke-dasharray: 4 4;
        }
        .hz-arc {
          fill: none;
          stroke: rgba(255,255,255,0.15);
          stroke-width: 1.5;
          stroke-dasharray: 3 3;
        }
        .hz-noon-line {
          stroke: rgba(255,215,0,0.3);
          stroke-width: 1;
          stroke-dasharray: 2 3;
        }
        .hz-sun {
          filter: drop-shadow(0 0 8px rgba(255,200,0,0.8));
        }
        .hz-sun-glow {
          fill: rgba(255,200,0,0.2);
        }
        .hz-sun-body {
          fill: #ffd700;
        }
        .hz-sun-below .hz-sun-body {
          fill: #ff6b35;
          opacity: 0.6;
        }
        .hz-sun-below .hz-sun-glow {
          fill: rgba(255,107,53,0.15);
        }
        .hz-ground {
          fill: ${this._config.dark_mode ? "rgba(10,15,26,0.85)" : "rgba(30,50,30,0.7)"};
        }
        .hz-time-labels {
          position: absolute;
          bottom: 8px;
          left: 0; right: 0;
          display: flex;
          justify-content: space-between;
          padding: 0 16px;
        }
        .hz-time-label {
          display: flex; flex-direction: column; align-items: center;
          font-size: 0.68rem; color: rgba(255,255,255,0.8);
        }
        .hz-time-label span:first-child { font-size: 0.9rem; margin-bottom: 2px; }
        .hz-time-label span:last-child { font-weight: 600; }
        .hz-body { padding: 14px 12px 16px; }
        .hz-data {
          display: flex; gap: 16px; justify-content: center;
          flex-wrap: wrap;
        }
        .hz-data-item {
          display: flex; flex-direction: column; align-items: center;
          padding: 8px 12px;
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
          border-radius: var(--ha-card-border-radius, 12px);
        }
        .hz-data-label {
          font-size: 0.68rem; color: ${ASTRO.text2};
          text-transform: uppercase; letter-spacing: 0.3px; font-weight: 500;
        }
        .hz-data-value {
          font-size: 1rem; font-weight: 600; color: ${ASTRO.text1};
          margin-top: 2px;
        }
        .hz-moon {
          display: flex; align-items: center; gap: 6px;
          justify-content: center; margin-top: 10px;
          padding-top: 10px; border-top: 1px solid ${ASTRO.divider};
        }
        .hz-moon-icon { font-size: 1.2rem; }
        .hz-moon-phase { font-size: 0.8rem; color: ${ASTRO.text2}; text-transform: capitalize; }
        .hz-state-badge {
          position: absolute; top: 10px; right: 12px;
          background: rgba(0,0,0,0.5); color: white;
          padding: 3px 9px; border-radius: 10px;
          font-size: 0.68rem; font-weight: 600;
          text-transform: uppercase; letter-spacing: 0.4px;
        }
        .hz-state-badge.above { color: ${ASTRO.flare}; }
        .hz-state-badge.below { color: ${ASTRO.accent}; }
      </style>
      <div class="astro-card">
        <div class="hz-sky">
          <svg class="hz-svg" viewBox="0 0 400 200" preserveAspectRatio="xMidYMid meet">
            <!-- Arc path -->
            <path class="hz-arc" d="M 40,180 A 160,160 0 0,1 360,180" />
            <!-- Horizon line -->
            <line class="hz-horizon-line" x1="20" y1="180" x2="380" y2="180" />
            ${this._config.show_noon_line ? '<line class="hz-noon-line" x1="200" y1="20" x2="200" y2="180" />' : ''}
            <!-- Ground fill -->
            <rect class="hz-ground" x="0" y="180" width="400" height="20" />
            <!-- Sun -->
            <g class="${elevation < 0 ? 'hz-sun-below' : 'hz-sun'}" transform="translate(${svgSunX}, ${effectiveSunY})">
              <circle class="hz-sun-glow" cx="0" cy="0" r="18" />
              <circle class="hz-sun-body" cx="0" cy="0" r="8" />
            </g>
          </svg>
          <div class="hz-state-badge ${elevation >= 0 ? 'above' : 'below'}">
            ${elevation >= 0 ? (rising ? '↑ Rising' : '↓ Setting') : '● Below Horizon'}
          </div>
          <div class="hz-time-labels">
            <div class="hz-time-label"><span>🌅</span><span>${riseTime}</span></div>
            ${this._config.show_noon_line ? `<div class="hz-time-label"><span>☀️</span><span>${noonTime}</span></div>` : ''}
            <div class="hz-time-label"><span>🌇</span><span>${setTime}</span></div>
          </div>
        </div>
        <div class="hz-body">
          <div class="hz-data">
            ${elevLabel}
            ${azLabel}
            <div class="hz-data-item"><span class="hz-data-label">Sunrise</span><span class="hz-data-value">${riseTime}</span></div>
            <div class="hz-data-item"><span class="hz-data-label">Sunset</span><span class="hz-data-value">${setTime}</span></div>
          </div>
          ${moonHtml}
        </div>
      </div>
    `;
  }

  _getMoonIcon(phase) {
    const icons = {
      "new_moon": "🌑", "waxing_crescent": "🌒", "first_quarter": "🌓",
      "waxing_gibbous": "🌔", "full_moon": "🌕", "waning_gibbous": "🌖",
      "last_quarter": "🌗", "waning_crescent": "🌘",
    };
    return icons[phase] || icons[phase?.toLowerCase()?.replace(/ /g, "_")] || "🌙";
  }

  getCardSize() { return 5; }
}

// ============================================================
// ASTRO LUNAR PHASE CARD CONFIG EDITOR
// ============================================================
class AstroLunarCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  setConfig(config) { this._config = { ...config }; this._render(); }
  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;
    this.shadowRoot.innerHTML = `
      <style>${EDITOR_STYLES}</style>
      <div class="editor">
        <ha-entity-picker
          label="Moon Phase Entity"
          value="${this._config.entity || "sensor.moon_phase"}"
          id="entity"
        ></ha-entity-picker>
        <label>
          <ha-switch id="show_illumination" ${this._config.show_illumination !== false ? "checked" : ""}></ha-switch>
          Show Illumination
        </label>
        <label>
          <ha-switch id="show_next_phases" ${this._config.show_next_phases !== false ? "checked" : ""}></ha-switch>
          Show Next Phases
        </label>
        <label>
          <ha-switch id="show_phase_name" ${this._config.show_phase_name !== false ? "checked" : ""}></ha-switch>
          Show Phase Name
        </label>
        <label>
          <ha-switch id="compact" ${this._config.compact ? "checked" : ""}></ha-switch>
          Compact Mode
        </label>
      </div>
    `;

    const picker = this.shadowRoot.getElementById("entity");
    picker.hass = this._hass;
    picker.addEventListener("value-changed", (e) => {
      this._config = { ...this._config, entity: e.detail.value }; this._dispatch();
    });
    ["show_illumination", "show_next_phases", "show_phase_name", "compact"].forEach(key => {
      this.shadowRoot.getElementById(key).addEventListener("change", (e) => {
        this._config = { ...this._config, [key]: e.target.checked }; this._dispatch();
      });
    });
  }

  _dispatch() {
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config } }));
  }
}
customElements.define("astro-lunar-card-editor", AstroLunarCardEditor);

// ============================================================
// ASTRO LUNAR PHASE CARD
// ============================================================
class AstroLunarCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  static getConfigElement() { return document.createElement("astro-lunar-card-editor"); }

  static getStubConfig() {
    return { entity: "sensor.moon_phase", show_illumination: true, show_next_phases: true, show_phase_name: true, compact: false };
  }

  setConfig(config) {
    if (!config.entity) throw new Error("You must define an entity");
    this._config = { show_illumination: true, show_next_phases: true, show_phase_name: true, compact: false, ...config };
  }

  set hass(hass) { this._hass = hass; this._render(); }

  _render() {
    if (!this._hass) return;
    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj) {
      this.shadowRoot.innerHTML = `<div class="astro-card" style="padding:24px;text-align:center;color:${ASTRO.text2}">Entity not found: ${esc(this._config.entity)}</div>`;
      return;
    }

    const phase = stateObj.state || "unknown";
    const phaseName = phase.replace(/_/g, " ");
    const phaseData = this._getPhaseData(phase);
    const illumination = phaseData.illumination;
    const moonSize = this._config.compact ? 100 : 150;

    // Build the SVG moon visualization
    const moonSvg = this._renderMoonSvg(phaseData.illuminationFraction, phaseData.waxing, moonSize);

    // Phase cycle (simplified predictions based on ~29.5 day cycle)
    const phaseOrder = ["new_moon", "waxing_crescent", "first_quarter", "waxing_gibbous", "full_moon", "waning_gibbous", "last_quarter", "waning_crescent"];
    const currentIdx = phaseOrder.indexOf(phase.toLowerCase().replace(/ /g, "_"));
    const nextPhases = [];
    if (this._config.show_next_phases && currentIdx >= 0) {
      for (let i = 1; i <= 4; i++) {
        const idx = (currentIdx + i) % 8;
        const daysAway = Math.round((i / 8) * 29.5);
        nextPhases.push({
          name: phaseOrder[idx].replace(/_/g, " "),
          icon: this._getMoonIcon(phaseOrder[idx]),
          days: daysAway,
        });
      }
    }

    const nextPhasesHtml = this._config.show_next_phases && nextPhases.length > 0 ? `
      <div class="lunar-phases">
        ${nextPhases.map(p => `
          <div class="lunar-next">
            <span class="lunar-next-icon">${p.icon}</span>
            <span class="lunar-next-name">${esc(p.name)}</span>
            <span class="lunar-next-days">~${p.days}d</span>
          </div>
        `).join("")}
      </div>
    ` : "";

    this.shadowRoot.innerHTML = `
      <style>
        ${BASE_STYLES}
        .lunar-body {
          display: flex; flex-direction: column; align-items: center;
          padding: ${this._config.compact ? '12px' : '24px'} 16px;
          background: linear-gradient(180deg, #0a0e1a 0%, #1a1a2e 100%);
          border-radius: ${ASTRO.radius} ${ASTRO.radius} 0 0;
          position: relative;
          overflow: hidden;
        }
        .lunar-stars {
          position: absolute; top: 0; left: 0; right: 0; bottom: 0;
          background-image:
            radial-gradient(1px 1px at 20% 30%, rgba(255,255,255,0.6), transparent),
            radial-gradient(1px 1px at 80% 20%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1px 1px at 50% 80%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1.5px 1.5px at 15% 70%, rgba(255,255,255,0.5), transparent),
            radial-gradient(1px 1px at 90% 60%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1px 1px at 35% 10%, rgba(255,255,255,0.3), transparent),
            radial-gradient(1.5px 1.5px at 65% 50%, rgba(255,255,255,0.4), transparent),
            radial-gradient(1px 1px at 10% 90%, rgba(255,255,255,0.3), transparent);
          pointer-events: none;
        }
        .lunar-moon {
          position: relative; z-index: 1;
          filter: drop-shadow(0 0 15px rgba(200,200,255,0.3));
        }
        .lunar-phase-label {
          margin-top: 14px; text-align: center; z-index: 1;
        }
        .lunar-phase-name {
          font-size: ${this._config.compact ? '0.9rem' : '1rem'};
          font-weight: 500; color: #e8e8f0;
          text-transform: capitalize;
        }
        .lunar-illumination {
          font-size: 0.78rem; color: rgba(200,200,255,0.65);
          margin-top: 4px;
        }
        .lunar-info {
          padding: 14px 12px;
        }
        .lunar-phases {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 6px;
          padding: 12px 12px 14px;
          border-top: 1px solid ${ASTRO.divider};
        }
        .lunar-next {
          display: flex; flex-direction: column; align-items: center;
          padding: 10px 4px; border-radius: var(--ha-card-border-radius, 12px);
          background: rgba(var(--rgb-primary-text-color, 0,0,0), 0.04);
        }
        .lunar-next-icon { font-size: 1.2rem; margin-bottom: 4px; }
        .lunar-next-name {
          font-size: 0.62rem; color: ${ASTRO.text2};
          text-align: center; text-transform: capitalize;
          line-height: 1.2;
        }
        .lunar-next-days {
          font-size: 0.68rem; font-weight: 500;
          color: ${ASTRO.accent}; margin-top: 3px;
        }
      </style>
      <div class="astro-card">
        <div class="lunar-body">
          <div class="lunar-stars"></div>
          <div class="lunar-moon">${moonSvg}</div>
          ${this._config.show_phase_name ? `
            <div class="lunar-phase-label">
              <div class="lunar-phase-name">${esc(phaseName)}</div>
              ${this._config.show_illumination ? `<div class="lunar-illumination">${illumination}% illuminated</div>` : ""}
            </div>
          ` : ""}
        </div>
        ${nextPhasesHtml}
      </div>
    `;
  }

  _renderMoonSvg(fraction, waxing, size) {
    // fraction: 0 (new) to 1 (full)
    // We draw a circle and overlay a shadow using SVG paths
    const r = size / 2 - 4;
    const cx = size / 2;
    const cy = size / 2;

    // Calculate the terminator curve
    // For waxing: shadow is on the left, shrinking
    // For waning: shadow is on the right, shrinking
    let shadowPath;

    if (fraction <= 0.01) {
      // New moon - full shadow
      shadowPath = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="rgba(10,10,20,0.92)" />`;
    } else if (fraction >= 0.99) {
      // Full moon - no shadow
      shadowPath = "";
    } else {
      // Partial illumination
      const sweep = fraction < 0.5
        ? (1 - 2 * fraction) * r  // crescent/quarter: bulge inward
        : (2 * fraction - 1) * r; // gibbous: bulge outward

      const dir = fraction < 0.5 ? 0 : 1; // arc sweep direction

      if (waxing) {
        // Shadow on right side (waxing = lit from right)
        // Actually: waxing = right side lit, left side dark
        shadowPath = `<path d="M ${cx} ${cy - r} A ${r} ${r} 0 0 0 ${cx} ${cy + r} A ${sweep} ${r} 0 0 ${dir} ${cx} ${cy - r} Z" fill="rgba(10,10,20,0.9)" />`;
      } else {
        // Shadow on left side (waning = left side dark)
        shadowPath = `<path d="M ${cx} ${cy - r} A ${r} ${r} 0 0 1 ${cx} ${cy + r} A ${sweep} ${r} 0 0 ${1-dir} ${cx} ${cy - r} Z" fill="rgba(10,10,20,0.9)" />`;
      }
    }

    return `
      <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
        <defs>
          <radialGradient id="moon-surface" cx="40%" cy="40%">
            <stop offset="0%" stop-color="#f5f5e8" />
            <stop offset="50%" stop-color="#d4d0c0" />
            <stop offset="100%" stop-color="#a8a090" />
          </radialGradient>
          <filter id="moon-texture">
            <feTurbulence type="fractalNoise" baseFrequency="0.4" numOctaves="3" seed="42" result="noise"/>
            <feColorMatrix type="saturate" values="0" in="noise" result="gray"/>
            <feBlend in="SourceGraphic" in2="gray" mode="multiply" result="textured"/>
          </filter>
        </defs>
        <!-- Moon body -->
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="url(#moon-surface)" />
        <!-- Crater hints -->
        <circle cx="${cx - r*0.2}" cy="${cy - r*0.1}" r="${r*0.12}" fill="rgba(150,140,120,0.3)" />
        <circle cx="${cx + r*0.25}" cy="${cy + r*0.3}" r="${r*0.09}" fill="rgba(150,140,120,0.25)" />
        <circle cx="${cx - r*0.1}" cy="${cy + r*0.35}" r="${r*0.15}" fill="rgba(140,130,110,0.2)" />
        <circle cx="${cx + r*0.35}" cy="${cy - r*0.25}" r="${r*0.07}" fill="rgba(150,140,120,0.2)" />
        <circle cx="${cx - r*0.4}" cy="${cy + r*0.1}" r="${r*0.06}" fill="rgba(150,140,120,0.15)" />
        <!-- Shadow overlay -->
        ${shadowPath}
        <!-- Limb darkening -->
        <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(80,70,60,0.3)" stroke-width="2" />
      </svg>
    `;
  }

  _getPhaseData(phase) {
    const normalized = phase.toLowerCase().replace(/ /g, "_");
    const data = {
      "new_moon": { illumination: 0, illuminationFraction: 0, waxing: true },
      "waxing_crescent": { illumination: 25, illuminationFraction: 0.25, waxing: true },
      "first_quarter": { illumination: 50, illuminationFraction: 0.5, waxing: true },
      "waxing_gibbous": { illumination: 75, illuminationFraction: 0.75, waxing: true },
      "full_moon": { illumination: 100, illuminationFraction: 1.0, waxing: false },
      "waning_gibbous": { illumination: 75, illuminationFraction: 0.75, waxing: false },
      "last_quarter": { illumination: 50, illuminationFraction: 0.5, waxing: false },
      "waning_crescent": { illumination: 25, illuminationFraction: 0.25, waxing: false },
    };
    return data[normalized] || { illumination: 0, illuminationFraction: 0, waxing: true };
  }

  _getMoonIcon(phase) {
    const icons = {
      "new_moon": "🌑", "waxing_crescent": "🌒", "first_quarter": "🌓",
      "waxing_gibbous": "🌔", "full_moon": "🌕", "waning_gibbous": "🌖",
      "last_quarter": "🌗", "waning_crescent": "🌘",
    };
    return icons[phase] || "🌙";
  }

  getCardSize() { return this._config.compact ? 3 : 5; }
}

// ============================================================
// REGISTER ELEMENTS
// ============================================================
customElements.define("apod-card", ApodCard);
customElements.define("neo-threat-card", NeoThreatCard);
customElements.define("solar-activity-card", SolarActivityCard);
customElements.define("astro-horizon-card", AstroHorizonCard);
customElements.define("astro-lunar-card", AstroLunarCard);

window.customCards = window.customCards || [];
window.customCards.push(
  { type: "apod-card", name: "APOD Card", description: "NASA Astronomy Picture of the Day with UI editor", preview: true, documentationURL: "https://github.com/snfx-johaver/home-assistant-astronomy-suite" },
  { type: "neo-threat-card", name: "NEO Threat Card", description: "Near Earth Object tracker with UI editor", preview: true, documentationURL: "https://github.com/snfx-johaver/home-assistant-astronomy-suite" },
  { type: "solar-activity-card", name: "Solar Activity Card", description: "Solar activity monitor with UI editor", preview: true, documentationURL: "https://github.com/snfx-johaver/home-assistant-astronomy-suite" },
  { type: "astro-horizon-card", name: "Astro Horizon Card", description: "Sun/Moon horizon tracker with arc visualization", preview: true, documentationURL: "https://github.com/snfx-johaver/home-assistant-astronomy-suite" },
  { type: "astro-lunar-card", name: "Astro Lunar Phase Card", description: "Moon phase visualization with SVG rendering", preview: true, documentationURL: "https://github.com/snfx-johaver/home-assistant-astronomy-suite" }
);

console.info(
  "%c NASA-ASTRONOMY-CARDS %c v1.2.5 ",
  "color:white;background:#1a237e;font-weight:bold;padding:2px 6px;border-radius:4px 0 0 4px;",
  "color:#1a237e;background:#e8eaf6;font-weight:bold;padding:2px 6px;border-radius:0 4px 4px 0;"
);
