# Application Shell (V1)

The desktop app's UI shell: sidebar + main area, built around the generic
form renderer in `../renderer/`. Plain scripts, no bundler — each file
attaches to `window.PatentFormsApp.<name>`, mirroring how `../renderer/`
attaches to `window.FormRenderer`.

## Module boundaries

| File | Owns | Does NOT know about |
|---|---|---|
| `dom.js` | one tiny `el()` helper | anything else |
| `pdfValidation.js` | `isPdf(file)` — pure file-type check | DOM, storage, everything else |
| `documentStore.js` | Storage: localStorage CRUD for document **metadata** (`id, originalFilename, displayTitle, size, uploadedAt`) — never file bytes | DOM, forms, the renderer |
| `documentUpload.js` | Upload: `ingestFiles(files)` — validates raw `File` objects and turns accepted ones into metadata via `documentStore` | DOM, forms, the renderer |
| `documentWorkspace.js` | UI: Documents panel — dropzone (click + drag/drop) and document list; wires remove/rename | forms, `formCatalog`/`formLoader`/`formState`, the renderer |
| `formCatalog.js` | static `{formId, formNumber, officialName}` list (navigation metadata only) | field/section content, the renderer, documents |
| `formLoader.js` | `loadDefinition(formId)` — fetch + cache `.definition.json` files | the sidebar, the renderer, storage, documents |
| `formState.js` | `loadDraft` / `saveDraft` / `clearDraft` — localStorage persistence for form drafts | the DOM, the renderer, documents |
| `sidebar.js` | Forms panel DOM: search box, filtered list; emits `onSelect(formId)` | form definitions, the renderer, storage, documents |
| `mainArea.js` | welcome / loading / unavailable states, form toolbar, **the only module that calls `window.FormRenderer.mount()`** | the sidebar, the catalog, documents |
| `app.js` | wiring: mounts the Document Workspace and the Forms sidebar side by side; connects sidebar selection → `loadDefinition` → `mainArea` | rendering internals, storage internals |
| `../renderer/form-renderer.js` | all rendering logic (unchanged from the approved proof) | formId, catalog, storage, documents, the app shell entirely |

Data flows one direction: `app.js` reads a selection from `sidebar.js`, asks
`formLoader.js` for a definition, and hands it to `mainArea.js`, which reads/
writes drafts via `formState.js` and mounts `../renderer/form-renderer.js`
with `(definition, values, callbacks)`. No module reaches "sideways" into
another's internals.

**The Document Workspace (`pdfValidation.js` / `documentStore.js` /
`documentUpload.js` / `documentWorkspace.js`) is a fully separate branch of
that same one-way flow.** `app.js` mounts it independently in the same
`boot()` call that mounts the sidebar — the two are siblings, not
dependents. Neither the Document Workspace nor the renderer references the
other anywhere in the code; only `app.js` knows both exist.

### Disclosed layout change (Sprint 1)

The app-level brand block ("Patent Forms") moved out of `sidebar.js` into a
shared `#appbar` in `index.html`, since the recommended layout puts it above
*both* the Documents and Forms panels, not owned by the forms panel alone.
`sidebar.js` gained a "Search Forms" heading in its place; its search/list/
selection logic is otherwise unchanged. This is the only edit made to an
already-approved file in Sprint 1.

## Adding a future feature

- **Preview / Export**: a new `preview.js` / `exportPdf.js` reading
  `rendererController.getValues()` (already exposed) plus the `definition` —
  hook it into `mainArea.js`'s toolbar. No renderer change needed.
- **Extraction Engine** (Upload → Extraction → Structured Patent Data →
  Auto-fill Renderer): connects at **two** existing, already-separated seams
  — no redesign of this feature required:
  1. **Ingestion side** — `documentUpload.js`'s `ingestFiles()` already has
     the raw `File` and its freshly-minted metadata `id` at the moment of
     upload, before anything renders. A future extraction call (e.g.
     `extractionEngine.enqueue(file, meta.id)`) slots in right there,
     running asynchronously and writing its output to a new, separate
     "structured patent data" store keyed by document `id` — exactly the
     same Storage-module pattern as `documentStore.js`/`formState.js`.
  2. **Auto-fill side** — `mainArea.js`'s `showForm()` currently computes
     `initialValues` from a saved draft only
     (`var initialValues = saved ? saved.values : {}`). That is precisely
     where auto-fill suggestions would be merged in before calling
     `FormRenderer.mount()` — using the per-field `autofill` hints already
     present in every form definition (schema-approved, currently unused).
     The renderer needs no change: it already accepts pre-filled
     `initialValues` and never locks them, so extracted values stay fully
     user-editable, per the product principle "the software suggests, the
     user decides."
- **Validation**: `FormRenderer.mount(...)`'s `onGapsChange(gaps, findings)`
  callback is already wired as a seam; a validation module can also read
  `definition.constraints` / per-field `validation` directly, independent of
  rendering.
- **A new form (e.g. Form 13)**: needs no code change anywhere in this
  folder or in `../renderer/` — see the root `V1_APPLICATION.md` notes for
  why.

## Run

Serve the **repository root** (not just `frontend/`) so `/docs/...` resolves:

```bash
python -m http.server 8991 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8991/frontend/app/index.html`.

The pre-existing Vite prototype at `frontend/index.html` / `frontend/src/`
(the PDF-upload landing page from an earlier phase) was left untouched — this
app shell is a separate, static entry point, matching how `../renderer/` was
already structured before this change.
