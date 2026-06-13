/**
 * Night Sky Highlights 2 Card
 * Version: 1.0.0
 * 
 * An enhanced standalone Lovelace card showing tonight's best observing targets.
 * Fully independent — does NOT modify or replace the original Night Sky Highlights card.
 */

const NSH2_VERSION = "1.0.0";

const NSH2_STYLES = `
  :host {
    display: block;
  }
  .nsh2-card {
    padding: 16px;
    border-radius: var(--ha-card-border-radius, 12px);
    background: var(--ha-card-background, var(--card-background-color, #fff));
    box-shadow: var(--ha-card-box-shadow, none);
    color: var(--primary-text-color);
    font-family: var(--paper-font-body1_-_font-family, 'Roboto', sans-serif);
  }
  .nsh2-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
  }
  .nsh2-title {
    font-size: 1.2em;
    font-weight: 500;
    color: var(--primary-text-color);
  }
  .nsh2-subtitle {
    font-size: 0.75em;
    color: var(--secondary-text-color);
    opacity: 0.7;
  }
  .nsh2-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 12px;
  }
  .nsh2-tile {
    display: flex;
    flex-direction: column;
    padding: 14px;
    border-radius: 10px;
    background: var(--card-background-color, rgba(0,0,0,0.03));
    border: 1px solid var(--divider-color, rgba(0,0,0,0.08));
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .nsh2-tile:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }
  .nsh2-tile-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }
  .nsh2-icon {
    font-size: 1.6em;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
  }
  .nsh2-tile-title {
    font-size: 0.95em;
    font-weight: 500;
    flex: 1;
  }
  .nsh2-visibility-badge {
    font-size: 0.7em;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 12px;
    color: #fff;
    min-width: 32px;
    text-align: center;
  }
  .nsh2-vis-green { background: #4caf50; }
  .nsh2-vis-yellow { background: #ff9800; }
  .nsh2-vis-red { background: #f44336; }
  .nsh2-description {
    font-size: 0.82em;
    color: var(--secondary-text-color);
    margin-bottom: 8px;
    line-height: 1.4;
  }
  .nsh2-footer {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }
  .nsh2-badge {
    font-size: 0.65em;
    font-weight: 600;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: 6px;
    background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
    color: var(--primary-color, #03a9f4);
    letter-spacing: 0.3px;
  }
  .nsh2-countdown {
    font-size: 0.75em;
    color: var(--secondary-text-color);
    margin-left: auto;
    font-variant-numeric: tabular-nums;
  }
  .nsh2-sparkline {
    margin-top: 8px;
    height: 30px;
    width: 100%;
  }
  .nsh2-sparkline svg {
    width: 100%;
    height: 100%;
  }
  .nsh2-sparkline path {
    fill: none;
    stroke: var(--primary-color, #03a9f4);
    stroke-width: 1.5;
    stroke-linecap: round;
    stroke-linejoin: round;
  }
  .nsh2-sparkline .nsh2-spark-fill {
    fill: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
    stroke: none;
  }
  .nsh2-unavailable {
    opacity: 0.4;
    pointer-events: none;
  }
  .nsh2-empty {
    text-align: center;
    padding: 32px 16px;
    color: var(--secondary-text-color);
    font-size: 0.9em;
  }
  @media (max-width: 600px) {
    .nsh2-grid {
      grid-template-columns: 1fr;
    }
  }
`;

