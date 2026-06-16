/**
 * Deep-Sky Objects Cards
 * Pre-built bundle for the Astronomy Space Suite (nasa_astronomy) integration.
 *
 * Shadow-DOM custom elements, auto-registered via window.customCards. No global
 * CSS, no external dependencies, no personal data. All cards read the locally
 * computed deep-sky sensors created by sensor_deepsky.py.
 *
 * Cards:
 *  - <deepsky-tonight-card>    Tonight's best telescope targets (table)
 *  - <deepsky-yardmap-card>    Top-down sky map (integration-rendered SVG)
 *  - <deepsky-panorama-card>   Horizon panorama strip (integration-rendered SVG)
 *  - <deepsky-dome-card>       Interactive 3D sky dome (canvas)
 *  - <night-sky-highlights-2-card>  Folded in from the standalone card
 *
 * Default sensor: sensor.nasa_astronomy_deepsky_best_tonight
 */

const DEEPSKY_CARDS_VERSION = "1.0.0";
const DS_DEFAULT_ENTITY = "sensor.nasa_astronomy_deepsky_best_tonight";
const DS_DOCS_URL =
  "https://github.com/snfx-johaver/home-assistant-astronomy-suite";

const DS = {
  radius: "var(--ha-card-border-radius, 12px)",
  surface: "var(--ha-card-background, var(--card-background-color, #fff))",
  text1: "var(--primary-text-color)",
  text2: "var(--secondary-text-color)",
  bg2: "var(--card-background-color, rgba(0,0,0,0.03))",
  divider: "var(--divider-color, rgba(0,0,0,0.08))",
  green: "var(--success-color, #4caf50)",
  amber: "var(--warning-color, #ff9800)",
  red: "var(--error-color, #f44336)",
  info: "var(--info-color, #42a5f5)",
};

function dsDefineElement(name, ctor) {
  if (!customElements.get(name)) customElements.define(name, ctor);
}

function dsRegisterCard(type, name, description) {
  window.customCards = window.customCards || [];
  if (!window.customCards.some((c) => c.type === type)) {
    window.customCards.push({
      type,
      name,
      description,
      preview: true,
      documentationURL: DS_DOCS_URL,
    });
  }
}

function dsEsc(s) {
  return String(s == null ? "" : s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
  );
}

function dsState(hass, entity) {
  if (!hass || !entity) return null;
  const st = hass.states[entity];
  if (!st || st.state === "unavailable" || st.state === "unknown") return null;
  return st;
}

