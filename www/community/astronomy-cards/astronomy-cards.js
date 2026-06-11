/**
 * NASA Astronomy Cards v1.1.0
 * Pre-built bundle - place in /config/www/community/astronomy-cards/
 *
 * Cards: <apod-card>, <neo-threat-card>, <solar-activity-card>
 * All cards feature:
 *  - Visual UI config editor (no YAML needed)
 *  - Consistent shared color theme
 */

// ============================================================
// SHARED THEME
// ============================================================
const ASTRO = {
  primary: "#1a237e",
  accent: "#7c4dff",
  radius: "var(--ha-card-border-radius, 12px)",
  shadow: "var(--ha-card-box-shadow, none)",
  surface: "var(--ha-card-background, var(--card-background-color, #fff))",
  text1: "var(--primary-text-color)",
  text2: "var(--secondary-text-color)",
  bg2: "var(--secondary-background-color)",
  divider: "var(--divider-color)",
  success: "#4caf50",
  warning: "#ff9800",
  error: "#f44336",
  cme: "#ff6b35",
  flare: "#ffd700",
  storm: "#9c27b0",
  neo: "#42a5f5",
  badge: "rgba(26, 35, 126, 0.85)",
  overlay: "linear-gradient(transparent, rgba(10, 10, 30, 0.92))",
};

