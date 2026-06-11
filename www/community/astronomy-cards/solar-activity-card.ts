import {
  LitElement,
  html,
  css,
  CSSResultGroup,
  TemplateResult,
} from "lit";
import { customElement, property, state } from "lit/decorators.js";

interface SolarActivityCardConfig {
  type: string;
  cme_entity: string;
  flare_entity: string;
  storm_entity: string;
  show_timeline?: boolean;
}

interface SolarEvent {
  activity_id?: string;
  flr_id?: string;
  gst_id?: string;
  start_time?: string;
  begin_time?: string;
  peak_time?: string;
  end_time?: string;
  type?: string;
  class_type?: string;
  kp_index?: number;
  note?: string;
}

@customElement("solar-activity-card")
export class SolarActivityCard extends LitElement {
  @property({ attribute: false }) public hass: any;
  @state() private _config?: SolarActivityCardConfig;

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: block;
        contain: content;
      }
      .solar-card {
        background: var(--ha-card-background, var(--card-background-color, #fff));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, none);
        overflow: hidden;
        padding: 16px;
      }
      .solar-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;
      }
      .solar-header ha-icon {
        color: var(--warning-color, #ff9800);
      }
      .solar-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--primary-text-color);
      }
      .solar-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-bottom: 16px;
      }
      .solar-metric {
        background: var(--secondary-background-color);
        border-radius: 10px;
        padding: 14px 10px;
        text-align: center;
        position: relative;
        overflow: hidden;
      }
      .solar-metric::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
      }
      .solar-metric.cme::before {
        background: #ff6b35;
      }
      .solar-metric.flare::before {
        background: #ffd700;
      }
      .solar-metric.storm::before {
        background: #9c27b0;
      }
      .solar-metric-icon {
        font-size: 1.4rem;
        margin-bottom: 6px;
      }
      .solar-metric-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--primary-text-color);
      }
      .solar-metric-label {
        font-size: 0.7rem;
        color: var(--secondary-text-color);
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
      }
      .solar-timeline {
        border-top: 1px solid var(--divider-color);
        padding-top: 12px;
      }
      .solar-timeline-title {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--secondary-text-color);
        margin-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .solar-timeline-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .solar-event {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 10px;
        border-radius: 6px;
        background: var(--secondary-background-color);
      }
      .solar-event-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        flex-shrink: 0;
      }
      .solar-event-dot.cme { background: #ff6b35; }
      .solar-event-dot.flare { background: #ffd700; }
      .solar-event-dot.storm { background: #9c27b0; }
      .solar-event-info {
        flex: 1;
        min-width: 0;
      }
      .solar-event-type {
        font-size: 0.78rem;
        font-weight: 500;
        color: var(--primary-text-color);
      }
      .solar-event-time {
        font-size: 0.7rem;
        color: var(--secondary-text-color);
      }
      .solar-event-class {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        background: var(--divider-color);
        color: var(--primary-text-color);
      }
      .no-data {
        padding: 24px;
        text-align: center;
        color: var(--secondary-text-color);
      }
      .solar-status {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-size: 0.8rem;
        font-weight: 500;
      }
      .solar-status.calm {
        background: rgba(76, 175, 80, 0.1);
        color: var(--success-color, #4caf50);
      }
      .solar-status.active {
        background: rgba(255, 152, 0, 0.1);
        color: var(--warning-color, #ff9800);
      }
      .solar-status.intense {
        background: rgba(244, 67, 54, 0.1);
        color: var(--error-color, #f44336);
      }
    `;
  }

  setConfig(config: SolarActivityCardConfig): void {
    if (!config.cme_entity || !config.flare_entity || !config.storm_entity) {
      throw new Error("You must define cme_entity, flare_entity, and storm_entity");
    }
    this._config = {
      show_timeline: true,
      ...config,
    };
  }

  protected render(): TemplateResult {
    if (!this._config || !this.hass) {
      return html`<div class="solar-card"><div class="no-data">Loading...</div></div>`;
    }

    const cmeState = this.hass.states[this._config.cme_entity];
    const flareState = this.hass.states[this._config.flare_entity];
    const stormState = this.hass.states[this._config.storm_entity];

    const cmeCount = cmeState ? parseInt(cmeState.state) || 0 : 0;
    const flareCount = flareState ? parseInt(flareState.state) || 0 : 0;
    const stormCount = stormState ? parseInt(stormState.state) || 0 : 0;

    const totalActivity = cmeCount + flareCount + stormCount;
    const statusClass = totalActivity > 10 ? "intense" : totalActivity > 3 ? "active" : "calm";
    const statusText = totalActivity > 10 ? "⚠ Intense Solar Activity" : totalActivity > 3 ? "☀ Elevated Activity" : "✓ Solar Conditions Calm";

    const timelineEvents = this._buildTimeline(cmeState, flareState, stormState);

    return html`
      <div class="solar-card">
        <div class="solar-header">
          <ha-icon icon="mdi:white-balance-sunny"></ha-icon>
          <span class="solar-title">Solar Activity Monitor</span>
        </div>

        <div class="solar-status ${statusClass}">${statusText}</div>

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

        ${this._config.show_timeline && timelineEvents.length > 0
          ? html`
              <div class="solar-timeline">
                <div class="solar-timeline-title">Recent Events</div>
                <div class="solar-timeline-list">
                  ${timelineEvents.slice(0, 6).map(
                    (evt) => html`
                      <div class="solar-event">
                        <div class="solar-event-dot ${evt.category}"></div>
                        <div class="solar-event-info">
                          <div class="solar-event-type">${evt.label}</div>
                          <div class="solar-event-time">${evt.time}</div>
                        </div>
                        ${evt.classType
                          ? html`<span class="solar-event-class">${evt.classType}</span>`
                          : ""}
                      </div>
                    `
                  )}
                </div>
              </div>
            `
          : ""}
      </div>
    `;
  }

  private _buildTimeline(
    cmeState: any,
    flareState: any,
    stormState: any
  ): Array<{ category: string; label: string; time: string; classType?: string }> {
    const events: Array<{ category: string; label: string; time: string; classType?: string; sortTime: string }> = [];

    if (cmeState?.attributes?.events) {
      for (const e of cmeState.attributes.events) {
        events.push({
          category: "cme",
          label: "Coronal Mass Ejection",
          time: this._formatTime(e.start_time),
          sortTime: e.start_time || "",
        });
      }
    }

    if (flareState?.attributes?.events) {
      for (const e of flareState.attributes.events) {
        events.push({
          category: "flare",
          label: "Solar Flare",
          time: this._formatTime(e.begin_time),
          classType: e.class_type,
          sortTime: e.begin_time || "",
        });
      }
    }

    if (stormState?.attributes?.events) {
      for (const e of stormState.attributes.events) {
        events.push({
          category: "storm",
          label: `Geomagnetic Storm${e.kp_index ? ` (Kp${e.kp_index})` : ""}`,
          time: this._formatTime(e.start_time),
          sortTime: e.start_time || "",
        });
      }
    }

    events.sort((a, b) => (b.sortTime > a.sortTime ? 1 : -1));
    return events;
  }

  private _formatTime(timeStr: string | undefined): string {
    if (!timeStr) return "Unknown";
    try {
      const d = new Date(timeStr);
      return d.toLocaleDateString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
    } catch {
      return timeStr;
    }
  }

  getCardSize(): number {
    return 5;
  }

  static getStubConfig() {
    return {
      cme_entity: "sensor.nasa_astronomy_suite_coronal_mass_ejections",
      flare_entity: "sensor.nasa_astronomy_suite_solar_flares",
      storm_entity: "sensor.nasa_astronomy_suite_geomagnetic_storms",
      show_timeline: true,
    };
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "solar-activity-card": SolarActivityCard;
  }
}

(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: "solar-activity-card",
  name: "Solar Activity Card",
  description: "Solar activity monitoring card with CME, flare, and storm tracking",
  preview: true,
});
