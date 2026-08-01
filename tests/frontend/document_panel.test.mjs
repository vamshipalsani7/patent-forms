/*
 * Documents panel interactions — the sidebar list of uploaded documents.
 *
 * The panel used browser prompt()/confirm() dialogs for rename and remove.
 * These tests drive the real documentWorkspace.js and assert those are gone:
 * rename and remove now happen with inline in-page controls. window.prompt and
 * window.confirm are left unset, so any regression to a browser dialog throws.
 */
import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap, makeContainer, findByText, findByClass } from "./harness.mjs";

function seedDoc(ns, over = {}) {
  return ns.documentStore.add(Object.assign({
    id: "d1", originalFilename: "spec.pdf", displayTitle: "spec.pdf",
    size: 2048, uploadedAt: new Date().toISOString(), workspaceId: "default",
    extractionStatus: "extracted", detectedType: "form2_specification",
    detectedTypeLabel: "Specification", factCount: 4,
  }, over));
}

describe("documents panel", () => {
  let ns, container, changes;
  beforeEach(() => {
    ({ ns } = bootstrap(
      "dom.js", "fileValidation.js", "documentStore.js", "documentUpload.js", "documentWorkspace.js",
    ));
    ns.extractionClient = { uploadForExtraction: () => Promise.resolve(null) };
    container = makeContainer();
    changes = 0;
  });

  const mount = () => ns.documentWorkspace.mount(container, { onChange: () => { changes += 1; } });

  test("shows the document with its detected type and a status badge", () => {
    seedDoc(ns);
    mount();
    const text = container.textContent;
    assert.match(text, /spec\.pdf/);
    assert.match(text, /Specification/);
    assert.match(text, /Information found/);
  });

  test("the status badge carries an actionable hint for unreadable files", () => {
    seedDoc(ns, { extractionStatus: "unrecognised", detectedTypeLabel: null, factCount: 0 });
    mount();
    const badge = findByClass(container, "doc-status");
    assert.match(badge.getAttribute("title"), /PDF or DOCX/i);
  });

  test("removing a document is a two-step inline confirm, not a browser dialog", () => {
    seedDoc(ns);
    mount();
    // First click reveals an inline confirm, does not remove yet.
    findByText(container, "✕").click();
    assert.match(container.textContent, /Remove\?/);
    assert.equal(ns.documentStore.list().length, 1, "must not remove on the first click");

    // Confirming actually removes it.
    findByText(container, "Remove").click();
    assert.equal(ns.documentStore.list().length, 0);
  });

  test("declining the inline confirm keeps the document", () => {
    seedDoc(ns);
    mount();
    findByText(container, "✕").click();
    findByText(container, "Keep").click();
    assert.equal(ns.documentStore.list().length, 1);
    assert.doesNotMatch(container.textContent, /Remove\?/);
  });

  test("renaming happens inline and persists the new title", () => {
    seedDoc(ns);
    mount();
    findByText(container, "✎").click();
    const input = findByClass(container, "doc-rename-input");
    assert.ok(input, "no inline rename input appeared");
    input.value = "Complete Specification (as filed)";
    findByText(container, "✓").click();
    assert.equal(ns.documentStore.get("d1").displayTitle, "Complete Specification (as filed)");
    assert.match(container.textContent, /as filed/);
  });
});
