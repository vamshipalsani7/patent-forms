/*
 * Dynamic form-definition loader. The single place in the application that
 * knows where .definition.json files live on disk.
 *
 * loadDefinition(formId) -> Promise<definition>
 *
 * On a missing/failed definition, the promise rejects with a descriptive
 * Error rather than the caller inventing placeholder content — mainArea.js
 * turns that rejection into an honest "not yet available" state.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  var cache = {}; // formId -> Promise<definition> (successful loads only)

  function loadDefinition(formId) {
    if (cache[formId]) return cache[formId];

    var path = "/docs/specifications/definitions/" + formId + ".definition.json";
    var promise = fetch(path)
      .then(function (res) {
        if (!res.ok) {
          throw new Error("No definition available for \"" + formId + "\" (HTTP " + res.status + " at " + path + ").");
        }
        return res.json();
      })
      .catch(function (err) {
        delete cache[formId]; // don't cache failures — allow retry once a definition is authored
        throw err;
      });

    cache[formId] = promise;
    return promise;
  }

  ns.formLoader = { loadDefinition: loadDefinition };
})(window.PatentFormsApp);