// ─── Tonight table card ──────────────────────────────────────────────────────
class DeepSkyTonightCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
  }

  static getStubConfig() {
    return { entity: DS_DEFAULT_ENTITY, title: "Deep-Sky Tonight" };
  }

  setConfig(config) {
    this._config = {
      entity: config.entity || DS_DEFAULT_ENTITY,
      title: config.title || "Deep-Sky Tonight",
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 7;
  }

  _statusColor(status) {
    if (status === "Now") return DS.green;
    if (status === "Up") return DS.info;
    if (status === "Later") return DS.amber;
    return DS.text2;
  }

  _render() {
    const st = dsState(this._hass, this._config.entity);
    const head = `
      <style>
        :host { display: block; }
        ha-card { padding: 16px; }
        .head { display:flex; align-items:baseline; justify-content:space-between;
          gap:8px; margin-bottom:12px; }
        .title { font-size:1.2em; font-weight:500; color:${DS.text1}; }
        .count { font-size:0.8em; color:${DS.text2}; }
        table { width:100%; border-collapse:collapse; font-size:0.85em; }
        th { text-align:left; color:${DS.text2}; font-weight:600;
          padding:4px 8px; border-bottom:1px solid ${DS.divider};
          font-size:0.82em; }
        td { padding:6px 8px; border-bottom:1px solid ${DS.divider};
          color:${DS.text1}; vertical-align:middle; }
        td.num { font-variant-numeric:tabular-nums; white-space:nowrap; }
        .badge { display:inline-block; font-size:0.72em; font-weight:600;
          color:#fff; padding:2px 8px; border-radius:10px; white-space:nowrap; }
        .name { font-weight:500; }
        .type { color:${DS.text2}; font-size:0.85em; }
        .empty { text-align:center; padding:28px 8px; color:${DS.text2}; }
      </style>`;

    if (!st) {
      this.shadowRoot.innerHTML = `${head}
        <ha-card>
          <div class="head"><div class="title">${dsEsc(
            this._config.title
          )}</div></div>
          <div class="empty">Waiting for ${dsEsc(
            this._config.entity
          )}…</div>
        </ha-card>`;
      return;
    }

    const objects = Array.isArray(st.attributes.objects)
      ? st.attributes.objects
      : [];
    const hasYard = objects.some((o) => o && o.yard != null);
    const count = st.state;

    const rows = objects
      .map((o) => {
        const yardCell = hasYard
          ? `<td>${dsEsc(o.yard)}</td>`
          : "";
        return `
        <tr>
          <td><span class="name">${dsEsc(o.name)}</span>
            <span class="type">· ${dsEsc(o.type)}</span></td>
          <td class="num">${dsEsc(o.altitude)}°</td>
          <td>${dsEsc(o.direction)}</td>
          <td>${dsEsc(o.window)}</td>
          <td><span class="badge" style="background:${this._statusColor(
            o.status
          )}">${dsEsc(o.status)}</span></td>
          ${yardCell}
        </tr>`;
      })
      .join("");

    const body = objects.length
      ? `<table>
          <thead><tr>
            <th>Object</th><th>Alt</th><th>Dir</th>
            <th>Window</th><th>Status</th>${hasYard ? "<th>Yard</th>" : ""}
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>`
      : `<div class="empty">No catalog objects up tonight.</div>`;

    this.shadowRoot.innerHTML = `${head}
      <ha-card>
        <div class="head">
          <div class="title">${dsEsc(this._config.title)}</div>
          <div class="count">${dsEsc(count)} observable now</div>
        </div>
        ${body}
      </ha-card>`;
  }
}

