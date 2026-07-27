/*
 * Draft persistence: serializes/restores editor state per form, keyed by
 * formId. This module owns the "Save Draft" storage mechanism only — no DOM,
 * no renderer knowledge, no PDF/export. It stores the raw values object the
 * renderer's `getValues()` returns, so `setValues()` can play it straight
 * back in for a faithful restore.
 *
 * Persisted to localStorage for this V1 proof (survives reload, does not
 * require a backend). Swapping this for a backend-backed draft store later
 * only touches this file.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var NAMESPACE = "patentforms.draft.";

  function loadDraft(formId) {
    try {
      var raw = localStorage.getItem(NAMESPACE + formId);
      if (!raw) return null;
      return JSON.parse(raw); // { formId, values, userEditedPaths, savedAt }
    } catch (e) {
      console.warn("[formState] failed to read saved draft for", formId, e);
      return null;
    }
  }

  /**
   * @param {string}   formId
   * @param {object}   values           — current renderer values (flat path→value)
   * @param {string[]} userEditedPaths  — paths where user value differs from suggestion
   */
  function saveDraft(formId, values, userEditedPaths) {
    var record = {
      formId: formId,
      values: values,
      userEditedPaths: userEditedPaths || [],
      savedAt: new Date().toISOString(),
    };
    localStorage.setItem(NAMESPACE + formId, JSON.stringify(record));
    return record;
  }

  function clearDraft(formId) {
    localStorage.removeItem(NAMESPACE + formId);
  }

  ns.formState = { loadDraft: loadDraft, saveDraft: saveDraft, clearDraft: clearDraft };
})(window.PatentFormsApp);
