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

  /**
   * Persist suggestions for a form.
   * @param {string} formId
   * @param {object} suggestions  { fieldPath: { value, fact } }
   */
  function setSuggestions(formId, suggestions) {
    try {
      localStorage.setItem(PREFIX + formId, JSON.stringify(suggestions));
    } catch (_) {
      // Storage quota exceeded — silently ignore; suggestions can be re-fetched
    }
  }

  /**
   * Retrieve cached suggestions.
   * @param {string} formId
   * @returns {object}  { fieldPath: { value, fact } } or {} if not cached
   */
  function getSuggestions(formId) {
    try {
      var raw = localStorage.getItem(PREFIX + formId);
      return raw ? JSON.parse(raw) : {};
    } catch (_) {
      return {};
    }
  }

  /**
   * Remove cached suggestions for a form.
   * @param {string} formId
   */
  function clearSuggestions(formId) {
    localStorage.removeItem(PREFIX + formId);
  }

  ns.suggestionStore = {
    setSuggestions: setSuggestions,
    getSuggestions: getSuggestions,
    clearSuggestions: clearSuggestions,
  };
})(window.PatentFormsApp);