// ─── SVG cards (yard-map + panorama) ─────────────────────────────────────────
class DeepSkySvgCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._lastUrl = "";
  }

  // Overridden by subclasses.
  get _urlAttr() {
    return "map_url";
  }
  get _defaultTitle() {
    return "Deep-Sky";
  }

  setConfig(config) {
    this._config = {
      entity: config.entity || DS_DEFAULT_ENTITY,
      title: config.title || this._defaultTitle,
      ...config,
    };
    this._lastUrl = "";
    this._shell();
  }

  set hass(hass) {
    this._hass = hass;
    this._maybeFetch();
  }

  getCardSize() {
    return 6;
  }

  _shell() {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        ha-card { padding:12px 12px 8px; }
        .title { font-size:1.1em; font-weight:500; color:${DS.text1};
          margin-bottom:8px; }
        .holder { width:100%; }
        .holder svg { width:100%; height:auto; display:block;
          border-radius:8px; }
        .empty { text-align:center; padding:28px 8px; color:${DS.text2};
          font-size:0.9em; }
      </style>
      <ha-card>
        <div class="title">${dsEsc(this._config.title)}</div>
        <div class="holder"><div class="empty">Waiting for sky map…</div></div>
      </ha-card>`;
  }

  _maybeFetch() {
    const st = dsState(this._hass, this._config.entity);
    if (!st) return;
    const url = st.attributes[this._urlAttr];
    if (!url || url === this._lastUrl) return;
    this._lastUrl = url;
    fetch(url, { cache: "no-store" })
      .then((r) => (r.ok ? r.text() : Promise.reject(r.status)))
      .then((svg) => {
        const holder = this.shadowRoot.querySelector(".holder");
        if (holder && svg.indexOf("<svg") !== -1) holder.innerHTML = svg;
      })
      .catch(() => {
        /* leave the prior frame in place on a transient error */
      });
  }
}

class DeepSkyYardMapCard extends DeepSkySvgCard {
  static getStubConfig() {
    return { entity: DS_DEFAULT_ENTITY, title: "Deep-Sky Sky Map" };
  }
  get _urlAttr() {
    return "map_url";
  }
  get _defaultTitle() {
    return "Deep-Sky Sky Map";
  }
}

class DeepSkyPanoramaCard extends DeepSkySvgCard {
  static getStubConfig() {
    return { entity: DS_DEFAULT_ENTITY, title: "Deep-Sky Panorama" };
  }
  get _urlAttr() {
    return "pano_url";
  }
  get _defaultTitle() {
    return "Deep-Sky Panorama";
  }
  getCardSize() {
    return 4;
  }
}

// ─── 3D dome card (canvas) ───────────────────────────────────────────────────
const DS_D2R = Math.PI / 180;
const DS_KIND = {
  deepsky: "#5bd6ff",
  planet: "#ffd24a",
  moon: "#e8e8e8",
  sun: "#ff8c2a",
};
const DS_CARDINALS = [
  [0, "N"],
  [45, "NE"],
  [90, "E"],
  [135, "SE"],
  [180, "S"],
  [225, "SW"],
  [270, "W"],
  [315, "NW"],
];

function dsVec(az, alt) {
  const ca = Math.cos(alt * DS_D2R);
  return [ca * Math.sin(az * DS_D2R), Math.sin(alt * DS_D2R), ca * Math.cos(az * DS_D2R)];
}
function dsDot(a, b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}
function dsBasis(yaw, pitch) {
  const f = dsVec(yaw, pitch);
  const rx = f[2],
    rz = -f[0],
    rl = Math.hypot(rx, rz) || 1e-6;
  const r = [rx / rl, 0, rz / rl];
  const u = [
    f[1] * r[2] - f[2] * r[1],
    f[2] * r[0] - f[0] * r[2],
    f[0] * r[1] - f[1] * r[0],
  ];
  return { f, r, u };
}
function dsProject(P, b, focal, W, H) {
  const f = dsDot(P, b.f);
  if (f <= 0.12) return null;
  return [W / 2 + (dsDot(P, b.r) / f) * focal, H / 2 - (dsDot(P, b.u) / f) * focal, f];
}
function dsDirName(a) {
  const n = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
  ];
  return n[Math.round((((a % 360) + 360) % 360) / 22.5) % 16];
}

class DeepSkyDomeCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._yaw = 180;
    this._pitch = 22;
    this._fov = 72;
    this._w = 0;
    this._h = 0;
    this._dpr = 1;
    this._data = { objects: [], horizon: null, now: "" };
    this._pts = {};
    this._last = null;
    this._pinch0 = 0;
    this._fov0 = 0;
    this._built = false;
  }

  static getStubConfig() {
    return { entity: DS_DEFAULT_ENTITY, title: "Deep-Sky Dome" };
  }

  setConfig(config) {
    this._config = {
      entity: config.entity || DS_DEFAULT_ENTITY,
      title: config.title || "Deep-Sky Dome",
      height: config.height || 360,
      ...config,
    };
    if (this._built) this._applyHeight();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) this._build();
    this._ingest();
  }

  getCardSize() {
    return 8;
  }

  connectedCallback() {
    if (this._hass && !this._built) this._build();
  }

  _applyHeight() {
    const wrap = this.shadowRoot.querySelector(".wrap");
    if (wrap) wrap.style.height = `${this._config.height}px`;
  }

  _build() {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; }
        ha-card { padding:0; overflow:hidden; }
        .wrap { position:relative; width:100%; height:${this._config.height}px;
          background:#05080f; border-radius:${DS.radius}; overflow:hidden;
          touch-action:none; }
        canvas { position:absolute; inset:0; width:100%; height:100%;
          display:block; cursor:grab; }
        canvas.drag { cursor:grabbing; }
        .ov { position:absolute; pointer-events:none; color:#cfe3f2;
          text-shadow:0 1px 3px #000, 0 0 6px #000;
          font-family:system-ui, sans-serif; }
        .facing { top:10px; left:12px; font-size:18px; font-weight:700; }
        .sub { top:34px; left:12px; font-size:12px; color:#8aa0b2; }
        .stamp { top:10px; right:12px; font-size:12px; color:#8aa0b2;
          text-align:right; }
        .hint { bottom:8px; left:50%; transform:translateX(-50%);
          font-size:11px; color:#7d93a6; white-space:nowrap; }
        .empty { position:absolute; inset:0; display:flex; align-items:center;
          justify-content:center; color:#8aa0b2; font-size:13px;
          font-family:system-ui, sans-serif; }
      </style>
      <ha-card>
        <div class="wrap">
          <canvas></canvas>
          <div class="ov facing">Facing —</div>
          <div class="ov sub">tilt —</div>
          <div class="ov stamp"></div>
          <div class="ov hint">Drag to look around · scroll / pinch to zoom</div>
          <div class="empty">Waiting for sky data…</div>
        </div>
      </ha-card>`;

    this._wrap = this.shadowRoot.querySelector(".wrap");
    this._cv = this.shadowRoot.querySelector("canvas");
    this._ctx = this._cv.getContext("2d");
    this._built = true;
    this._bindEvents();

    if (window.ResizeObserver) {
      this._ro = new ResizeObserver(() => this._resize());
      this._ro.observe(this._wrap);
    }
    this._resize();
  }

  _bindEvents() {
    const cv = this._cv;
    const pdist = () => {
      const a = Object.keys(this._pts).map((k) => this._pts[k]);
      return Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y);
    };
    const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);

    cv.addEventListener("pointerdown", (e) => {
      cv.setPointerCapture(e.pointerId);
      this._pts[e.pointerId] = { x: e.clientX, y: e.clientY };
      this._last = { x: e.clientX, y: e.clientY };
      cv.classList.add("drag");
      if (Object.keys(this._pts).length === 2) {
        this._pinch0 = pdist();
        this._fov0 = this._fov;
      }
    });
    cv.addEventListener("pointermove", (e) => {
      if (!this._pts[e.pointerId]) return;
      this._pts[e.pointerId] = { x: e.clientX, y: e.clientY };
      if (Object.keys(this._pts).length >= 2) {
        const d = pdist();
        if (this._pinch0 > 0) {
          this._fov = clamp((this._fov0 * this._pinch0) / d, 32, 104);
          this._draw();
        }
        return;
      }
      if (this._last) {
        this._yaw -= (e.clientX - this._last.x) * 0.18;
        this._pitch = clamp(this._pitch + (e.clientY - this._last.y) * 0.18, -12, 82);
        this._last = { x: e.clientX, y: e.clientY };
        this._draw();
      }
    });
    const up = (e) => {
      delete this._pts[e.pointerId];
      if (Object.keys(this._pts).length < 2) this._pinch0 = 0;
      if (Object.keys(this._pts).length === 0) {
        this._last = null;
        cv.classList.remove("drag");
      }
    };
    cv.addEventListener("pointerup", up);
    cv.addEventListener("pointercancel", up);
    cv.addEventListener(
      "wheel",
      (e) => {
        e.preventDefault();
        this._fov = clamp(this._fov + (e.deltaY > 0 ? 4 : -4), 32, 104);
        this._draw();
      },
      { passive: false }
    );
  }

  _resize() {
    if (!this._wrap) return;
    this._dpr = Math.min(window.devicePixelRatio || 1, 2);
    this._w = this._wrap.clientWidth;
    this._h = this._wrap.clientHeight;
    this._cv.width = Math.round(this._w * this._dpr);
    this._cv.height = Math.round(this._h * this._dpr);
    this._ctx.setTransform(this._dpr, 0, 0, this._dpr, 0, 0);
    this._draw();
  }

  _ingest() {
    const st = dsState(this._hass, this._config.entity);
    const empty = this.shadowRoot && this.shadowRoot.querySelector(".empty");
    if (!st) {
      if (empty) empty.style.display = "flex";
      return;
    }
    const objs = Array.isArray(st.attributes.sky_objects)
      ? st.attributes.sky_objects
      : [];
    const hz = st.attributes.sky_horizon;
    this._data = {
      objects: objs.filter((o) => o && o.alt > -2),
      horizon: Array.isArray(hz) && hz.length === 360 ? hz : null,
      now: st.attributes.sky_now || "",
    };
    if (empty) empty.style.display = objs.length ? "none" : "flex";
    this._draw();
  }

  _draw() {
    if (!this._built || !this._w) return;
    const ctx = this._ctx,
      W = this._w,
      H = this._h;
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "#05070f");
    g.addColorStop(0.55, "#0a1430");
    g.addColorStop(1, "#16284a");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    const b = dsBasis(this._yaw, this._pitch);
    const focal = H / 2 / Math.tan((this._fov * DS_D2R) / 2);
    const yaw = this._yaw;
    const hz =
      this._data.horizon && this._data.horizon.length === 360
        ? this._data.horizon
        : null;

    // Diagram horizon wall (only when a horizon profile is configured).
    if (hz) {
      const step = 1.5;
      for (let k = -118; k <= 118; k += step) {
        const a0 = yaw + k,
          a1 = yaw + k + step;
        const t0 = hz[(((Math.round(a0) % 360) + 360) % 360)];
        const t1 = hz[(((Math.round(a1) % 360) + 360) % 360)];
        const p1 = dsProject(dsVec(a0, -5), b, focal, W, H);
        const p2 = dsProject(dsVec(a1, -5), b, focal, W, H);
        const p3 = dsProject(dsVec(a1, t1), b, focal, W, H);
        const p4 = dsProject(dsVec(a0, t0), b, focal, W, H);
        if (!p1 || !p2 || !p3 || !p4) continue;
        ctx.beginPath();
        ctx.moveTo(p1[0], p1[1]);
        ctx.lineTo(p2[0], p2[1]);
        ctx.lineTo(p3[0], p3[1]);
        ctx.lineTo(p4[0], p4[1]);
        ctx.closePath();
        ctx.fillStyle = "#0b160e";
        ctx.fill();
        ctx.strokeStyle = "rgba(56,97,63,0.55)";
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }

    // Horizon reference line (alt 0).
    ctx.lineWidth = 1;
    ctx.strokeStyle = "rgba(120,150,175,0.35)";
    ctx.beginPath();
    let started = false;
    for (let k = -118; k <= 118; k += 3) {
      const p = dsProject(dsVec(yaw + k, 0), b, focal, W, H);
      if (!p) {
        started = false;
        continue;
      }
      if (!started) {
        ctx.moveTo(p[0], p[1]);
        started = true;
      } else ctx.lineTo(p[0], p[1]);
    }
    ctx.stroke();

    // Cardinal letters.
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    for (let ci = 0; ci < DS_CARDINALS.length; ci++) {
      const pc = dsProject(dsVec(DS_CARDINALS[ci][0], 1.2), b, focal, W, H);
      if (!pc) continue;
      const big = DS_CARDINALS[ci][0] % 90 === 0;
      ctx.font = (big ? "700 17px" : "600 12px") + " system-ui, sans-serif";
      ctx.fillStyle = big ? "#cfe3f2" : "#86a0b4";
      ctx.lineWidth = 3;
      ctx.strokeStyle = "#05080f";
      ctx.strokeText(DS_CARDINALS[ci][1], pc[0], pc[1]);
      ctx.fillText(DS_CARDINALS[ci][1], pc[0], pc[1]);
    }

    // Objects.
    for (let i = 0; i < this._data.objects.length; i++) {
      const o = this._data.objects[i];
      const p = dsProject(dsVec(o.az, o.alt), b, focal, W, H);
      if (!p) continue;
      const blocked = o.tier === "blocked",
        stepTier = o.tier === "step";
      const col = blocked
        ? "#d9534f"
        : stepTier
        ? "#ff9f40"
        : DS_KIND[o.kind] || "#5bd6ff";
      const bright = o.bright !== false;
      const rad = o.kind !== "deepsky" && bright && !blocked ? 6 : 4.5;
      ctx.globalAlpha = blocked ? 0.5 : bright ? 1 : 0.6;
      if (!blocked && bright) {
        ctx.beginPath();
        ctx.arc(p[0], p[1], rad + 6, 0, 7);
        ctx.fillStyle = col;
        ctx.globalAlpha *= 0.18;
        ctx.fill();
        ctx.globalAlpha = blocked ? 0.5 : bright ? 1 : 0.6;
      }
      ctx.beginPath();
      ctx.arc(p[0], p[1], rad, 0, 7);
      ctx.fillStyle = col;
      ctx.fill();
      ctx.lineWidth = 1;
      ctx.strokeStyle = "#05080f";
      ctx.stroke();
      const lab = o.short + (blocked ? "" : "  " + Math.round(o.alt) + "\u00b0");
      ctx.font = "600 12px system-ui, sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.lineWidth = 3;
      ctx.strokeStyle = "#05080f";
      ctx.fillStyle = blocked || !bright ? "#9fb3c4" : "#eaf3fb";
      ctx.strokeText(lab, p[0] + rad + 4, p[1]);
      ctx.fillText(lab, p[0] + rad + 4, p[1]);
      ctx.globalAlpha = 1;
    }

    // Overlays.
    const facing = this.shadowRoot.querySelector(".facing");
    const sub = this.shadowRoot.querySelector(".sub");
    const stamp = this.shadowRoot.querySelector(".stamp");
    if (facing)
      facing.textContent =
        "Facing " +
        dsDirName(yaw) +
        "  " +
        Math.round(((yaw % 360) + 360) % 360) +
        "\u00b0";
    if (sub)
      sub.textContent =
        "tilt " +
        Math.round(this._pitch) +
        "\u00b0 up \u00b7 zoom " +
        Math.round(this._fov) +
        "\u00b0";
    if (stamp) stamp.textContent = this._data.now || "";
  }
}

