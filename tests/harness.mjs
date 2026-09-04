/**
 * Loads the card bundles in Node with just enough DOM stubs to evaluate them,
 * then hands back the module-internal helpers and card classes for testing.
 *
 * The bundles are plain classic scripts (no import/export), so they can be
 * evaluated with `new Function` and asked to return their internals.
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

export const BUNDLES = {
  astronomy: join(ROOT, "custom_components", "nasa_astronomy", "astronomy-cards.js"),
  deepsky: join(ROOT, "custom_components", "nasa_astronomy", "deepsky-cards.js"),
  astronomyWww: join(ROOT, "www", "community", "astronomy-cards", "astronomy-cards.js"),
  deepskyWww: join(ROOT, "www", "community", "astronomy-cards", "deepsky-cards.js"),
};

class StubElement {
  constructor() {
    this.shadowRoot = null;
  }

  attachShadow() {
    this.shadowRoot = {
      innerHTML: "",
      getElementById: () => ({ addEventListener() {} }),
      querySelector: () => null,
      querySelectorAll: () => [],
    };
    return this.shadowRoot;
  }

  addEventListener() {}

  dispatchEvent() {}

  get isConnected() {
    return false;
  }
}

/**
 * Build the globals a bundle sees.
 *
 * `customElements.define` throws on a name that is already registered, which
 * is what the browser does (`NotSupportedError`, per the custom elements
 * spec). An earlier version of this stub was `registry.set`, i.e. silently
 * idempotent -- more forgiving than the real thing, and forgiving in exactly
 * the direction that hides an unguarded registration block. Every test in this
 * suite passed against a bundle that would have thrown on its first duplicate
 * define in a real browser. A stub may be incomplete; it must not be *kinder*
 * than production, because then the suite reports on the stub.
 */
export function makeSandbox() {
  const registry = new Map();
  const sandbox = {
    HTMLElement: StubElement,
    customElements: {
      get: (name) => registry.get(name),
      define: (name, ctor) => {
        if (registry.has(name)) {
          const err = new Error(
            `Failed to execute 'define' on 'CustomElementRegistry': the name "${name}" has already been used with this registry`,
          );
          err.name = "NotSupportedError";
          throw err;
        }
        registry.set(name, ctor);
      },
      // Not part of the DOM API -- the tests need to see what got registered.
      _names: () => [...registry.keys()],
    },
    document: { createElement: () => new StubElement() },
    console: { info() {}, warn() {}, error() {} },
    CustomEvent: class CustomEvent {
      constructor(type, init) {
        this.type = type;
        Object.assign(this, init);
      }
    },
  };
  sandbox.window = sandbox;
  sandbox.self = sandbox;
  return sandbox;
}

/**
 * Evaluate a bundle against an existing sandbox, so a caller can evaluate the
 * same file twice against one shared `customElements` registry -- the state a
 * browser is in when two Lovelace resources resolve to the same bundle.
 *
 * @param {object} sandbox from `makeSandbox()`
 * @param {string} file absolute path to the bundle
 */
export function evaluateBundleInto(sandbox, file) {
  const source = readFileSync(file, "utf8");
  const keys = Object.keys(sandbox);
  // eslint-disable-next-line no-new-func
  const factory = new Function(...keys, source);
  factory(...keys.map((key) => sandbox[key]));
  return sandbox;
}

/**
 * Evaluate a bundle and return the named top-level bindings it declares.
 *
 * @param {string} file absolute path to the bundle
 * @param {string[]} names top-level function/class names to expose
 */
export function loadBundle(file, names) {
  const source = readFileSync(file, "utf8");
  const sandbox = makeSandbox();
  const keys = Object.keys(sandbox);
  const body = `${source}\n;return { ${names.join(", ")} };`;
  // eslint-disable-next-line no-new-func
  const factory = new Function(...keys, body);
  return factory(...keys.map((key) => sandbox[key]));
}

/** Minimal `hass` stand-in. */
export function makeHass(states, unitSystem = { temperature: "\u00b0C" }) {
  return { states, config: { unit_system: unitSystem } };
}

/** Build a fake HA state object. */
export function makeState(entityId, state, attributes = {}) {
  return { entity_id: entityId, state, attributes };
}

/**
 * Replace a card's shadow root with one that can satisfy the canvas-based dome
 * card, and record every 2D context call so tests can inspect what was drawn.
 *
 * Returns the recorder: `{ calls, fillText, lines }`.
 */
export function stubCanvasShadowRoot(card, { width = 400, height = 333 } = {}) {
  const calls = [];
  const record = (name) => (...args) => { calls.push({ name, args }); };
  const ctx = {
    beginPath: record("beginPath"),
    closePath: record("closePath"),
    ellipse: record("ellipse"),
    arc: record("arc"),
    moveTo: record("moveTo"),
    lineTo: record("lineTo"),
    stroke: record("stroke"),
    fill: record("fill"),
    scale: record("scale"),
    clearRect: record("clearRect"),
    setLineDash: record("setLineDash"),
    fillText: record("fillText"),
    // Deterministic stand-in for the browser's text metrics.
    measureText: (text) => ({ width: String(text).length * 0.55 * 8 }),
  };

  const container = {
    getBoundingClientRect: () => ({ width, height }),
    addEventListener() {},
    setPointerCapture() {},
  };
  const canvas = { style: {}, getContext: () => ctx };

  card.shadowRoot = {
    innerHTML: "",
    getElementById: (id) => (id === "dome" ? canvas : { addEventListener() {} }),
    querySelector: (sel) => (sel === ".dome-container" ? container : null),
    querySelectorAll: () => [],
  };

  return {
    calls,
    get fillText() {
      return calls.filter((c) => c.name === "fillText").map((c) => ({
        text: c.args[0],
        x: c.args[1],
        y: c.args[2],
      }));
    },
    get lines() {
      return calls.filter((c) => c.name === "lineTo").length;
    },
  };
}
