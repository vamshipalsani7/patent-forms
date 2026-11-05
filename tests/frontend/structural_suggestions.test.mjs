/*
 * Structural suggestions must reach the renderer but not the user.
 *
 * A repeatable group's instance count travels as a suggestion at
 * `path#count`, because flattenSuggestions() copying suggestion values into
 * initialValues is the only channel by which anything reaches renderer state.
 * It is renderer bookkeeping, not an extracted value, so it must still be
 * passed through to the renderer.
 *
 * That it is NOT surfaced to the user is now structural rather than a filter:
 * `#count` is not a rendered field node, so the review layer — which only
 * decorates and counts data-path leaf fields — never gives it a card or counts
 * it. That guarantee is asserted in review_layer.test.mjs ("a suggestion with
 * no field in the form neither decorates nor inflates the count"). Here we keep
 * the pass-through guarantee: the count and each instance value still reach the
 * renderer's initialValues.
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
    ({ ns } = bootstrap("dom.js", "reviewModel.js", "reviewLayer.js", "comparisonView.js", "packageClient.js", "downloadView.js", "formState.js", "mainArea.js"));
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

    test("an entirely-structural suggestion set still mounts a review, not a crash", () => {
      area.showForm(DEFINITION, FORM_ID, { "inventors.inventor#count": structural(1) });
      assert.equal(renderer.initialValues["inventors.inventor#count"], 1);
    });
  });
});