class NightSkyHighlights2Card extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._rendered = false;
  }

  static getConfigElement() {
    return document.createElement("night-sky-highlights-2-card-editor");
  }

  static getStubConfig() {
    return {
      title: "Night Sky Highlights 2",
      entities: {
        best_planet: "sensor.best_planet_tonight",
        best_dso: "sensor.best_dso_tonight",
        meteor_shower: "sensor.meteor_shower_activity",
        iss: "sensor.iss_next_pass",
        comet: "sensor.brightest_comet",
        events: "sensor.astronomy_special_events",
      },
    };
  }

  setConfig(config) {
    if (!config.entities) {
      throw new Error("Please define entities in the card configuration.");
    }
    this._config = {
      title: config.title || "Night Sky Highlights 2",
      entities: config.entities || {},
      show_sparkline: config.show_sparkline !== false,
      ...config,
    };
    this._rendered = false;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _getVisibilityClass(score) {
    if (score == null || isNaN(score)) return "nsh2-vis-yellow";
    if (score > 70) return "nsh2-vis-green";
    if (score >= 40) return "nsh2-vis-yellow";
    return "nsh2-vis-red";
  }

  _getEntityData(entityId) {
    if (!entityId || !this._hass) return null;
    const state = this._hass.states[entityId];
    if (!state || state.state === "unavailable" || state.state === "unknown") return null;
    return state;
  }

  _formatCountdown(targetTime) {
    if (!targetTime) return "";
    const now = new Date();
    let target;
    if (typeof targetTime === "number") {
      target = new Date(targetTime > 1e11 ? targetTime : targetTime * 1000);
    } else {
      target = new Date(targetTime);
    }
    if (isNaN(target.getTime())) return "";
    const diff = target - now;
    if (diff <= 0) return "Now";
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    if (hours > 24) return `${Math.floor(hours / 24)}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  }

  _buildSparkline(data) {
    if (!data || !Array.isArray(data) || data.length < 2) return "";
    const width = 200;
    const height = 28;
    const max = Math.max(...data);
    const min = Math.min(...data);
    const range = max - min || 1;
    const step = width / (data.length - 1);

    const points = data.map((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    });

    const linePath = `M${points.join(" L")}`;
    const fillPath = `${linePath} L${width},${height} L0,${height} Z`;

    return `
      <div class="nsh2-sparkline">
        <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
          <path class="nsh2-spark-fill" d="${fillPath}"/>
          <path d="${linePath}"/>
        </svg>
      </div>
    `;
  }

  _buildTile(icon, title, visibility, description, badges, countdown, sparklineData, unavailable) {
    const visClass = this._getVisibilityClass(visibility);
    const visText = visibility != null && !isNaN(visibility) ? `${Math.round(visibility)}%` : "—";
    const unavailClass = unavailable ? " nsh2-unavailable" : "";
    const countdownHtml = countdown ? `<span class="nsh2-countdown">⏱ ${countdown}</span>` : "";
    const badgesHtml = (badges || [])
      .map((b) => `<span class="nsh2-badge">${b}</span>`)
      .join("");
    const sparkHtml = this._config.show_sparkline ? this._buildSparkline(sparklineData) : "";

    return `
      <div class="nsh2-tile${unavailClass}">
        <div class="nsh2-tile-header">
          <div class="nsh2-icon">${icon}</div>
          <div class="nsh2-tile-title">${title}</div>
          <span class="nsh2-visibility-badge ${visClass}">${visText}</span>
        </div>
        <div class="nsh2-description">${description || "No data available"}</div>
        <div class="nsh2-footer">
          ${badgesHtml}
          ${countdownHtml}
        </div>
        ${sparkHtml}
      </div>
    `;
  }

  _parseTile(entityId, defaults) {
    const state = this._getEntityData(entityId);
    if (!state) {
      return this._buildTile(
        defaults.icon,
        defaults.title,
        null,
        "Sensor unavailable",
        [],
        "",
        null,
        true
      );
    }

    const attrs = state.attributes || {};
    const title = attrs.friendly_name || attrs.name || defaults.title;
    const visibility = parseFloat(attrs.visibility_score ?? attrs.visibility ?? attrs.score ?? state.state);
    const description = attrs.description || attrs.summary || attrs.details || state.state;
    const badges = attrs.badges || attrs.tags || attrs.event_types || [];
    const countdownTarget = attrs.next_time || attrs.countdown || attrs.event_time || attrs.pass_time;
    const countdown = this._formatCountdown(countdownTarget);
    const sparkData = attrs.altitude_forecast || attrs.altitude_data || attrs.sparkline || null;

    return this._buildTile(
      defaults.icon,
      title,
      isNaN(visibility) ? null : visibility,
      typeof description === "string" ? description : JSON.stringify(description),
      Array.isArray(badges) ? badges : [badges].filter(Boolean),
      countdown,
      sparkData,
      false
    );
  }

  _render() {
    if (!this._hass || !this._config) return;

    const entities = this._config.entities;

    const tiles = [
      this._parseTile(entities.best_planet, { icon: "🪐", title: "Best Planet Tonight" }),
      this._parseTile(entities.best_dso, { icon: "🌌", title: "Best DSO Tonight" }),
      this._parseTile(entities.meteor_shower, { icon: "☄️", title: "Meteor Shower Activity" }),
      this._parseTile(entities.iss, { icon: "🛰️", title: "ISS Next Pass" }),
      this._parseTile(entities.comet, { icon: "💫", title: "Brightest Comet" }),
      this._parseTile(entities.events, { icon: "🔭", title: "Special Events" }),
    ];

    const html = `
      <style>${NSH2_STYLES}</style>
      <ha-card>
        <div class="nsh2-card">
          <div class="nsh2-header">
            <div>
              <div class="nsh2-title">${this._config.title}</div>
              <div class="nsh2-subtitle">Updated ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>
            </div>
          </div>
          <div class="nsh2-grid">
            ${tiles.join("")}
          </div>
        </div>
      </ha-card>
    `;

    this.shadowRoot.innerHTML = html;
  }

  getCardSize() {
    return 5;
  }
}

// --- Editor ---
class NightSkyHighlights2CardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  _render() {
    const entities = this._config.entities || {};
    this.shadowRoot.innerHTML = `
      <style>
        .editor { padding: 16px; font-family: var(--paper-font-body1_-_font-family, sans-serif); }
        .field { margin-bottom: 12px; }
        .field label { display: block; font-size: 0.85em; margin-bottom: 4px; color: var(--secondary-text-color); }
        .field input { width: 100%; padding: 8px; border: 1px solid var(--divider-color, #ccc); border-radius: 6px; font-size: 0.9em; box-sizing: border-box; background: var(--card-background-color, #fff); color: var(--primary-text-color); }
        .section-title { font-weight: 500; margin: 16px 0 8px; font-size: 0.9em; }
      </style>
      <div class="editor">
        <div class="field">
          <label>Card Title</label>
          <input type="text" id="title" value="${this._config.title || "Night Sky Highlights 2"}" />
        </div>
        <div class="section-title">Entity Configuration</div>
        <div class="field">
          <label>Best Planet Tonight</label>
          <input type="text" id="best_planet" value="${entities.best_planet || ""}" />
        </div>
        <div class="field">
          <label>Best DSO Tonight</label>
          <input type="text" id="best_dso" value="${entities.best_dso || ""}" />
        </div>
        <div class="field">
          <label>Meteor Shower Activity</label>
          <input type="text" id="meteor_shower" value="${entities.meteor_shower || ""}" />
        </div>
        <div class="field">
          <label>ISS Next Pass</label>
          <input type="text" id="iss" value="${entities.iss || ""}" />
        </div>
        <div class="field">
          <label>Brightest Comet</label>
          <input type="text" id="comet" value="${entities.comet || ""}" />
        </div>
        <div class="field">
          <label>Special Events</label>
          <input type="text" id="events" value="${entities.events || ""}" />
        </div>
        <div class="field" style="margin-top:16px;">
          <label>
            <input type="checkbox" id="show_sparkline" ${this._config.show_sparkline !== false ? "checked" : ""} />
            Show altitude sparkline (if available)
          </label>
        </div>
      </div>
    `;

    // Bind events
    this.shadowRoot.getElementById("title").addEventListener("input", (e) => {
      this._config.title = e.target.value;
      this._dispatch();
    });

    ["best_planet", "best_dso", "meteor_shower", "iss", "comet", "events"].forEach((key) => {
      this.shadowRoot.getElementById(key).addEventListener("input", (e) => {
        if (!this._config.entities) this._config.entities = {};
        this._config.entities[key] = e.target.value;
        this._dispatch();
      });
    });

    this.shadowRoot.getElementById("show_sparkline").addEventListener("change", (e) => {
      this._config.show_sparkline = e.target.checked;
      this._dispatch();
    });
  }

  _dispatch() {
    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config: { ...this._config } },
        bubbles: true,
        composed: true,
      })
    );
  }
}

// --- Register ---
customElements.define("night-sky-highlights-2-card", NightSkyHighlights2Card);
customElements.define("night-sky-highlights-2-card-editor", NightSkyHighlights2CardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "night-sky-highlights-2-card",
  name: "ASS Night Sky Highlights 2",
  description: "Enhanced night sky observing highlights with visibility scores, countdowns, and sparklines.",
  preview: true,
});

console.info(
  `%c  NIGHT-SKY-HIGHLIGHTS-2-CARD  %c  v${NSH2_VERSION}  `,
  "background: #1a237e; color: #fff; font-weight: bold;",
  "background: #283593; color: #fff;"
);
