/**
 * NASA Astronomy Cards v1.0.0
 * Pre-built bundle - place in /config/www/community/astronomy-cards/
 * 
 * Cards: <apod-card>, <neo-threat-card>, <solar-activity-card>
 * 
 * NOTE: This is a development/readable version. For production, run `npm run build`
 * in the astronomy-cards directory to generate the minified bundle.
 */

// === LIT POLYFILL (minimal) ===
// In production, lit is bundled. For HA, we use the built-in lit from HA frontend.
// This file uses vanilla JS custom elements for zero-dependency deployment.

// ============================================================
// APOD CARD
// ============================================================
class ApodCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  setConfig(config) {
    if (!config.entity) throw new Error("You must define an entity");
    this._config = { show_explanation: true, show_copyright: true, ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config.entity) return;
    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj) {
      this.shadowRoot.innerHTML = `<ha-card><div style="padding:16px;text-align:center;color:var(--secondary-text-color)">Entity not found: ${this._config.entity}</div></ha-card>`;
      return;
    }

    const attrs = stateObj.attributes;
    const title = attrs.title || stateObj.state || "";
    const explanation = attrs.explanation || "";
    const url = attrs.url || "";
    const date = attrs.date || "";
    const mediaType = attrs.media_type || "image";
    const copyright = attrs.copyright || "";

    const imageHtml = mediaType === "image" 
      ? `<div class="apod-image-container">
           <img src="${url}" alt="${this._escHtml(title)}" loading="lazy" />
           <div class="apod-badge">NASA APOD</div>
           <div class="apod-overlay">
             <p class="apod-title">${this._escHtml(title)}</p>
             <span class="apod-date">${this._escHtml(date)}</span>
           </div>
         </div>`
      : `<div class="apod-video-container">
           <iframe src="${url}" allowfullscreen></iframe>
         </div>
         <div style="padding:12px 16px;">
           <p class="apod-title" style="color:var(--primary-text-color)">${this._escHtml(title)}</p>
           <span class="apod-date" style="color:var(--secondary-text-color)">${this._escHtml(date)}</span>
         </div>`;

    const explanationHtml = this._config.show_explanation && explanation
      ? `<div class="apod-explanation">${this._escHtml(explanation)}</div>` : "";
    const copyrightHtml = this._config.show_copyright && copyright
      ? `<div class="apod-footer">© ${this._escHtml(copyright)}</div>` : "";

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; contain:content; }
        .apod-card { position:relative; border-radius:var(--ha-card-border-radius,12px); overflow:hidden; background:var(--ha-card-background,var(--card-background-color,#fff)); box-shadow:var(--ha-card-box-shadow,none); }
        .apod-image-container { position:relative; width:100%; min-height:200px; overflow:hidden; }
        .apod-image-container img { width:100%; height:auto; display:block; object-fit:cover; max-height:400px; }
        .apod-video-container { position:relative; width:100%; padding-bottom:56.25%; }
        .apod-video-container iframe { position:absolute; top:0; left:0; width:100%; height:100%; border:none; }
        .apod-overlay { position:absolute; bottom:0; left:0; right:0; background:linear-gradient(transparent,rgba(0,0,0,0.85)); padding:40px 16px 16px; color:white; }
        .apod-title { font-size:1.1rem; font-weight:600; margin:0 0 4px; text-shadow:0 1px 3px rgba(0,0,0,0.5); }
        .apod-date { font-size:0.8rem; opacity:0.8; }
        .apod-explanation { padding:12px 16px; font-size:0.85rem; line-height:1.4; color:var(--primary-text-color); max-height:120px; overflow-y:auto; }
        .apod-footer { padding:8px 16px 12px; font-size:0.75rem; opacity:0.6; color:var(--secondary-text-color); }
        .apod-badge { position:absolute; top:12px; left:12px; background:rgba(0,0,0,0.6); color:white; padding:4px 10px; border-radius:12px; font-size:0.7rem; font-weight:600; letter-spacing:0.5px; text-transform:uppercase; }
      </style>
      <div class="apod-card">${imageHtml}${explanationHtml}${copyrightHtml}</div>
    `;
  }

  _escHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  getCardSize() { return 6; }

  static getStubConfig() {
    return { entity: "sensor.nasa_astronomy_suite_apod", show_explanation: true, show_copyright: true };
  }
}

// ============================================================
// NEO THREAT CARD
// ============================================================
class NeoThreatCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  setConfig(config) {
    if (!config.entity) throw new Error("You must define an entity");
    this._config = { show_chart: true, max_items: 8, ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config.entity) return;
    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj) {
      this.shadowRoot.innerHTML = `<ha-card><div style="padding:16px;text-align:center;color:var(--secondary-text-color)">Entity not found</div></ha-card>`;
      return;
    }

    const attrs = stateObj.attributes;
    const neoList = attrs.neo_list || [];
    const hazardousCount = attrs.hazardous_count || 0;
    const totalCount = attrs.total_count || parseInt(stateObj.state) || 0;

    const sorted = [...neoList].sort((a, b) => (a.miss_distance_km || Infinity) - (b.miss_distance_km || Infinity));
    const displayed = sorted.slice(0, this._config.max_items);
    const closest = sorted[0];
    const fastest = [...neoList].sort((a, b) => (b.velocity_kmh || 0) - (a.velocity_kmh || 0))[0];

    const badge = hazardousCount > 0
      ? `<span class="neo-count-badge hazardous">⚠ ${hazardousCount} hazardous</span>`
      : `<span class="neo-count-badge">${totalCount} tracked</span>`;

    const listHtml = displayed.map(neo => `
      <div class="neo-item">
        <div class="neo-hazard-indicator ${neo.hazardous ? 'dangerous' : ''}"></div>
        <div class="neo-item-info">
          <div class="neo-item-name">${this._escHtml(neo.name || '')}</div>
          <div class="neo-item-details">⌀ ${neo.diameter_max_m ? neo.diameter_max_m.toFixed(0) : '?'}m · ${this._fmtSpeed(neo.velocity_kmh)}</div>
        </div>
        <div class="neo-item-distance">${this._fmtDist(neo.miss_distance_km)}</div>
      </div>
    `).join("");

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; contain:content; }
        .neo-card { background:var(--ha-card-background,var(--card-background-color,#fff)); border-radius:var(--ha-card-border-radius,12px); box-shadow:var(--ha-card-box-shadow,none); overflow:hidden; padding:16px; }
        .neo-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
        .neo-title { display:flex; align-items:center; gap:8px; font-size:1rem; font-weight:600; color:var(--primary-text-color); }
        .neo-count-badge { background:var(--warning-color,#ff9800); color:white; padding:2px 10px; border-radius:12px; font-size:0.8rem; font-weight:600; }
        .neo-count-badge.hazardous { background:var(--error-color,#f44336); }
        .neo-stats { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:16px; }
        .neo-stat { background:var(--secondary-background-color); border-radius:8px; padding:10px; text-align:center; }
        .neo-stat-value { font-size:1.1rem; font-weight:700; color:var(--primary-text-color); }
        .neo-stat-label { font-size:0.7rem; color:var(--secondary-text-color); margin-top:2px; text-transform:uppercase; letter-spacing:0.3px; }
        .neo-list { display:flex; flex-direction:column; gap:8px; }
        .neo-item { display:grid; grid-template-columns:auto 1fr auto; align-items:center; gap:10px; padding:10px; border-radius:8px; background:var(--secondary-background-color); }
        .neo-hazard-indicator { width:8px; height:8px; border-radius:50%; background:var(--success-color,#4caf50); }
        .neo-hazard-indicator.dangerous { background:var(--error-color,#f44336); animation:pulse 2s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        .neo-item-info { min-width:0; }
        .neo-item-name { font-size:0.85rem; font-weight:500; color:var(--primary-text-color); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
        .neo-item-details { font-size:0.72rem; color:var(--secondary-text-color); margin-top:2px; }
        .neo-item-distance { font-size:0.8rem; font-weight:600; color:var(--primary-text-color); text-align:right; white-space:nowrap; }
      </style>
      <div class="neo-card">
        <div class="neo-header">
          <div class="neo-title"><ha-icon icon="mdi:meteor"></ha-icon>Near Earth Objects</div>
          ${badge}
        </div>
        <div class="neo-stats">
          <div class="neo-stat"><div class="neo-stat-value">${totalCount}</div><div class="neo-stat-label">Total</div></div>
          <div class="neo-stat"><div class="neo-stat-value">${closest ? this._fmtDist(closest.miss_distance_km) : '—'}</div><div class="neo-stat-label">Closest</div></div>
          <div class="neo-stat"><div class="neo-stat-value">${fastest ? this._fmtSpeed(fastest.velocity_kmh) : '—'}</div><div class="neo-stat-label">Fastest</div></div>
        </div>
        <div class="neo-list">${listHtml}</div>
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

  _escHtml(str) { const d=document.createElement("div"); d.textContent=str; return d.innerHTML; }
  getCardSize() { return 5; }
  static getStubConfig() { return { entity: "sensor.nasa_astronomy_suite_neo_count_today", max_items: 8 }; }
}

// ============================================================
// SOLAR ACTIVITY CARD
// ============================================================
class SolarActivityCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  setConfig(config) {
    if (!config.cme_entity || !config.flare_entity || !config.storm_entity) {
      throw new Error("You must define cme_entity, flare_entity, and storm_entity");
    }
    this._config = { show_timeline: true, ...config };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

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

    const timelineEvents = this._buildTimeline(cmeState, flareState, stormState);
    const timelineHtml = this._config.show_timeline && timelineEvents.length > 0 ? `
      <div class="solar-timeline">
        <div class="solar-timeline-title">Recent Events</div>
        <div class="solar-timeline-list">
          ${timelineEvents.slice(0,6).map(e => `
            <div class="solar-event">
              <div class="solar-event-dot ${e.category}"></div>
              <div class="solar-event-info">
                <div class="solar-event-type">${this._escHtml(e.label)}</div>
                <div class="solar-event-time">${this._escHtml(e.time)}</div>
              </div>
              ${e.classType ? `<span class="solar-event-class">${this._escHtml(e.classType)}</span>` : ""}
            </div>
          `).join("")}
        </div>
      </div>
    ` : "";

    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; contain:content; }
        .solar-card { background:var(--ha-card-background,var(--card-background-color,#fff)); border-radius:var(--ha-card-border-radius,12px); box-shadow:var(--ha-card-box-shadow,none); overflow:hidden; padding:16px; }
        .solar-header { display:flex; align-items:center; gap:8px; margin-bottom:16px; }
        .solar-header ha-icon { color:var(--warning-color,#ff9800); }
        .solar-title { font-size:1rem; font-weight:600; color:var(--primary-text-color); }
        .solar-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:16px; }
        .solar-metric { background:var(--secondary-background-color); border-radius:10px; padding:14px 10px; text-align:center; position:relative; overflow:hidden; }
        .solar-metric::before { content:""; position:absolute; top:0; left:0; right:0; height:3px; }
        .solar-metric.cme::before { background:#ff6b35; }
        .solar-metric.flare::before { background:#ffd700; }
        .solar-metric.storm::before { background:#9c27b0; }
        .solar-metric-icon { font-size:1.4rem; margin-bottom:6px; }
        .solar-metric-value { font-size:1.6rem; font-weight:700; color:var(--primary-text-color); }
        .solar-metric-label { font-size:0.7rem; color:var(--secondary-text-color); margin-top:4px; text-transform:uppercase; letter-spacing:0.3px; }
        .solar-timeline { border-top:1px solid var(--divider-color); padding-top:12px; }
        .solar-timeline-title { font-size:0.8rem; font-weight:600; color:var(--secondary-text-color); margin-bottom:10px; text-transform:uppercase; letter-spacing:0.5px; }
        .solar-timeline-list { display:flex; flex-direction:column; gap:6px; }
        .solar-event { display:flex; align-items:center; gap:10px; padding:8px 10px; border-radius:6px; background:var(--secondary-background-color); }
        .solar-event-dot { width:6px; height:6px; border-radius:50%; flex-shrink:0; }
        .solar-event-dot.cme { background:#ff6b35; }
        .solar-event-dot.flare { background:#ffd700; }
        .solar-event-dot.storm { background:#9c27b0; }
        .solar-event-info { flex:1; min-width:0; }
        .solar-event-type { font-size:0.78rem; font-weight:500; color:var(--primary-text-color); }
        .solar-event-time { font-size:0.7rem; color:var(--secondary-text-color); }
        .solar-event-class { font-size:0.75rem; font-weight:600; padding:2px 6px; border-radius:4px; background:var(--divider-color); color:var(--primary-text-color); }
        .solar-status { display:flex; align-items:center; gap:6px; padding:8px 12px; border-radius:8px; margin-bottom:12px; font-size:0.8rem; font-weight:500; }
        .solar-status.calm { background:rgba(76,175,80,0.1); color:var(--success-color,#4caf50); }
        .solar-status.active { background:rgba(255,152,0,0.1); color:var(--warning-color,#ff9800); }
        .solar-status.intense { background:rgba(244,67,54,0.1); color:var(--error-color,#f44336); }
      </style>
      <div class="solar-card">
        <div class="solar-header"><ha-icon icon="mdi:white-balance-sunny"></ha-icon><span class="solar-title">Solar Activity Monitor</span></div>
        <div class="solar-status ${statusClass}">${statusText}</div>
        <div class="solar-grid">
          <div class="solar-metric cme"><div class="solar-metric-icon">💥</div><div class="solar-metric-value">${cmeCount}</div><div class="solar-metric-label">CMEs (7d)</div></div>
          <div class="solar-metric flare"><div class="solar-metric-icon">☀️</div><div class="solar-metric-value">${flareCount}</div><div class="solar-metric-label">Flares (7d)</div></div>
          <div class="solar-metric storm"><div class="solar-metric-icon">🌊</div><div class="solar-metric-value">${stormCount}</div><div class="solar-metric-label">Storms (30d)</div></div>
        </div>
        ${timelineHtml}
      </div>
    `;
  }

  _buildTimeline(cmeState, flareState, stormState) {
    const events = [];
    if (cmeState && cmeState.attributes && cmeState.attributes.events) {
      for (const e of cmeState.attributes.events) {
        events.push({ category:"cme", label:"Coronal Mass Ejection", time:this._fmtTime(e.start_time), sortTime:e.start_time||"" });
      }
    }
    if (flareState && flareState.attributes && flareState.attributes.events) {
      for (const e of flareState.attributes.events) {
        events.push({ category:"flare", label:"Solar Flare", time:this._fmtTime(e.begin_time), classType:e.class_type, sortTime:e.begin_time||"" });
      }
    }
    if (stormState && stormState.attributes && stormState.attributes.events) {
      for (const e of stormState.attributes.events) {
        events.push({ category:"storm", label:`Geomagnetic Storm${e.kp_index?' (Kp'+e.kp_index+')':''}`, time:this._fmtTime(e.start_time), sortTime:e.start_time||"" });
      }
    }
    events.sort((a,b) => b.sortTime > a.sortTime ? 1 : -1);
    return events;
  }

  _fmtTime(t) {
    if (!t) return "Unknown";
    try { const d=new Date(t); return d.toLocaleDateString(undefined,{month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"}); }
    catch { return t; }
  }

  _escHtml(str) { const d=document.createElement("div"); d.textContent=str||""; return d.innerHTML; }
  getCardSize() { return 5; }
  static getStubConfig() {
    return { cme_entity:"sensor.nasa_astronomy_suite_coronal_mass_ejections", flare_entity:"sensor.nasa_astronomy_suite_solar_flares", storm_entity:"sensor.nasa_astronomy_suite_geomagnetic_storms" };
  }
}

// ============================================================
// REGISTER ELEMENTS
// ============================================================
customElements.define("apod-card", ApodCard);
customElements.define("neo-threat-card", NeoThreatCard);
customElements.define("solar-activity-card", SolarActivityCard);

window.customCards = window.customCards || [];
window.customCards.push(
  { type:"apod-card", name:"APOD Card", description:"NASA Astronomy Picture of the Day", preview:true },
  { type:"neo-threat-card", name:"NEO Threat Card", description:"Near Earth Object tracker", preview:true },
  { type:"solar-activity-card", name:"Solar Activity Card", description:"Solar activity monitor", preview:true }
);

console.info(
  "%c NASA-ASTRONOMY-CARDS %c v1.0.0 ",
  "color:white;background:#1a237e;font-weight:bold;padding:2px 6px;border-radius:4px 0 0 4px;",
  "color:#1a237e;background:#e8eaf6;font-weight:bold;padding:2px 6px;border-radius:0 4px 4px 0;"
);