// ─── Night Sky Highlights 2 (folded in from the standalone card) ─────────────
const NSH2_VERSION = "1.0.0";

const NSH2_STYLES = `
  :host { display: block; }
  .nsh2-card {
    padding: 16px;
    border-radius: var(--ha-card-border-radius, 12px);
    background: var(--ha-card-background, var(--card-background-color, #fff));
    box-shadow: var(--ha-card-box-shadow, none);
    color: var(--primary-text-color);
    font-family: var(--paper-font-body1_-_font-family, 'Roboto', sans-serif);
  }
  .nsh2-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  .nsh2-title { font-size: 1.2em; font-weight: 500; color: var(--primary-text-color); }
  .nsh2-subtitle { font-size: 0.75em; color: var(--secondary-text-color); opacity: 0.7; }
  .nsh2-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }
  .nsh2-tile {
    display: flex; flex-direction: column; padding: 14px; border-radius: 10px;
    background: var(--card-background-color, rgba(0,0,0,0.03));
    border: 1px solid var(--divider-color, rgba(0,0,0,0.08));
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }
  .nsh2-tile:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
  .nsh2-tile-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .nsh2-icon {
    font-size: 1.6em; width: 36px; height: 36px; display: flex; align-items: center;
    justify-content: center; border-radius: 8px;
    background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
  }
  .nsh2-tile-title { font-size: 0.95em; font-weight: 500; flex: 1; }
  .nsh2-visibility-badge {
    font-size: 0.7em; font-weight: 600; padding: 3px 8px; border-radius: 12px;
    color: #fff; min-width: 32px; text-align: center;
  }
  .nsh2-vis-green { background: #4caf50; }
  .nsh2-vis-yellow { background: #ff9800; }
  .nsh2-vis-red { background: #f44336; }
  .nsh2-description { font-size: 0.82em; color: var(--secondary-text-color); margin-bottom: 8px; line-height: 1.4; }
  .nsh2-footer { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  .nsh2-badge {
    font-size: 0.65em; font-weight: 600; text-transform: uppercase; padding: 2px 7px;
    border-radius: 6px; background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
    color: var(--primary-color, #03a9f4); letter-spacing: 0.3px;
  }
  .nsh2-countdown { font-size: 0.75em; color: var(--secondary-text-color); margin-left: auto; font-variant-numeric: tabular-nums; }
  .nsh2-sparkline { margin-top: 8px; height: 30px; width: 100%; }
  .nsh2-sparkline svg { width: 100%; height: 100%; }
  .nsh2-sparkline path { fill: none; stroke: var(--primary-color, #03a9f4); stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }
  .nsh2-sparkline .nsh2-spark-fill { fill: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1); stroke: none; }
  .nsh2-unavailable { opacity: 0.4; pointer-events: none; }
  .nsh2-empty { text-align: center; padding: 32px 16px; color: var(--secondary-text-color); font-size: 0.9em; }
  @media (max-width: 600px) { .nsh2-grid { grid-template-columns: 1fr; } }
`;

