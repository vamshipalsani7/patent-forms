/*
 * Suggested vs user-entered value separation (mainArea.js) — finding F3.
 *
 * Before this, a saved draft made suggestions indistinguishable from user input
 * forever: re-extraction could never safely refresh them, and "the user decides"
 * became unverifiable. The fix lives entirely in the host application, using
 * only the approved renderer API.
 *
 * Every test here drives the real mainArea.js against a stub that implements
 * nothing beyond mount/getValues/setValues/getGaps/getFindings/unmount. That the
 * suite passes against that surface is the evidence the renderer needed no
 * changes — if mainArea ever reached for a renderer capability that doesn't
 * exist, these tests would fail.
 */

import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap, makeContainer, findByText, findByClass, installRendererStub } from "./harness.mjs";

const FORM_ID = "form_03";

const DEFINITION = {
  formId: FORM_ID,
  formNumber: "3",
  officialName: "Statement and Undertaking Under Section 8",
  sections: [],
};

/** Build a suggestion entry with plausible provenance. */
function suggestion(value, overrides = {}) {
  return {
    value,
    fact: {
      key: "applicant.name",
      value,
      document_id: "doc_1",
      source_type: "form1",
      page: 1,
      confidence: 0.8,
      method: "anchor",
      extractor_version: "form1@1",
      extracted_at: "2026-01-01T00:00:00Z",
      ...overrides,
    },
  };
}

