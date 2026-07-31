/*
 * Workspace isolation (documentStore.js, documentUpload.js).
 *
 * Merging a Form 1 for Patent A with a certificate for Patent B produces a
 * confidently wrong profile — the worst failure mode, because it looks fine.
 * `workspaceId` is what prevents that, so these tests cover both that documents
 * carry it and that querying by workspace never leaks across matters.
 */

import { test, describe, beforeEach } from "node:test";
import assert from "node:assert/strict";

import { bootstrap, loadAppScript } from "./harness.mjs";

const PATENT_A = "ws_patent_a";
const PATENT_B = "ws_patent_b";

function record(id, workspaceId, name = "doc.pdf") {
  return {
    id,
    originalFilename: name,
    displayTitle: name,
    size: 1024,
    uploadedAt: new Date().toISOString(),
    workspaceId,
  };
}

describe("documentStore — workspace scoping", () => {
  let ns, localStorage;

  beforeEach(() => {
    ({ ns, localStorage } = bootstrap("documentStore.js"));
  });

  test("starts empty", () => {
    assert.deepEqual(ns.documentStore.list(), []);
  });

  test("persists the workspaceId on a document", () => {
    ns.documentStore.add(record("d1", PATENT_A));
    assert.equal(ns.documentStore.get("d1").workspaceId, PATENT_A);
  });

  test("listByWorkspace returns only that workspace's documents", () => {
    ns.documentStore.add(record("a1", PATENT_A));
    ns.documentStore.add(record("a2", PATENT_A));
    ns.documentStore.add(record("b1", PATENT_B));

    assert.deepEqual(ns.documentStore.listByWorkspace(PATENT_A).map((d) => d.id), ["a1", "a2"]);
    assert.deepEqual(ns.documentStore.listByWorkspace(PATENT_B).map((d) => d.id), ["b1"]);
  });

  test("documents from different patents never appear in the same workspace view", () => {
    ns.documentStore.add(record("a1", PATENT_A, "patent-a-form1.pdf"));
    ns.documentStore.add(record("b1", PATENT_B, "patent-b-certificate.pdf"));

    for (const doc of ns.documentStore.listByWorkspace(PATENT_A)) {
      assert.notEqual(doc.workspaceId, PATENT_B, "cross-workspace contamination");
    }
  });

  test("an unknown workspace yields nothing rather than everything", () => {
    ns.documentStore.add(record("a1", PATENT_A));
    assert.deepEqual(ns.documentStore.listByWorkspace("ws_never_created"), []);
  });

  test("documents without a workspaceId are not returned for any workspace", () => {
    ns.documentStore.add({ id: "legacy", originalFilename: "old.pdf", displayTitle: "old.pdf" });
    assert.deepEqual(ns.documentStore.listByWorkspace(PATENT_A), []);
    assert.equal(ns.documentStore.list().length, 1, "it should still be listed globally");
  });

  test("removing from one workspace leaves another untouched", () => {
    ns.documentStore.add(record("a1", PATENT_A));
    ns.documentStore.add(record("b1", PATENT_B));

    ns.documentStore.remove("a1");

    assert.deepEqual(ns.documentStore.listByWorkspace(PATENT_A), []);
    assert.equal(ns.documentStore.listByWorkspace(PATENT_B).length, 1);
  });

  test("renaming changes the display title and preserves the workspace", () => {
    ns.documentStore.add(record("a1", PATENT_A, "raw-scan.pdf"));
    ns.documentStore.rename("a1", "Form 1 as filed");

    const doc = ns.documentStore.get("a1");
    assert.equal(doc.displayTitle, "Form 1 as filed");
    assert.equal(doc.originalFilename, "raw-scan.pdf", "the original filename must not change");
    assert.equal(doc.workspaceId, PATENT_A);
  });

  test("renaming an unknown id returns null rather than throwing", () => {
    assert.equal(ns.documentStore.rename("nope", "x"), null);
  });

  test("get returns null for an unknown id", () => {
    assert.equal(ns.documentStore.get("nope"), null);
  });

  test("survives corrupt storage instead of throwing", () => {
    localStorage.setItem("patentforms.documents", "{ not json");
    assert.deepEqual(ns.documentStore.list(), []);
  });

  test("ignores a non-array payload in storage", () => {
    localStorage.setItem("patentforms.documents", '{"unexpected":"shape"}');
    assert.deepEqual(ns.documentStore.list(), []);
  });
});

