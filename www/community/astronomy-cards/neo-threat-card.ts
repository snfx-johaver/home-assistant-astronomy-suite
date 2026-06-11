import {
  LitElement,
  html,
  css,
  CSSResultGroup,
  TemplateResult,
} from "lit";
import { customElement, property, state } from "lit/decorators.js";

interface NeoThreatCardConfig {
  type: string;
  entity: string;
  show_chart?: boolean;
  max_items?: number;
}

interface NeoObject {
  name: string;
  id: string;
  hazardous: boolean;
  diameter_min_m: number;
  diameter_max_m: number;
  velocity_kmh: number;
  miss_distance_km: number;
  close_approach_date: string;
}

@customElement("neo-threat-card")
export class NeoThreatCard extends LitElement {
  @property({ attribute: false }) public hass: any;
  @state() private _config?: NeoThreatCardConfig;

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: block;
        contain: content;
      }
      .neo-card {
        background: var(--ha-card-background, var(--card-background-color, #fff));
        border-radius: var(--ha-card-border-radius, 12px);
        box-shadow: var(--ha-card-box-shadow, none);
        overflow: hidden;
        padding: 16px;
      }
      .neo-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
      }
      .neo-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 1rem;
        font-weight: 600;
        color: var(--primary-text-color);
      }
      .neo-title ha-icon {
        color: var(--warning-color, #ff9800);
      }
      .neo-count-badge {
        background: var(--warning-color, #ff9800);
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
      }
      .neo-count-badge.hazardous {
        background: var(--error-color, #f44336);
      }
      .neo-stats {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 16px;
      }
      .neo-stat {
        background: var(--secondary-background-color);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
      }
      .neo-stat-value {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--primary-text-color);
      }
      .neo-stat-label {
        font-size: 0.7rem;
        color: var(--secondary-text-color);
        margin-top: 2px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
      }
      .neo-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .neo-item {
        display: grid;
        grid-template-columns: auto 1fr auto;
        align-items: center;
        gap: 10px;
        padding: 10px;
        border-radius: 8px;
        background: var(--secondary-background-color);
        transition: background 0.2s;
      }
      .neo-item:hover {
        background: var(--divider-color);
      }
      .neo-hazard-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--success-color, #4caf50);
      }
      .neo-hazard-indicator.dangerous {
        background: var(--error-color, #f44336);
        animation: pulse 2s infinite;
      }
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
      }
      .neo-item-info {
        min-width: 0;
      }
      .neo-item-name {
        font-size: 0.85rem;
        font-weight: 500;
        color: var(--primary-text-color);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .neo-item-details {
        font-size: 0.72rem;
        color: var(--secondary-text-color);
        margin-top: 2px;
      }
      .neo-item-distance {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--primary-text-color);
        text-align: right;
        white-space: nowrap;
      }
      .no-data {
        padding: 24px;
        text-align: center;
        color: var(--secondary-text-color);
      }
    `;
  }

  setConfig(config: NeoThreatCardConfig): void {
    if (!config.entity) {
      throw new Error("You must define an entity");
    }
    this._config = {
      show_chart: true,
      max_items: 8,
      ...config,
    };
  }

  protected render(): TemplateResult {
    if (!this._config || !this.hass) {
      return html`<div class="neo-card"><div class="no-data">Loading...</div></div>`;
    }

    const stateObj = this.hass.states[this._config.entity];
    if (!stateObj) {
      return html`<div class="neo-card"><div class="no-data">Entity not found: ${this._config.entity}</div></div>`;
    }

    const attrs = stateObj.attributes;
    const neoList: NeoObject[] = attrs.neo_list || [];
    const hazardousCount: number = attrs.hazardous_count || 0;
    const totalCount: number = attrs.total_count || parseInt(stateObj.state) || 0;

    const sorted = [...neoList].sort(
      (a, b) => (a.miss_distance_km || Infinity) - (b.miss_distance_km || Infinity)
    );
    const displayed = sorted.slice(0, this._config.max_items);

    const closest = sorted[0];
    const fastest = [...neoList].sort(
      (a, b) => (b.velocity_kmh || 0) - (a.velocity_kmh || 0)
    )[0];

    return html`
      <div class="neo-card">
        <div class="neo-header">
          <div class="neo-title">
            <ha-icon icon="mdi:meteor"></ha-icon>
            Near Earth Objects
          </div>
          <span class="neo-count-badge ${hazardousCount > 0 ? "hazardous" : ""}">
            ${hazardousCount > 0
              ? `⚠ ${hazardousCount} hazardous`
              : `${totalCount} tracked`}
          </span>
        </div>

        <div class="neo-stats">
          <div class="neo-stat">
            <div class="neo-stat-value">${totalCount}</div>
            <div class="neo-stat-label">Total</div>
          </div>
          <div class="neo-stat">
            <div class="neo-stat-value">${closest ? this._formatDistance(closest.miss_distance_km) : "—"}</div>
            <div class="neo-stat-label">Closest</div>
          </div>
          <div class="neo-stat">
            <div class="neo-stat-value">${fastest ? this._formatSpeed(fastest.velocity_kmh) : "—"}</div>
            <div class="neo-stat-label">Fastest</div>
          </div>
        </div>

        <div class="neo-list">
          ${displayed.map(
            (neo) => html`
              <div class="neo-item">
                <div class="neo-hazard-indicator ${neo.hazardous ? "dangerous" : ""}"></div>
                <div class="neo-item-info">
                  <div class="neo-item-name">${neo.name}</div>
                  <div class="neo-item-details">
                    ⌀ ${neo.diameter_max_m?.toFixed(0) || "?"}m · ${this._formatSpeed(neo.velocity_kmh)}
                  </div>
                </div>
                <div class="neo-item-distance">${this._formatDistance(neo.miss_distance_km)}</div>
              </div>
            `
          )}
        </div>
      </div>
    `;
  }

  private _formatDistance(km: number | null): string {
    if (!km) return "—";
    if (km > 1_000_000) return `${(km / 1_000_000).toFixed(1)}M km`;
    if (km > 1_000) return `${(km / 1_000).toFixed(0)}K km`;
    return `${km.toFixed(0)} km`;
  }

  private _formatSpeed(kmh: number | null): string {
    if (!kmh) return "—";
    return `${(kmh / 1000).toFixed(0)}K km/h`;
  }

  getCardSize(): number {
    return 5;
  }

  static getStubConfig() {
    return {
      entity: "sensor.nasa_astronomy_suite_neo_count_today",
      show_chart: true,
      max_items: 8,
    };
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "neo-threat-card": NeoThreatCard;
  }
}

(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: "neo-threat-card",
  name: "NEO Threat Card",
  description: "Near Earth Object threat tracker card",
  preview: true,
});