// Shared base styles injected into all cards
const BASE_STYLES = `
  :host { display:block; contain:content; }
  .astro-card {
    background: ${ASTRO.surface};
    border-radius: ${ASTRO.radius};
    box-shadow: ${ASTRO.shadow};
    overflow: hidden;
    border: 1px solid ${ASTRO.divider};
  }
  .astro-header {
    display: flex; align-items: center; gap: 8px;
    padding: 16px 16px 0; margin-bottom: 12px;
  }
  .astro-header ha-icon { color: ${ASTRO.accent}; --mdc-icon-size: 22px; }
  .astro-title {
    font-size: 0.95rem; font-weight: 600;
    color: ${ASTRO.text1}; flex: 1;
  }
  .astro-badge {
    background: ${ASTRO.badge}; color: white;
    padding: 3px 10px; border-radius: 12px;
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.3px; text-transform: uppercase;
  }
  .astro-badge.warn { background: ${ASTRO.warning}; }
  .astro-badge.danger { background: ${ASTRO.error}; }
  .astro-stat-grid {
    display: grid; gap: 8px; padding: 0 16px; margin-bottom: 14px;
  }
  .astro-stat-grid.cols-3 { grid-template-columns: repeat(3, 1fr); }
  .astro-stat-grid.cols-4 { grid-template-columns: repeat(4, 1fr); }
  .astro-stat {
    background: ${ASTRO.bg2}; border-radius: 8px;
    padding: 10px 8px; text-align: center;
  }
  .astro-stat-value {
    font-size: 1.1rem; font-weight: 700; color: ${ASTRO.text1};
  }
  .astro-stat-label {
    font-size: 0.68rem; color: ${ASTRO.text2};
    margin-top: 2px; text-transform: uppercase; letter-spacing: 0.3px;
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
        .apod-overlay { position:absolute; bottom:0; left:0; right:0; background:${ASTRO.overlay}; padding:48px 16px 16px; color:white; }
        .apod-title { font-size:1.1rem; font-weight:600; margin:0 0 4px; text-shadow:0 1px 3px rgba(0,0,0,0.6); }
        .apod-date { font-size:0.8rem; opacity:0.8; }
        .apod-video { position:relative; width:100%; padding-bottom:56.25%; }
        .apod-video iframe { position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
        .apod-text-header { padding:12px 16px; }
        .apod-title-text { font-size:1.05rem; font-weight:600; color:${ASTRO.text1}; margin:8px 0 4px; }
        .apod-date-text { font-size:0.8rem; color:${ASTRO.text2}; }
        .apod-explanation { padding:12px 16px; font-size:0.84rem; line-height:1.5; color:${ASTRO.text1}; max-height:120px; overflow-y:auto; }
        .apod-footer { padding:8px 16px 12px; font-size:0.75rem; opacity:0.6; color:${ASTRO.text2}; }
        .apod-hd { padding:4px 16px 14px; }
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
        .neo-body { padding: 0 16px 16px; }
        .neo-item {
          display: grid; grid-template-columns: auto 1fr auto;
          align-items: center; gap: 10px; padding: 9px 12px;
          border-radius: 8px; background: ${ASTRO.bg2};
          margin-bottom: 6px; transition: background 0.15s;
        }
        .neo-item:hover { background: ${ASTRO.divider}; }
        .neo-dot {
          width: 8px; height: 8px; border-radius: 50%;
          background: ${ASTRO.success};
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
        .neo-detail { font-size: 0.71rem; color: ${ASTRO.text2}; margin-top: 2px; }
        .neo-dist {
          font-size: 0.8rem; font-weight: 600; color: ${ASTRO.text1};
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
        .solar-body { padding: 0 16px 16px; }
        .solar-status {
          display: flex; align-items: center; gap: 6px;
          padding: 8px 12px; border-radius: 8px;
          margin: 0 16px 12px; font-size: 0.8rem; font-weight: 500;
        }
        .solar-status.calm { background: rgba(76,175,80,0.1); color: ${ASTRO.success}; }
        .solar-status.active { background: rgba(255,152,0,0.1); color: ${ASTRO.warning}; }
        .solar-status.intense { background: rgba(244,67,54,0.1); color: ${ASTRO.error}; }
        .solar-metric {
          background: ${ASTRO.bg2}; border-radius: 10px;
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
        .solar-metric-value { font-size: 1.5rem; font-weight: 700; color: ${ASTRO.text1}; }
        .solar-metric-label { font-size: 0.68rem; color: ${ASTRO.text2}; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.3px; }
        .solar-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 10px; padding: 0 16px; margin-bottom: 14px; }
        .solar-timeline { border-top: 1px solid ${ASTRO.divider}; margin: 0 16px; padding-top: 12px; padding-bottom: 4px; }
        .solar-tl-title { font-size: 0.76rem; font-weight: 600; color: ${ASTRO.text2}; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; }
        .solar-tl-list { display: flex; flex-direction: column; gap: 6px; }
        .solar-evt {
          display: flex; align-items: center; gap: 10px;
          padding: 8px 10px; border-radius: 6px; background: ${ASTRO.bg2};
        }
        .solar-evt-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
        .solar-evt-dot.cme { background: ${ASTRO.cme}; }
        .solar-evt-dot.flare { background: ${ASTRO.flare}; }
        .solar-evt-dot.storm { background: ${ASTRO.storm}; }
        .solar-evt-info { flex: 1; min-width: 0; }
        .solar-evt-type { font-size: 0.78rem; font-weight: 500; color: ${ASTRO.text1}; }
        .solar-evt-time { font-size: 0.7rem; color: ${ASTRO.text2}; }
        .solar-evt-class {
          font-size: 0.73rem; font-weight: 600; padding: 2px 7px;
          border-radius: 4px; background: ${ASTRO.divider}; color: ${ASTRO.text1};
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
// REGISTER ELEMENTS
// ============================================================
customElements.define("apod-card", ApodCard);
customElements.define("neo-threat-card", NeoThreatCard);
customElements.define("solar-activity-card", SolarActivityCard);

window.customCards = window.customCards || [];
window.customCards.push(
  { type: "apod-card", name: "APOD Card", description: "NASA Astronomy Picture of the Day with UI editor", preview: true, documentationURL: "https://github.com/snfx-johaver/home-assistant-astronomy-suite" },
  { type: "neo-threat-card", name: "NEO Threat Card", description: "Near Earth Object tracker with UI editor", preview: true, documentationURL: "https://github.com/snfx-johaver/home-assistant-astronomy-suite" },
  { type: "solar-activity-card", name: "Solar Activity Card", description: "Solar activity monitor with UI editor", preview: true, documentationURL: "https://github.com/snfx-johaver/home-assistant-astronomy-suite" }
);

console.info(
  "%c NASA-ASTRONOMY-CARDS %c v1.1.0 ",
  "color:white;background:#1a237e;font-weight:bold;padding:2px 6px;border-radius:4px 0 0 4px;",
  "color:#1a237e;background:#e8eaf6;font-weight:bold;padding:2px 6px;border-radius:0 4px 4px 0;"
);
