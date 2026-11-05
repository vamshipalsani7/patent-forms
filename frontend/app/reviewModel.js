/*
 * Review model — the pure logic behind the AI Form Review experience.
 *
 * Given what the AI filled in (a suggestion), what the field currently holds,
 * and the user's own decisions, it decides how a field should read to a patent
 * professional reviewing the form: where the value came from, whether it was
 * entered or chosen by the user, whether it has since been edited, or whether
 * it is missing. It also tallies the live review summary.
 *
 * No DOM, no network, no knowledge of the renderer. Everything the review layer
 * shows on screen is decided here, which is what makes the presentation testable
 * without a browser. The UX rule that no internal name (vocabulary key,
 * sourceType, mapper path, confidence percentage) is ever shown is enforced by
 * this module returning only human-facing language.
 */
window.PatentFormsApp = window.PatentFormsApp || {};
(function (ns) {
  "use strict";

  // Confidence as language. Same thresholds the Patent Workspace uses, so a
  // value reads the same before and after the form is generated. The exact
  // figure is never shown — only the word.
  function confidenceWord(conf) {
    if (conf == null) return null;
    if (conf >= 0.8) return "High Confidence";
    if (conf >= 0.6) return "Medium Confidence";
    return "Low Confidence";
  }

  // Mirrors the renderer's own notion of "filled" so the review agrees with the
  // form: an array counts if any entry (or any cell of a row object) has text.
  function isFilled(v) {
    if (v == null) return false;
    if (Array.isArray(v)) {
      return v.some(function (x) {
        if (x && typeof x === "object") {
          return Object.keys(x).some(function (k) { return String(x[k] == null ? "" : x[k]).trim() !== ""; });
        }
        return String(x == null ? "" : x).trim() !== "";
      });
    }
    if (typeof v === "boolean") return v;
    return String(v).trim() !== "";
  }

  function valuesEqual(a, b) {
    if (a === b) return true;
    if (typeof a !== "object" || typeof b !== "object" || a == null || b == null) return false;
    return JSON.stringify(a) === JSON.stringify(b);
  }

  function displayValue(v) {
    if (v == null) return "";
    if (Array.isArray(v)) {
      return v.map(function (x) {
        if (x && typeof x === "object") {
          return Object.keys(x).map(function (k) { return x[k]; }).filter(Boolean).join(", ");
        }
        return x;
      }).filter(function (s) { return String(s || "").trim() !== ""; }).join("; ");
    }
    return String(v);
  }

  /**
   * Which field paths are exempt from the "must complete before generating"
   * check. These are fields a patent professional does NOT fill to make the
   * matter ready — they are handled at, or by, filing:
   *
   *   - signatures (signed at filing)
   *   - IPO-generated / computed values (autofill strategy "derived": the
   *     receiving office, checkbox declarations, category classifications)
   *   - fields inside a "for office use only" section
   *   - the signing date next to a signature block ("Dated this __ day of __")
   *
   * Counting these as "missing" makes the completion state unreachable and
   * scares the user with a form that looks far from ready. Excluding them makes
   * "Missing" mean what it should: substantive information still to provide.
   *
   * Keyed by the definition path (no repeat indices); the review layer strips
   * ".0"/".1" instance indices before looking a field up here.
   *
   * @param {object} definition  parsed form definition JSON
   * @returns {object} { path: true }
   */
  function exemptPaths(definition) {
    var out = {};
    (definition && definition.sections ? definition.sections : []).forEach(function (section) {
      var officeSection = /office\s*use|for\s*office/i.test(section.title || "") ||
        String(section.id || "").toLowerCase().indexOf("office") === 0;
      walkExempt(section.fields || [], section.id, officeSection, out);
    });
    return out;
  }

  // Value is the REASON a field is exempt, so the comparison screen can label it
  // accurately (a signature is not "Patent Office Use"). Any non-empty reason is
  // truthy, so callers that only need the boolean are unaffected.
  function walkExempt(fields, base, officeSection, out) {
    fields.forEach(function (f) {
      var path = base + "." + f.id;
      var af = f.autofill || {};
      var reason = null;
      if (officeSection) reason = "office";
      else if (f.kind === "signature" || f.kind === "signatureBlock") reason = "signature";
      else if (f.kind === "date" && /signature|statement_date/i.test(path)) reason = "signing_date";
      else if (af.strategy === "derived") reason = "derived";
      if (reason) out[path] = reason;
      if (f.fields) walkExempt(f.fields, path, officeSection, out);
    });
  }

  /**
   * Classify one field for review.
   *
   * @param {object} d
   * @param {object|null} d.suggestion  { value, fact:{source_type, method, key, page, confidence}, source_label }
   * @param {*}      d.currentValue      the renderer's current value at this path
   * @param {object} [d.resolvedKeys]    { vocabKey: true } — conflicts the user resolved
   * @param {boolean}[d.required]        does the form require this field
   * @param {boolean}[d.reviewed]        has the user marked it reviewed
   * @param {boolean}[d.exempt]          is this field handled at filing (see exemptPaths)
   * @returns {object} presentation state (all human-facing)
   */
  function fieldState(d) {
    var suggestion = d.suggestion || null;
    var current = d.currentValue;
    var resolved = d.resolvedKeys || {};
    var required = !!d.required;
    var reviewed = !!d.reviewed;
    var exempt = !!d.exempt;

    var filled = isFilled(current);
    var fact = suggestion && suggestion.fact ? suggestion.fact : null;
    var key = fact ? fact.key : null;
    var edited = false;
    var status;

    if (suggestion) {
      edited = !valuesEqual(current, suggestion.value);
      if (edited) {
        status = "edited_by_you";
      } else if (fact && (fact.source_type === "user" || fact.method === "manual")) {
        status = "entered_by_you";
      } else if (key && resolved[key]) {
        status = "selected_during_review";
      } else {
        status = "from_document";
      }
    } else if (!filled) {
      // A field handled at filing is neither "missing" nor a gap to nag about.
      status = exempt ? "exempt" : (required ? "missing" : "empty_optional");
    } else {
      // Filled with no AI suggestion behind it — the user's own value.
      status = "entered_by_you";
    }

    return {
      hasSuggestion: !!suggestion,
      status: status,
      filled: filled,
      required: required,
      reviewed: reviewed && !edited,   // an edit reopens review
      edited: edited,
      current: displayValue(current),
      original: suggestion ? displayValue(suggestion.value) : null,
      sourceLabel: suggestion ? (suggestion.source_label || null) : null,
      page: fact ? fact.page : null,
      confidenceWord: fact ? confidenceWord(fact.confidence) : null,
      provenanceText: provenanceText(status, suggestion),
    };
  }

  function provenanceText(status, suggestion) {
    switch (status) {
      case "from_document":
        return "From " + ((suggestion && suggestion.source_label) || "your documents");
      case "entered_by_you": return "Entered by you";
      case "selected_during_review": return "Selected during review";
      case "edited_by_you": return "Edited by you";
      case "missing": return "Missing";
      default: return "";
    }
  }

  /**
   * Roll a set of field states up into the live review summary.
   * @param {object[]} states  fieldState() results for every reviewed field
   */
  function summarize(states) {
    var autoFilled = 0, reviewed = 0, edited = 0, missing = 0, tracked = 0;
    states.forEach(function (s) {
      if (s.hasSuggestion) autoFilled += 1;
      if (s.reviewed) reviewed += 1;
      if (s.edited) edited += 1;
      if (s.status === "missing") missing += 1;
      // A field the review actually speaks to — filled by the AI or the user, or
      // still needed. Distinguishes "a real form being worked on" from a form
      // with nothing substantive to complete (so we don't celebrate emptiness).
      if (s.status === "from_document" || s.status === "entered_by_you" ||
          s.status === "selected_during_review" || s.status === "edited_by_you" ||
          s.status === "missing") {
        tracked += 1;
      }
    });
    return {
      autoFilled: autoFilled,
      reviewed: reviewed,
      edited: edited,
      missing: missing,
      tracked: tracked,
      // "Every required field is complete" — the gate for the completion state.
      complete: missing === 0,
    };
  }

  ns.reviewModel = {
    confidenceWord: confidenceWord,
    isFilled: isFilled,
    valuesEqual: valuesEqual,
    displayValue: displayValue,
    exemptPaths: exemptPaths,
    fieldState: fieldState,
    summarize: summarize,
  };
})(window.PatentFormsApp);
