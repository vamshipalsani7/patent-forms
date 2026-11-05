/*
 * Review model — the logic that decides how every generated-form field reads
 * to a reviewing patent professional. These tests pin the review philosophy:
 * every value answers "where did this come from?", confidence is language not a
 * percentage, edits are visible with the original recoverable, and the summary
 * counts what the user cares about.
 */
import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap } from "./harness.mjs";

function docSuggestion(value, over = {}) {
  return {
    value: value,
    source_label: over.source_label || "Complete Specification",
    fact: Object.assign({
      source_type: "form2_specification", method: "anchor",
      key: "applicant.name", page: 2, confidence: 0.9,
    }, over.fact || {}),
  };
}

describe("reviewModel", () => {
  let m;
  beforeEach(() => { ({ ns: { reviewModel: m } } = bootstrap("reviewModel.js")); });

  describe("confidence is language, never a percentage", () => {
    test("maps confidence bands to words", () => {
      assert.equal(m.confidenceWord(0.95), "High Confidence");
      assert.equal(m.confidenceWord(0.7), "Medium Confidence");
      assert.equal(m.confidenceWord(0.4), "Low Confidence");
      assert.equal(m.confidenceWord(null), null);
    });
  });

  describe("a value the documents supplied", () => {
    test("reads as From <source> with page and confidence word", () => {
      const s = m.fieldState({
        suggestion: docSuggestion("ABC Technologies Pvt Ltd"),
        currentValue: "ABC Technologies Pvt Ltd",
      });
      assert.equal(s.status, "from_document");
      assert.equal(s.provenanceText, "From Complete Specification");
      assert.equal(s.page, 2);
      assert.equal(s.confidenceWord, "High Confidence");
      assert.equal(s.edited, false);
    });
  });

  describe("a value the user entered themselves", () => {
    test("a manual (user) fact reads as Entered by you", () => {
      const s = m.fieldState({
        suggestion: docSuggestion("Indian", { fact: { source_type: "user", method: "manual", key: "applicant.nationality", confidence: 1.0 } }),
        currentValue: "Indian",
      });
      assert.equal(s.status, "entered_by_you");
      assert.equal(s.provenanceText, "Entered by you");
    });

    test("a filled field with no AI suggestion also reads as Entered by you", () => {
      const s = m.fieldState({ suggestion: null, currentValue: "Something the user typed" });
      assert.equal(s.status, "entered_by_you");
    });
  });

  describe("a value chosen when resolving a conflict", () => {
    test("reads as Selected during review, not a confidence", () => {
      const s = m.fieldState({
        suggestion: docSuggestion("A Solar Cooler", { fact: { key: "invention.title", source_type: "patent_certificate", confidence: 0.85 } }),
        currentValue: "A Solar Cooler",
        resolvedKeys: { "invention.title": true },
      });
      assert.equal(s.status, "selected_during_review");
      assert.equal(s.provenanceText, "Selected during review");
    });
  });

  describe("an edited value", () => {
    test("reads as Edited by you and keeps the original recoverable", () => {
      const s = m.fieldState({
        suggestion: docSuggestion("ABC Technologies Pvt Ltd"),
        currentValue: "ABC Technologies Pvt. Ltd.",
      });
      assert.equal(s.status, "edited_by_you");
      assert.equal(s.provenanceText, "Edited by you");
      assert.equal(s.original, "ABC Technologies Pvt Ltd");
      assert.equal(s.current, "ABC Technologies Pvt. Ltd.");
      assert.equal(s.edited, true);
    });

    test("editing reopens review even if the field was marked reviewed", () => {
      const s = m.fieldState({
        suggestion: docSuggestion("ABC"),
        currentValue: "ABC changed",
        reviewed: true,
      });
      assert.equal(s.reviewed, false, "an edit must un-review the field");
    });
  });

  describe("a missing value", () => {
    test("a required empty field with no suggestion reads as Missing", () => {
      const s = m.fieldState({ suggestion: null, currentValue: "", required: true });
      assert.equal(s.status, "missing");
      assert.equal(s.provenanceText, "Missing");
    });

    test("an optional empty field is not flagged missing", () => {
      const s = m.fieldState({ suggestion: null, currentValue: "", required: false });
      assert.equal(s.status, "empty_optional");
    });

    test("a required field cleared after being autofilled counts against completion", () => {
      const s = m.fieldState({
        suggestion: docSuggestion("Was here"),
        currentValue: "",
        required: true,
      });
      // It still has a suggestion, but it is now empty and required → edited away.
      assert.equal(s.edited, true);
      assert.equal(s.filled, false);
    });
  });

  describe("fields handled at filing are exempt from Missing/completion", () => {
    const DEF = {
      sections: [
        { id: "office_use", title: "FOR OFFICE USE ONLY", fields: [
          { id: "rq_no", kind: "text", required: true },
        ]},
        { id: "requester", title: "Applicant", fields: [
          { id: "name", kind: "text", required: true },
          { id: "address", kind: "textarea", required: true },
        ]},
        { id: "signature", title: "Signature", fields: [
          { id: "statement_date", kind: "date", required: true, autofill: { strategy: "derived" } },
          { id: "signature", kind: "signature", required: true },
        ]},
        { id: "addressee", title: "To", fields: [
          { id: "patent_office", kind: "dropdown", required: true, autofill: { strategy: "derived" } },
        ]},
      ],
    };

    test("exemptPaths flags office-use, signatures, derived and signing dates", () => {
      const ex = m.exemptPaths(DEF);
      assert.ok(ex["office_use.rq_no"], "office-use field");
      assert.ok(ex["signature.statement_date"], "signing date");
      assert.ok(ex["signature.signature"], "signature");
      assert.ok(ex["addressee.patent_office"], "IPO-generated (derived) value");
    });

    test("exemptPaths records WHY each field is exempt (for accurate labels)", () => {
      const ex = m.exemptPaths(DEF);
      assert.equal(ex["office_use.rq_no"], "office");
      assert.equal(ex["signature.signature"], "signature");
      assert.equal(ex["signature.statement_date"], "signing_date");
      assert.equal(ex["addressee.patent_office"], "derived");
    });

    test("substantive fields are NOT exempt", () => {
      const ex = m.exemptPaths(DEF);
      assert.ok(!ex["requester.name"]);
      assert.ok(!ex["requester.address"]);
    });

    test("an empty exempt field is 'exempt', not 'missing'", () => {
      const s = m.fieldState({ suggestion: null, currentValue: "", required: true, exempt: true });
      assert.equal(s.status, "exempt");
    });

    test("completion ignores exempt fields — only substantive gaps block it", () => {
      const states = [
        m.fieldState({ suggestion: docSuggestion("Acme"), currentValue: "Acme" }), // name filled
        m.fieldState({ suggestion: null, currentValue: "", required: true, exempt: true }),  // signature
        m.fieldState({ suggestion: null, currentValue: "", required: true, exempt: true }),  // patent office
      ];
      const sum = m.summarize(states);
      assert.equal(sum.missing, 0, "exempt fields must not count as missing");
      assert.equal(sum.complete, true);
    });

    test("a substantive empty field still blocks completion", () => {
      const states = [
        m.fieldState({ suggestion: null, currentValue: "", required: true, exempt: false }), // real gap
        m.fieldState({ suggestion: null, currentValue: "", required: true, exempt: true }),  // signature
      ];
      const sum = m.summarize(states);
      assert.equal(sum.missing, 1);
      assert.equal(sum.complete, false);
    });
  });

  describe("the live review summary", () => {
    test("counts auto-filled, reviewed, edited and missing independently", () => {
      const states = [
        m.fieldState({ suggestion: docSuggestion("A"), currentValue: "A", reviewed: true }),      // auto + reviewed
        m.fieldState({ suggestion: docSuggestion("B"), currentValue: "B edited" }),                // auto + edited
        m.fieldState({ suggestion: null, currentValue: "", required: true }),                      // missing
        m.fieldState({ suggestion: docSuggestion("C"), currentValue: "C" }),                       // auto
      ];
      const sum = m.summarize(states);
      assert.equal(sum.autoFilled, 3);
      assert.equal(sum.reviewed, 1);
      assert.equal(sum.edited, 1);
      assert.equal(sum.missing, 1);
      assert.equal(sum.complete, false);
    });

    test("is complete only when no required field is missing", () => {
      const complete = m.summarize([
        m.fieldState({ suggestion: docSuggestion("A"), currentValue: "A" }),
        m.fieldState({ suggestion: null, currentValue: "filled", required: true }),
      ]);
      assert.equal(complete.missing, 0);
      assert.equal(complete.complete, true);
    });
  });

  describe("no internal names leak through the model", () => {
    test("provenance text is human, never a sourceType or key", () => {
      const s = m.fieldState({ suggestion: docSuggestion("X"), currentValue: "X" });
      assert.doesNotMatch(s.provenanceText, /form2_specification|applicant\.name|_/);
    });
  });
});