describe("documentUpload — ingestion stamps the workspace", () => {
  let ns, uploadCalls;

  beforeEach(() => {
    const env = bootstrap("pdfValidation.js", "documentStore.js");
    ns = env.ns;

    // Stub the extraction client: ingestion fires it, but the network round
    // trip is not what this test is about.
    uploadCalls = [];
    ns.extractionClient = {
      uploadForExtraction: (documentId, file) => {
        uploadCalls.push({ documentId, file });
        return Promise.resolve({ document_id: documentId, source_type: "form1", facts: [] });
      },
    };
    loadAppScript("documentUpload.js");
  });

  const pdf = (name = "form1.pdf") => ({ name, size: 2048, type: "application/pdf" });

  test("accepts a PDF and stores metadata", () => {
    const result = ns.documentUpload.ingestFiles([pdf()]);

    assert.equal(result.accepted.length, 1);
    assert.equal(result.rejected.length, 0);
    assert.equal(ns.documentStore.list().length, 1);
  });

  test("stamps every ingested document with a workspaceId", () => {
    ns.documentUpload.ingestFiles([pdf("a.pdf"), pdf("b.pdf")]);

    for (const doc of ns.documentStore.list()) {
      assert.ok(doc.workspaceId, `document ${doc.id} has no workspaceId`);
    }
  });

  test("ingested documents are retrievable by their workspace", () => {
    const { accepted } = ns.documentUpload.ingestFiles([pdf()]);
    const workspaceId = accepted[0].workspaceId;

    assert.deepEqual(
      ns.documentStore.listByWorkspace(workspaceId).map((d) => d.id),
      [accepted[0].id],
    );
  });

  test("rejects a non-PDF and does not store it", () => {
    const result = ns.documentUpload.ingestFiles([{ name: "notes.txt", size: 10, type: "text/plain" }]);

    assert.equal(result.accepted.length, 0);
    assert.equal(result.rejected.length, 1);
    assert.match(result.rejected[0].reason, /PDF/i);
    assert.deepEqual(ns.documentStore.list(), []);
  });

  test("accepts a .pdf whose MIME type the OS did not report", () => {
    const result = ns.documentUpload.ingestFiles([{ name: "scan.pdf", size: 10, type: "" }]);
    assert.equal(result.accepted.length, 1);
  });

  test("assigns unique ids across a multi-file ingest", () => {
    const { accepted } = ns.documentUpload.ingestFiles([pdf("a.pdf"), pdf("b.pdf"), pdf("c.pdf")]);
    assert.equal(new Set(accepted.map((d) => d.id)).size, 3);
  });

  test("hands each accepted file to the extraction client", () => {
    const { accepted } = ns.documentUpload.ingestFiles([pdf()]);

    assert.equal(uploadCalls.length, 1);
    assert.equal(uploadCalls[0].documentId, accepted[0].id);
  });

  test("does not send rejected files for extraction", () => {
    ns.documentUpload.ingestFiles([{ name: "notes.txt", size: 10, type: "text/plain" }]);
    assert.equal(uploadCalls.length, 0);
  });

  test("records metadata only — never file contents", () => {
    ns.documentUpload.ingestFiles([pdf()]);
    const stored = JSON.parse(globalThis.localStorage.getItem("patentforms.documents"));

    assert.deepEqual(
      Object.keys(stored[0]).sort(),
      ["displayTitle", "id", "originalFilename", "size", "uploadedAt", "workspaceId"],
    );
  });

  test("handles an empty file list", () => {
    const result = ns.documentUpload.ingestFiles([]);
    assert.deepEqual(result, { accepted: [], rejected: [] });
  });
});

