/*
 * Structural suggestions must reach the renderer but not the user.
 *
 * A repeatable group's instance count travels as a suggestion at
 * `path#count`, because flattenSuggestions() copying suggestion values into
 * initialValues is the only channel by which anything reaches renderer state.
 * It is renderer bookkeeping, not an extracted value, so it must still be
 * passed through to the renderer while being kept out of the provenance
 * banner — otherwise the user is shown a "field" named
 * `inventors.inventor#count` holding the number 2, and the auto-filled count
 * is inflated by one per repeatable group.
 */

import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap, makeContainer, findByClass, installRendererStub } from "./harness.mjs";

const FORM_ID = "form_05";

const DEFINITION = {
  formId: FORM_ID,
  formNumber: "5",
  officialName: "Declaration as to Inventorship",
  sections: [],
};

function fact(value) {
  return {
    key: "inventor.name",
    value,
    document_id: "doc_1",
    source_type: "form2_specification",
    page: 1,
    confidence: 0.85,
    method: "anchor",
    extractor_version: "form2_specification@1",
    extracted_at: "2026-01-01T00:00:00Z",
  };
}

function value(v) {
  return { value: v, fact: fact(v), facts: [fact(v)], structural: false };
}

function structural(v) {
  return { value: v, fact: fact(v), facts: [fact(v)], structural: true };
}

/** The suggestion set a two-inventor specification actually produces. */
function twoInventors() {
  return {
    "inventors.inventor.0.name": value("RAJESH KUMAR"),
    "inventors.inventor.1.name": value("PRIYA SHARMA"),
    "inventors.inventor#count": structural(2),
  };
}

describe("mainArea — structural suggestions", () => {
  let ns, renderer, container, area;

  beforeEach(() => {
    ({ ns } = bootstrap("dom.js", "formState.js", "mainArea.js"));
    renderer = installRendererStub();
    container = makeContainer();
    area = ns.mainArea.mount(container);
  });

  describe("passing through to the renderer", () => {
    test("the instance count reaches initialValues", () => {
      area.showForm(DEFINITION, FORM_ID, twoInventors());
      assert.equal(renderer.initialValues["inventors.inventor#count"], 2);
    });

    test("every indexed instance value reaches initialValues", () => {
      area.showForm(DEFINITION, FORM_ID, twoInventors());
      assert.equal(renderer.initialValues["inventors.inventor.0.name"], "RAJESH KUMAR");
      assert.equal(renderer.initialValues["inventors.inventor.1.name"], "PRIYA SHARMA");
    });

    test("values are passed plainly, not as provenance envelopes", () => {
      area.showForm(DEFINITION, FORM_ID, twoInventors());
      assert.equal(typeof renderer.initialValues["inventors.inventor.0.name"], "string");
      assert.equal(typeof renderer.initialValues["inventors.inventor#count"], "number");
    });
  });

  describe("keeping bookkeeping out of the provenance banner", () => {
    const bannerText = () => {
      const banner = findByClass(container, "provenance-banner");
      return banner ? banner.textContent : "";
    };

    test("the count is not listed as an auto-filled field", () => {
      area.showForm(DEFINITION, FORM_ID, twoInventors());
      assert.ok(!bannerText().includes("#count"), "banner leaked renderer bookkeeping");
    });

    test("the auto-filled tally counts only real values", () => {
      area.showForm(DEFINITION, FORM_ID, twoInventors());
      assert.ok(bannerText().includes("2 fields auto-filled"), bannerText());
    });

    test("real suggested values are still listed", () => {
      area.showForm(DEFINITION, FORM_ID, twoInventors());
      assert.ok(bannerText().includes("RAJESH KUMAR"));
      assert.ok(bannerText().includes("PRIYA SHARMA"));
    });

    test("a suggestion set that is entirely structural shows no banner", () => {
      area.showForm(DEFINITION, FORM_ID, {
        "inventors.inventor#count": structural(1),
      });
      assert.equal(findByClass(container, "provenance-banner"), null);
    });

    test("suggestions without the structural flag are treated as visible", () => {
      // Backwards compatibility: a cached suggestion payload written before
      // `structural` existed has no such key, and must still be listed.
      area.showForm(DEFINITION, FORM_ID, {
        "sec.a": { value: "Acme Ltd", fact: fact("Acme Ltd") },
      });
      assert.ok(bannerText().includes("1 field auto-filled"), bannerText());
    });
  });
});