describe("mainArea — suggested vs user-entered separation", () => {
  let ns, renderer, container, area;

  beforeEach(() => {
    ({ ns } = bootstrap("dom.js", "formState.js", "mainArea.js"));
    renderer = installRendererStub();
    container = makeContainer();
    area = ns.mainArea.mount(container);
  });

  const save = () => findByText(container, "Save Draft").click();
  const draft = () => ns.formState.loadDraft(FORM_ID);

  describe("initial values", () => {
    test("a form with no suggestions and no draft starts empty", () => {
      area.showForm(DEFINITION, FORM_ID, {});
      assert.deepEqual(renderer.initialValues, {});
    });

    test("suggestions pre-fill the form", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      assert.deepEqual(renderer.initialValues, { "sec.a": "Acme Ltd" });
    });

    test("suggestions are passed as plain values, not provenance envelopes", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      assert.equal(typeof renderer.initialValues["sec.a"], "string");
    });

    test("array-valued suggestions survive intact", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.list": suggestion(["Acme Ltd"]) });
      assert.deepEqual(renderer.initialValues["sec.list"], ["Acme Ltd"]);
    });
  });

  describe("tracking which paths the user edited", () => {
    test("an untouched form records no user edits", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      save();
      assert.deepEqual(draft().userEditedPaths, []);
    });

    test("editing a suggested field marks that path as user-edited", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.a": "Corrected Ltd" });
      save();

      assert.deepEqual(draft().userEditedPaths, ["sec.a"]);
      assert.equal(draft().values["sec.a"], "Corrected Ltd");
    });

    test("only the edited path is marked, not its neighbours", () => {
      area.showForm(DEFINITION, FORM_ID, {
        "sec.a": suggestion("Acme Ltd"),
        "sec.b": suggestion("202211012345"),
      });
      renderer.userEdits({ "sec.a": "Corrected Ltd" });
      save();

      assert.deepEqual(draft().userEditedPaths, ["sec.a"]);
    });

    test("typing a value back to match the suggestion un-marks it", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.a": "Corrected Ltd" });
      renderer.userEdits({ "sec.a": "Acme Ltd" });
      save();

      assert.deepEqual(draft().userEditedPaths, []);
    });

    test("an unchanged array value is not mistaken for an edit", () => {
      /*
       * Regression guard. The renderer clones its value snapshot on every
       * onChange, so a strict !== comparison reports every array-valued field
       * as user-edited on the very first render — which would permanently
       * freeze repeatable and table fields against re-extraction.
       */
      area.showForm(DEFINITION, FORM_ID, { "sec.list": suggestion(["Acme Ltd"]) });
      renderer.userEdits({ "sec.list": ["Acme Ltd"] });
      save();

      assert.deepEqual(draft().userEditedPaths, []);
    });

    test("a genuinely changed array value is marked", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.list": suggestion(["Acme Ltd"]) });
      renderer.userEdits({ "sec.list": ["Acme Ltd", "Beta Ltd"] });
      save();

      assert.deepEqual(draft().userEditedPaths, ["sec.list"]);
    });

    test("editing a field that was never suggested is not tracked as an override", () => {
      // Nothing to diverge from, so there is no suggestion to protect it against.
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.untouched_by_extraction": "typed by hand" });
      save();

      assert.deepEqual(draft().userEditedPaths, []);
      assert.equal(draft().values["sec.untouched_by_extraction"], "typed by hand");
    });
  });

  describe("re-extraction refreshes suggestions without overwriting user edits", () => {
    beforeEach(() => {
      // Session 1: user corrects one field, leaves another as suggested.
      area.showForm(DEFINITION, FORM_ID, {
        "sec.edited": suggestion("Original Extract"),
        "sec.untouched": suggestion("Original Number"),
      });
      renderer.userEdits({ "sec.edited": "User Correction" });
      save();
    });

    test("the user's edit survives a refresh", () => {
      area.showForm(DEFINITION, FORM_ID, {
        "sec.edited": suggestion("Newly Extracted"),
        "sec.untouched": suggestion("New Number"),
      });
      assert.equal(renderer.initialValues["sec.edited"], "User Correction");
    });

    test("an untouched field picks up the newer suggestion", () => {
      area.showForm(DEFINITION, FORM_ID, {
        "sec.edited": suggestion("Newly Extracted"),
        "sec.untouched": suggestion("New Number"),
      });
      assert.equal(renderer.initialValues["sec.untouched"], "New Number");
    });

    test("the user-edited set persists across the reload", () => {
      area.showForm(DEFINITION, FORM_ID, {
        "sec.edited": suggestion("Newly Extracted"),
        "sec.untouched": suggestion("New Number"),
      });
      save();
      assert.deepEqual(draft().userEditedPaths, ["sec.edited"]);
    });

    test("a field that stops being suggested keeps the user's value", () => {
      area.showForm(DEFINITION, FORM_ID, {});
      assert.equal(renderer.initialValues["sec.edited"], "User Correction");
    });

    test("re-editing the same field in a later session still holds", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.edited": suggestion("Newly Extracted") });
      renderer.userEdits({ "sec.edited": "Second Correction" });
      save();

      area.showForm(DEFINITION, FORM_ID, { "sec.edited": suggestion("Third Extract") });
      assert.equal(renderer.initialValues["sec.edited"], "Second Correction");
    });
  });

  describe("the user always has the final edit", () => {
    test("no suggested value is ever locked", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.a": "" });
      save();

      assert.equal(draft().values["sec.a"], "", "the user must be able to clear a suggestion");
      assert.deepEqual(draft().userEditedPaths, ["sec.a"]);
    });

    test("a deliberately cleared field is not silently re-filled on refresh", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.a": "" });
      save();

      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd Again") });
      assert.equal(renderer.initialValues["sec.a"], "");
    });
  });

  describe("Start Fresh", () => {
    test("discards the draft and returns to the suggested values", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.a": "User Correction" });
      save();

      findByText(container, "Start Fresh").click();

      assert.equal(ns.formState.loadDraft(FORM_ID), null, "draft was not cleared");
      assert.deepEqual(renderer.setValuesCalls.at(-1), { "sec.a": "Acme Ltd" });
    });

    test("clears the user-edited set", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.a": "User Correction" });
      save();

      findByText(container, "Start Fresh").click();
      save();

      assert.deepEqual(draft().userEditedPaths, []);
    });

    test("does nothing when the confirmation is declined", () => {
      globalThis.window.confirm = () => false;

      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.a": "User Correction" });
      save();

      findByText(container, "Start Fresh").click();

      assert.ok(ns.formState.loadDraft(FORM_ID), "draft was cleared despite declining");
    });
  });

  describe("provenance is visible to the user", () => {
    test("a banner reports how many fields were auto-filled", () => {
      area.showForm(DEFINITION, FORM_ID, {
        "sec.a": suggestion("Acme Ltd"),
        "sec.b": suggestion("202211012345"),
      });
      assert.equal(findByClass(container, "provenance-count").textContent, "2 fields auto-filled");
    });

    test("the count is singular for one field", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      assert.equal(findByClass(container, "provenance-count").textContent, "1 field auto-filled");
    });

    test("no banner is shown when nothing was auto-filled", () => {
      area.showForm(DEFINITION, FORM_ID, {});
      assert.equal(findByClass(container, "provenance-banner"), null);
    });

    test("each suggestion's source document, page, method and confidence are shown", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });

      const source = findByClass(container, "provenance-src").textContent;
      assert.match(source, /form1/, "source document type is missing");
      assert.match(source, /p\.1/, "page number is missing");
      assert.match(source, /anchor/, "extraction method is missing");
      assert.match(source, /80% conf/, "confidence is missing");
    });

    test("the sources panel can be expanded and collapsed", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });

      const detail = findByClass(container, "provenance-detail");
      const toggle = findByClass(container, "provenance-toggle");

      assert.equal(detail.style.display, "none", "sources should start collapsed");
      toggle.click();
      assert.equal(detail.style.display, "block");
      assert.equal(toggle.textContent, "Hide sources");
      toggle.click();
      assert.equal(detail.style.display, "none");
    });
  });

  describe("renderer contract", () => {
    test("mainArea uses only the approved renderer API", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.a": "x" });
      save();
      findByText(container, "Start Fresh").click();

      // The stub exposes nothing beyond the approved surface, so reaching the
      // end of this flow without a TypeError is the assertion.
      assert.equal(renderer.mountCount, 1);
    });

    test("switching forms unmounts the previous renderer instance", () => {
      area.showForm(DEFINITION, FORM_ID, {});
      area.showWelcome();
      assert.equal(renderer.unmounted, true);
    });

    test("the definition is passed through untouched", () => {
      area.showForm(DEFINITION, FORM_ID, {});
      assert.equal(renderer.definition, DEFINITION);
    });
  });

  describe("draft status feedback", () => {
    test("reports the number of auto-filled fields on a fresh form", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      assert.match(findByClass(container, "draft-status").textContent, /auto-filled/);
    });

    test("reports unsaved changes after an edit", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.a": "x" });

      const status = findByClass(container, "draft-status");
      assert.equal(status.textContent, "Unsaved changes");
      assert.ok(status.classList.contains("dirty"));
    });

    test("clears the dirty marker once saved", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      renderer.userEdits({ "sec.a": "x" });
      save();

      const status = findByClass(container, "draft-status");
      assert.ok(!status.classList.contains("dirty"));
      assert.match(status.textContent, /Draft saved/);
    });

    test("reports a restored draft on reload", () => {
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });
      save();
      area.showForm(DEFINITION, FORM_ID, { "sec.a": suggestion("Acme Ltd") });

      assert.match(findByClass(container, "draft-status").textContent, /Restored draft/);
    });
  });
});