describe("extractionClient — the workspace travels with every request", () => {
  let ns, requests;

  beforeEach(() => {
    ({ ns } = bootstrap("extractionClient.js"));

    requests = [];
    globalThis.fetch = (url, options) => {
      requests.push({ url, options });
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ form_id: "form_03", workspace_id: "ws", suggestions: {} }),
      });
    };
    // FormData is not a Node global in every version; a minimal stand-in is
    // enough to observe which fields the client appends.
    globalThis.FormData = class {
      constructor() { this.entries = []; }
      append(k, v) { this.entries.push([k, v]); }
      get(k) { const e = this.entries.find((x) => x[0] === k); return e ? e[1] : null; }
    };
  });

  test("upload sends the workspace alongside the document", async () => {
    await ns.extractionClient.uploadForExtraction("doc_1", { name: "a.pdf" }, "patent_a");

    const body = requests[0].options.body;
    assert.equal(body.get("workspace_id"), "patent_a");
    assert.equal(body.get("document_id"), "doc_1");
  });

  test("suggestions are requested for a named workspace", async () => {
    await ns.extractionClient.getSuggestions("form_03", "patent_a");
    assert.match(requests[0].url, /workspace_id=patent_a/);
  });

  test("the workspace id is url-encoded", async () => {
    await ns.extractionClient.getSuggestions("form_03", "a b&c");
    assert.match(requests[0].url, /workspace_id=a%20b%26c/);
    assert.ok(!requests[0].url.includes("&c="), "an unencoded id could forge a query parameter");
  });

  test("a failed request still reports which workspace it was for", async () => {
    globalThis.fetch = () => Promise.reject(new Error("backend offline"));
    const result = await ns.extractionClient.getSuggestions("form_03", "patent_a");

    assert.equal(result.workspace_id, "patent_a");
    assert.deepEqual(result.suggestions, {}, "an offline backend must not imply 'no scoping'");
  });
});

describe("suggestionStore — cache is scoped per workspace", () => {
  let ns;

  beforeEach(() => {
    ({ ns } = bootstrap("suggestionStore.js"));
  });

  const forWorkspace = (name) => ({ "sec.a": { value: name, fact: { document_id: "d" } } });

  test("one workspace's cached suggestions are invisible to another", () => {
    ns.suggestionStore.setSuggestions("form_03", forWorkspace("Company A"), "patent_a");
    assert.deepEqual(ns.suggestionStore.getSuggestions("form_03", "patent_b"), {});
  });

  test("each workspace keeps its own cache for the same form", () => {
    ns.suggestionStore.setSuggestions("form_03", forWorkspace("Company A"), "patent_a");
    ns.suggestionStore.setSuggestions("form_03", forWorkspace("Company B"), "patent_b");

    assert.equal(ns.suggestionStore.getSuggestions("form_03", "patent_a")["sec.a"].value, "Company A");
    assert.equal(ns.suggestionStore.getSuggestions("form_03", "patent_b")["sec.a"].value, "Company B");
  });

  test("clearing one workspace's cache leaves the other intact", () => {
    ns.suggestionStore.setSuggestions("form_03", forWorkspace("Company A"), "patent_a");
    ns.suggestionStore.setSuggestions("form_03", forWorkspace("Company B"), "patent_b");

    ns.suggestionStore.clearSuggestions("form_03", "patent_a");

    assert.deepEqual(ns.suggestionStore.getSuggestions("form_03", "patent_a"), {});
    assert.equal(ns.suggestionStore.getSuggestions("form_03", "patent_b")["sec.a"].value, "Company B");
  });
});

describe("documentStore — the default workspace is shared, not duplicated", () => {
  test("exposes the constant upload and retrieval both depend on", () => {
    const { ns } = bootstrap("documentStore.js");
    assert.equal(typeof ns.documentStore.DEFAULT_WORKSPACE, "string");
    assert.ok(ns.documentStore.DEFAULT_WORKSPACE.length > 0);
  });

  test("ingest stamps documents with exactly that workspace", () => {
    const env = bootstrap("pdfValidation.js", "documentStore.js");
    env.ns.extractionClient = { uploadForExtraction: () => Promise.resolve(null) };
    loadAppScript("documentUpload.js");

    const { accepted } = env.ns.documentUpload.ingestFiles([
      { name: "a.pdf", size: 10, type: "application/pdf" },
    ]);
    assert.equal(accepted[0].workspaceId, env.ns.documentStore.DEFAULT_WORKSPACE);
  });

  test("the workspace sent for extraction matches the one stored", () => {
    const env = bootstrap("pdfValidation.js", "documentStore.js");
    const sent = [];
    env.ns.extractionClient = {
      uploadForExtraction: (id, file, workspaceId) => {
        sent.push(workspaceId);
        return Promise.resolve(null);
      },
    };
    loadAppScript("documentUpload.js");

    const { accepted } = env.ns.documentUpload.ingestFiles([
      { name: "a.pdf", size: 10, type: "application/pdf" },
    ]);

    assert.deepEqual(sent, [accepted[0].workspaceId],
      "a mismatch would file the document under a workspace the UI never queries");
  });
});
