/*
 * Draft persistence (formState.js) and the suggestion cache (suggestionStore.js).
 *
 * The draft record is what carries the suggested-vs-user-entered distinction
 * across sessions, so its shape is a contract, not an implementation detail.
 */

import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap } from "./harness.mjs";

describe("formState — draft persistence", () => {
  let ns, localStorage;

  beforeEach(() => {
    ({ ns, localStorage } = bootstrap("formState.js"));
  });

  test("returns null when no draft has been saved", () => {
    assert.equal(ns.formState.loadDraft("form_03"), null);
  });

  test("round-trips values", () => {
    ns.formState.saveDraft("form_03", { "sec.a": "hello" }, []);
    assert.deepEqual(ns.formState.loadDraft("form_03").values, { "sec.a": "hello" });
  });

  test("persists the set of user-edited paths", () => {
    ns.formState.saveDraft("form_03", { "sec.a": "x" }, ["sec.a"]);
    assert.deepEqual(ns.formState.loadDraft("form_03").userEditedPaths, ["sec.a"]);
  });

  test("defaults userEditedPaths to empty when omitted", () => {
    ns.formState.saveDraft("form_03", { "sec.a": "x" });
    assert.deepEqual(ns.formState.loadDraft("form_03").userEditedPaths, []);
  });

  test("records the form id and a save timestamp", () => {
    const record = ns.formState.saveDraft("form_03", {}, []);
    assert.equal(record.formId, "form_03");
    assert.ok(record.savedAt, "savedAt is missing");
    assert.ok(!Number.isNaN(Date.parse(record.savedAt)), "savedAt is not a valid date");
  });

  test("returns the saved record so callers need not re-read it", () => {
    const record = ns.formState.saveDraft("form_03", { "sec.a": "x" }, ["sec.a"]);
    assert.deepEqual(record.values, { "sec.a": "x" });
    assert.deepEqual(record.userEditedPaths, ["sec.a"]);
  });

  test("saving again overwrites the previous draft", () => {
    ns.formState.saveDraft("form_03", { "sec.a": "first" }, []);
    ns.formState.saveDraft("form_03", { "sec.a": "second" }, ["sec.a"]);

    const draft = ns.formState.loadDraft("form_03");
    assert.equal(draft.values["sec.a"], "second");
    assert.deepEqual(draft.userEditedPaths, ["sec.a"]);
  });

  test("drafts are scoped per form", () => {
    ns.formState.saveDraft("form_03", { "sec.a": "three" }, []);
    ns.formState.saveDraft("form_13", { "sec.a": "thirteen" }, []);

    assert.equal(ns.formState.loadDraft("form_03").values["sec.a"], "three");
    assert.equal(ns.formState.loadDraft("form_13").values["sec.a"], "thirteen");
  });

  test("clearDraft removes only the targeted form", () => {
    ns.formState.saveDraft("form_03", { "sec.a": "x" }, []);
    ns.formState.saveDraft("form_13", { "sec.a": "y" }, []);

    ns.formState.clearDraft("form_03");

    assert.equal(ns.formState.loadDraft("form_03"), null);
    assert.ok(ns.formState.loadDraft("form_13"), "clearing one form wiped another");
  });

  test("preserves array values such as repeatable rows and table rows", () => {
    const values = {
      "sec.applicants": ["Acme Ltd", "Beta Ltd"],
      "sec.table": [{ country: "Germany", number: "DE123" }],
    };
    ns.formState.saveDraft("form_03", values, []);
    assert.deepEqual(ns.formState.loadDraft("form_03").values, values);
  });

  test("survives corrupt storage instead of throwing", () => {
    localStorage.setItem("patentforms.draft.form_03", "{ not json");
    assert.equal(ns.formState.loadDraft("form_03"), null);
  });
});

describe("suggestionStore — cached suggestions", () => {
  let ns, localStorage;

  beforeEach(() => {
    ({ ns, localStorage } = bootstrap("suggestionStore.js"));
  });

  const SUGGESTIONS = {
    "sec.a": { value: "Acme Ltd", fact: { document_id: "doc_1", page: 1, confidence: 0.8 } },
  };

  test("returns an empty object when nothing is cached", () => {
    assert.deepEqual(ns.suggestionStore.getSuggestions("form_03"), {});
  });

  test("round-trips suggestions with their provenance intact", () => {
    ns.suggestionStore.setSuggestions("form_03", SUGGESTIONS);
    const loaded = ns.suggestionStore.getSuggestions("form_03");

    assert.equal(loaded["sec.a"].value, "Acme Ltd");
    assert.equal(loaded["sec.a"].fact.document_id, "doc_1");
    assert.equal(loaded["sec.a"].fact.page, 1);
  });

  test("suggestions are scoped per form", () => {
    ns.suggestionStore.setSuggestions("form_03", SUGGESTIONS);
    assert.deepEqual(ns.suggestionStore.getSuggestions("form_13"), {});
  });

  test("clearSuggestions removes the cache", () => {
    ns.suggestionStore.setSuggestions("form_03", SUGGESTIONS);
    ns.suggestionStore.clearSuggestions("form_03");
    assert.deepEqual(ns.suggestionStore.getSuggestions("form_03"), {});
  });

  test("refreshing replaces the previous cache wholesale", () => {
    ns.suggestionStore.setSuggestions("form_03", SUGGESTIONS);
    ns.suggestionStore.setSuggestions("form_03", { "sec.b": { value: "New", fact: {} } });

    const loaded = ns.suggestionStore.getSuggestions("form_03");
    assert.ok(!("sec.a" in loaded), "stale suggestion survived a refresh");
    assert.equal(loaded["sec.b"].value, "New");
  });

  test("survives corrupt storage instead of throwing", () => {
    localStorage.setItem("patentforms.suggestions.form_03", "{ not json");
    assert.deepEqual(ns.suggestionStore.getSuggestions("form_03"), {});
  });

  test("does not throw when storage rejects a write", () => {
    // Simulates a quota error; suggestions are re-fetchable, so this is survivable.
    localStorage.setItem = () => { throw new Error("QuotaExceededError"); };
    assert.doesNotThrow(() => ns.suggestionStore.setSuggestions("form_03", SUGGESTIONS));
  });
});