class NightSkyHighlights2Card extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
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
    const badgesHtml = (badges || []).map((b) => `<span class="nsh2-badge">${b}</span>`).join("");
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
      return this._buildTile(defaults.icon, defaults.title, null, "Sensor unavailable", [], "", null, true);
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
        <div class="field"><label>Best Planet Tonight</label><input type="text" id="best_planet" value="${entities.best_planet || ""}" /></div>
        <div class="field"><label>Best DSO Tonight</label><input type="text" id="best_dso" value="${entities.best_dso || ""}" /></div>
        <div class="field"><label>Meteor Shower Activity</label><input type="text" id="meteor_shower" value="${entities.meteor_shower || ""}" /></div>
        <div class="field"><label>ISS Next Pass</label><input type="text" id="iss" value="${entities.iss || ""}" /></div>
        <div class="field"><label>Brightest Comet</label><input type="text" id="comet" value="${entities.comet || ""}" /></div>
        <div class="field"><label>Special Events</label><input type="text" id="events" value="${entities.events || ""}" /></div>
        <div class="field" style="margin-top:16px;">
          <label>
            <input type="checkbox" id="show_sparkline" ${this._config.show_sparkline !== false ? "checked" : ""} />
            Show altitude sparkline (if available)
          </label>
        </div>
      </div>
    `;

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

// ─── Register ────────────────────────────────────────────────────────────────
dsDefineElement("deepsky-tonight-card", DeepSkyTonightCard);
dsDefineElement("deepsky-yardmap-card", DeepSkyYardMapCard);
dsDefineElement("deepsky-panorama-card", DeepSkyPanoramaCard);
dsDefineElement("deepsky-dome-card", DeepSkyDomeCard);
dsDefineElement("night-sky-highlights-2-card", NightSkyHighlights2Card);
dsDefineElement("night-sky-highlights-2-card-editor", NightSkyHighlights2CardEditor);

dsRegisterCard("deepsky-tonight-card", "ASS Deep-Sky Tonight", "Tonight's best telescope targets from the local deep-sky catalog.");
dsRegisterCard("deepsky-yardmap-card", "ASS Deep-Sky Sky Map", "Top-down sky map of deep-sky objects and solar-system bodies.");
dsRegisterCard("deepsky-panorama-card", "ASS Deep-Sky Panorama", "Horizon panorama strip showing what is up right now.");
dsRegisterCard("deepsky-dome-card", "ASS Deep-Sky Dome", "Interactive 3D sky dome you can drag and zoom.");
dsRegisterCard("night-sky-highlights-2-card", "ASS Night Sky Highlights 2", "Enhanced night sky observing highlights with visibility scores and countdowns.");

console.info(
  `%c Deep-Sky Objects Cards v${DEEPSKY_CARDS_VERSION} %c`,
  "color:white;background:#1a237e;font-weight:bold;padding:2px 8px;border-radius:4px 0 0 4px;",
  "color:#1a237e;background:#e8eaf6;font-weight:bold;padding:2px 8px;border-radius:0 4px 4px 0;"
);
