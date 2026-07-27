/*
 * Test harness for the app-shell modules.
 *
 * frontend/app/*.js are plain browser scripts (no bundler, no exports) that
 * attach themselves to window.PatentFormsApp. This harness gives them the
 * globals they expect — window, document, localStorage — so the real
 * production files can be loaded and exercised in Node without a browser.
 *
 * The DOM shim is deliberately minimal: just enough of the element API that
 * the app shell actually uses. It is not a jsdom substitute, and it is not
 * meant to become one — if a test needs real layout or real events, that
 * belongs in a browser, not here.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const HERE = dirname(fileURLToPath(import.meta.url));
export const PROJECT_ROOT = join(HERE, "..", "..");
export const APP_DIR = join(PROJECT_ROOT, "frontend", "app");

// --------------------------------------------------------------- localStorage

class FakeStorage {
  constructor() { this._data = new Map(); }
  getItem(key) { return this._data.has(key) ? this._data.get(key) : null; }
  setItem(key, value) { this._data.set(key, String(value)); }
  removeItem(key) { this._data.delete(key); }
  clear() { this._data.clear(); }
  get length() { return this._data.size; }
  key(i) { return Array.from(this._data.keys())[i] ?? null; }
}

// ------------------------------------------------------------------- DOM shim

class FakeElement {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.parentNode = null;
    this.listeners = new Map();
    this.style = {};
    this.attributes = {};
    this._className = "";
    this._textContent = "";
    this.classList = {
      add: (c) => { if (!this._classes().includes(c)) this._className = (this._className + " " + c).trim(); },
      remove: (c) => { this._className = this._classes().filter((x) => x !== c).join(" "); },
      contains: (c) => this._classes().includes(c),
      toggle: (c) => (this.classList.contains(c) ? this.classList.remove(c) : this.classList.add(c)),
    };
  }

  _classes() { return this._className.split(/\s+/).filter(Boolean); }

  get className() { return this._className; }
  set className(v) { this._className = v == null ? "" : String(v); }

  get textContent() {
    if (this.children.length) return this.children.map((c) => c.textContent).join("");
    return this._textContent;
  }
  set textContent(v) { this._textContent = v == null ? "" : String(v); this.children = []; }

  get innerHTML() { return ""; }
  set innerHTML(_v) { this.children = []; }

  appendChild(child) { child.parentNode = this; this.children.push(child); return child; }
  removeChild(child) { this.children = this.children.filter((c) => c !== child); return child; }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  getAttribute(name) { return this.attributes[name] ?? null; }

  addEventListener(type, fn) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(fn);
  }

  /** Fire every listener registered for `type`. */
  dispatch(type, event = {}) {
    for (const fn of this.listeners.get(type) || []) fn(event);
  }
  click() { this.dispatch("click"); }

  /** Depth-first walk of this element and all descendants. */
  *walk() {
    yield this;
    for (const child of this.children) yield* child.walk();
  }
}

// ------------------------------------------------------------------ the world

/**
 * Build a fresh global environment and return handles to it.
 * Call this in beforeEach so no state leaks between tests.
 */
export function createEnvironment() {
  const localStorage = new FakeStorage();
  const document = {
    createElement: (tag) => new FakeElement(tag),
    baseURI: "http://localhost/frontend/app/index.html",
  };
  const window = {
    localStorage,
    document,
    confirm: () => true,
    PatentFormsApp: {},
  };

  globalThis.window = window;
  globalThis.document = document;
  globalThis.localStorage = localStorage;

  return { window, document, localStorage };
}

/**
 * Load one real file from frontend/app/ into the current environment.
 * Scripts must be loaded in dependency order, exactly as index.html does.
 */
export function loadAppScript(filename) {
  const code = readFileSync(join(APP_DIR, filename), "utf8");
  vm.runInThisContext(code, { filename });
  return globalThis.window.PatentFormsApp;
}

/** Convenience: fresh environment + the named scripts, in order. */
export function bootstrap(...filenames) {
  const env = createEnvironment();
  for (const name of filenames) loadAppScript(name);
  return { ...env, ns: env.window.PatentFormsApp };
}

// ------------------------------------------------------------------- helpers

export function makeContainer() { return new FakeElement("div"); }

/** Find the first descendant whose textContent matches exactly. */
export function findByText(root, text) {
  for (const node of root.walk()) {
    if (node.tagName === "BUTTON" && node.textContent === text) return node;
  }
  for (const node of root.walk()) {
    if (node.textContent === text) return node;
  }
  return null;
}

/** Find the first descendant carrying a CSS class. */
export function findByClass(root, className) {
  for (const node of root.walk()) {
    if (node.classList.contains(className)) return node;
  }
  return null;
}

/**
 * Stub of the approved FormRenderer contract.
 *
 * mount/getValues/setValues/getGaps/getFindings/unmount — nothing more. Using
 * only this surface is what proves the app shell never needed renderer changes
 * to separate suggested from user-entered values.
 */
export function installRendererStub() {
  const record = {
    mountCount: 0,
    initialValues: null,
    values: {},
    callbacks: null,
    setValuesCalls: [],
    unmounted: false,
  };

  globalThis.window.FormRenderer = {
    mount(container, definition, initialValues, callbacks) {
      record.mountCount += 1;
      record.initialValues = JSON.parse(JSON.stringify(initialValues || {}));
      record.values = JSON.parse(JSON.stringify(initialValues || {}));
      record.callbacks = callbacks || {};
      record.container = container;
      record.definition = definition;

      return {
        getValues: () => JSON.parse(JSON.stringify(record.values)),
        setValues: (v) => {
          record.setValuesCalls.push(JSON.parse(JSON.stringify(v || {})));
          record.values = JSON.parse(JSON.stringify(v || {}));
        },
        getGaps: () => [],
        getFindings: () => [],
        unmount: () => { record.unmounted = true; },
      };
    },
  };

  /** Simulate the user editing the form: updates state, then notifies. */
  record.userEdits = (changes) => {
    record.values = { ...record.values, ...changes };
    record.callbacks.onChange(JSON.parse(JSON.stringify(record.values)));
  };

  return record;
}
