/**
 * suggestionStore.js — localStorage cache for autofill suggestions per formId.
 *
 * Suggestions are ephemeral — they come from the backend on demand and are
 * cached here to survive a page reload. They are never the source of truth for
 * what the user entered; formState.js owns that.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var PREFIX = "patentforms.suggestions.";

  // Cached suggestions are derived from one workspace's documents, so the
  // cache key names that workspace too. Keying by form alone would let a
  // cached suggestion from one patent surface while another is open.
  function cacheKey(formId, workspaceId) {
    return PREFIX + (workspaceId || "default") + "." + formId;
  }

  /**
   * Persist suggestions for a form within a workspace.
   * @param {string} formId
   * @param {object} suggestions   { fieldPath: { value, fact } }
   * @param {string} [workspaceId] defaults to 'default'
   */
  function setSuggestions(formId, suggestions, workspaceId) {
    try {
      localStorage.setItem(cacheKey(formId, workspaceId), JSON.stringify(suggestions));
    } catch (_) {
      // Storage quota exceeded — silently ignore; suggestions can be re-fetched
    }
  }

  /**
   * Retrieve cached suggestions for a form within a workspace.
   * @param {string} formId
   * @param {string} [workspaceId] defaults to 'default'
   * @returns {object}  { fieldPath: { value, fact } } or {} if not cached
   */
  function getSuggestions(formId, workspaceId) {
    try {
      var raw = localStorage.getItem(cacheKey(formId, workspaceId));
      return raw ? JSON.parse(raw) : {};
    } catch (_) {
      return {};
    }
  }

  /**
   * Remove cached suggestions for a form within a workspace.
   * @param {string} formId
   * @param {string} [workspaceId] defaults to 'default'
   */
  function clearSuggestions(formId, workspaceId) {
    localStorage.removeItem(cacheKey(formId, workspaceId));
  }

  ns.suggestionStore = {
    setSuggestions: setSuggestions,
    getSuggestions: getSuggestions,
    clearSuggestions: clearSuggestions,
  };
})(window.PatentFormsApp);
