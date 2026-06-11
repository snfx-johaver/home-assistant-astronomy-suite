import {
  LitElement,
  html,
  css,
  CSSResultGroup,
  TemplateResult,
  PropertyValues,
} from "lit";
import { customElement, property, state } from "lit/decorators.js";

interface ApodCardConfig {
  type: string;
  entity: string;
  show_explanation?: boolean;
  show_copyright?: boolean;
}

@customElement("apod-card")
export class ApodCard extends LitElement {
  @property({ attribute: false }) public hass: any;
  @state() private _config?: ApodCardConfig;

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: block;
        contain: content;
      }
      .apod-card {
        position: relative;
        border-radius: var(--ha-card-border-radius, 12px);
        overflow: hidden;
        background: var(--ha-card-background, var(--card-background-color, #fff));
        box-shadow: var(--ha-card-box-shadow, none);
      }
      .apod-image-container {
        position: relative;
        width: 100%;
        min-height: 200px;
        overflow: hidden;
      }
      .apod-image-container img {
        width: 100%;
        height: auto;
        display: block;
        object-fit: cover;
        max-height: 400px;
      }
      .apod-video-container {
        position: relative;
        width: 100%;
        padding-bottom: 56.25%;
      }
      .apod-video-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: none;
      }
      .apod-overlay {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(transparent, rgba(0, 0, 0, 0.85));
        padding: 40px 16px 16px;
        color: white;
      }
      .apod-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0 0 4px;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
      }
      .apod-date {
        font-size: 0.8rem;
        opacity: 0.8;
      }
      .apod-explanation {
        padding: 12px 16px;
        font-size: 0.85rem;
        line-height: 1.4;
        color: var(--primary-text-color);
        max-height: 120px;
        overflow-y: auto;
      }
      .apod-footer {
        padding: 8px 16px 12px;
        font-size: 0.75rem;
        opacity: 0.6;
        color: var(--secondary-text-color);
      }
      .apod-badge {
        position: absolute;
        top: 12px;
        left: 12px;
        background: rgba(0, 0, 0, 0.6);
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
      }
      .no-data {
        padding: 24px 16px;
        text-align: center;
        color: var(--secondary-text-color);
      }
    `;
  }

  setConfig(config: ApodCardConfig): void {
    if (!config.entity) {
      throw new Error("You must define an entity");
    }
    this._config = {
      show_explanation: true,
      show_copyright: true,
      ...config,
    };
  }

  protected render(): TemplateResult {
    if (!this._config || !this.hass) {
      return html`<ha-card><div class="no-data">Loading...</div></ha-card>`;
    }

    const stateObj = this.hass.states[this._config.entity];
    if (!stateObj) {
      return html`<ha-card><div class="no-data">Entity not found: ${this._config.entity}</div></ha-card>`;
    }

    const attrs = stateObj.attributes;
    const title = attrs.title || stateObj.state;
    const explanation = attrs.explanation || "";
    const url = attrs.url || "";
    const date = attrs.date || "";
    const mediaType = attrs.media_type || "image";
    const copyright = attrs.copyright || "";

    return html`
      <div class="apod-card">
        ${mediaType === "image"
          ? html`
              <div class="apod-image-container">
                <img src="${url}" alt="${title}" loading="lazy" />
                <div class="apod-badge">NASA APOD</div>
                <div class="apod-overlay">
                  <p class="apod-title">${title}</p>
                  <span class="apod-date">${date}</span>
                </div>
              </div>
            `
          : html`
              <div class="apod-video-container">
                <iframe src="${url}" allowfullscreen></iframe>
              </div>
              <div style="padding: 12px 16px;">
                <p class="apod-title" style="color: var(--primary-text-color);">${title}</p>
                <span class="apod-date" style="color: var(--secondary-text-color);">${date}</span>
              </div>
            `}
        ${this._config.show_explanation && explanation
          ? html`<div class="apod-explanation">${explanation}</div>`
          : ""}
        ${this._config.show_copyright && copyright
          ? html`<div class="apod-footer">© ${copyright}</div>`
          : ""}
      </div>
    `;
  }

  getCardSize(): number {
    return 6;
  }

  static getStubConfig() {
    return {
      entity: "sensor.nasa_astronomy_suite_apod",
      show_explanation: true,
      show_copyright: true,
    };
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "apod-card": ApodCard;
  }
}

(window as any).customCards = (window as any).customCards || [];
(window as any).customCards.push({
  type: "apod-card",
  name: "APOD Card",
  description: "NASA Astronomy Picture of the Day card",
  preview: true,
});
