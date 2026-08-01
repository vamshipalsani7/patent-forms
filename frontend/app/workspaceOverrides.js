/*
 * Storage for the user's own decisions about a patent matter, kept separately
 * from the extracted facts the backend owns:
 *
 *   manual   — a value the user typed for a field the documents did not supply
 *   resolved — for a field the documents disagree on, the value the user chose
 *
 * These are the user's calls, not extractions, so they live in their own
 * localStorage record and never masquerade as document evidence. The Patent
 * Workspace overlays them on the backend summary at render time; the backend
 * summary itself is never mutated. Keyed by workspace so one matter's decisions
 * never bleed into another's.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var PREFIX = "patentforms.workspace.overrides.";

  function keyFor(workspaceId) {
    return PREFIX + (workspaceId || "default");
  }

  function load(workspaceId) {
    try {
      var raw = localStorage.getItem(keyFor(workspaceId));
      var parsed = raw ? JSON.parse(raw) : {};
      return {
        manual: parsed.manual || {},
        resolved: parsed.resolved || {},
      };
    } catch (e) {
      return { manual: {}, resolved: {} };
    }
  }

  function save(workspaceId, data) {
    try {
      localStorage.setItem(keyFor(workspaceId), JSON.stringify(data));
    } catch (e) {
      // Quota exceeded — decisions are re-enterable; nothing else to do.
    }
  }

  /** Record a value the user typed for a missing field. */
  function setManual(workspaceId, key, value) {
    var data = load(workspaceId);
    data.manual[key] = value;
    save(workspaceId, data);
    return data;
  }

  /** Remove a manual value (e.g. the user cleared it). */
  function clearManual(workspaceId, key) {
    var data = load(workspaceId);
    delete data.manual[key];
    save(workspaceId, data);
    return data;
  }

  /** Record which value the user chose to resolve a conflict on `key`. */
  function setResolved(workspaceId, key, value) {
    var data = load(workspaceId);
    data.resolved[key] = value;
    save(workspaceId, data);
    return data;
  }

  /**
   * One flat {key: value} map of every decision the user has made — typed-in
   * values and resolved conflicts together — for handing to the form generator
   * so the form pre-fills with what the user reviewed. A resolved conflict wins
   * over a manual value on the same key (it is the more deliberate act), though
   * in practice the two never touch the same key.
   */
  function merged(workspaceId) {
    var data = load(workspaceId);
    var out = {};
    Object.keys(data.manual).forEach(function (k) { out[k] = data.manual[k]; });
    Object.keys(data.resolved).forEach(function (k) { out[k] = data.resolved[k]; });
    return out;
  }

  ns.workspaceOverrides = {
    load: load,
    setManual: setManual,
    clearManual: clearManual,
    setResolved: setResolved,
    merged: merged,
  };
})(window.PatentFormsApp);
