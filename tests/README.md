# Tests

Automated tests for the extraction engine and the app shell.

## Running them

One command, from the repository root:

```bash
python tests/run_tests.py
```

That runs both suites and prints a combined summary. Exit code is `0` when
everything passes, `1` otherwise — so it is usable as a CI gate as-is.

**There is nothing to install first.** The backend tests use Python's stdlib
`unittest` and the frontend tests use Node's built-in `node:test` runner. No
pytest, no npm packages, no test-only dependencies were added to the project.

### Options

```bash
python tests/run_tests.py -v               # per-test output instead of a summary
python tests/run_tests.py --backend-only   # skip the Node suite
python tests/run_tests.py --frontend-only  # skip the Python suite
```

### Running one file

```bash
python -m unittest discover -s tests/backend -p "test_form1_extractor.py" -v
```

```bash
node --test tests/frontend/main_area_separation.test.mjs
```

### Requirements

| Suite | Needs | If missing |
|---|---|---|
| Backend | Python 3.9+, `pydantic`, `fastapi`, `pdfplumber` (already in `backend/requirements.txt`) | tests fail |
| Frontend | Node 18+ (for `node:test`) | suite is **skipped** with a warning; the runner still exits 0 but says coverage is incomplete |

## Layout

```
tests/
├── run_tests.py                        the one command
├── fixtures/
│   ├── form1_sample.pdf                a Form 1 with a text layer
│   └── not_a_patent_form.pdf           an unrelated PDF (negative case)
├── backend/
│   ├── context.py                      sys.path setup + fixture constants
│   ├── test_vocabulary_registry.py
│   ├── test_vocabulary_linter.py
│   ├── test_classifier.py
│   ├── test_form1_extractor.py
│   ├── test_autofill_mapper.py
│   ├── test_profile_builder.py
│   ├── test_suggestions_api.py
│   └── test_integration_vertical_slice.py
└── frontend/
    ├── harness.mjs                     window/document/localStorage shims
    ├── draft_persistence.test.mjs
    ├── workspace_isolation.test.mjs
    └── main_area_separation.test.mjs
```

## What is covered

| Area | File | Notes |
|---|---|---|
| Vocabulary registry | `test_vocabulary_registry.py` | Structure, atomicity, deprecations, the demand-driven invariant, and `DocumentType` ↔ registry alignment |
| Vocabulary linter | `test_vocabulary_linter.py` | Every rule, the F1/F2 defects it was built to catch, the cross-field false positive it must *not* raise, and its exit code |
| Document classifier | `test_classifier.py` | Each anchor, case/whitespace tolerance, `FORM 18` not matching `FORM 1`, and the deliberate `UNKNOWN` fallback |
| Form 1 extractor | `test_form1_extractor.py` | The three slice fields, provenance completeness on every fact, page attribution, tier precedence, and that it invents nothing |
| Autofill mapper | `test_autofill_mapper.py` | Authored source order beating confidence, repeatable array wrapping, nested/table fields, and genericity against an unseen definition |
| Profile builder | `test_profile_builder.py` | Extractor dispatch, unsupported types degrading quietly, and the merged `PatentProfile` projection |
| Suggestion generation | `test_suggestions_api.py` | Response shape, provenance, 404s, upload guards, and content-store durability |
| Workspace isolation | `workspace_isolation.test.mjs` + `test_suggestions_api.py` | `workspaceId` stamping and scoped queries; see the caveat below |
| Draft persistence | `draft_persistence.test.mjs` | Draft round-trip including `userEditedPaths`, per-form scoping, corrupt-storage tolerance |
| Suggested vs user-edited | `main_area_separation.test.mjs` | Finding F3 — the full lifecycle, including that re-extraction refreshes untouched fields but never overwrites a user edit |
| Vertical slice | `test_integration_vertical_slice.py` | Real PDF bytes through the whole chain, with provenance asserted end to end |

## Notes on the approach

**The backend tests call endpoint functions directly, not over HTTP.** FastAPI's
`TestClient` requires `httpx`, which is not installed, and the routing layer is
thin enough that the value lies in the pipeline behind it. Request validation
that FastAPI performs before the handler runs is therefore not exercised.

**The frontend tests run the real `frontend/app/*.js` files** under a minimal
`window`/`document`/`localStorage` shim (`harness.mjs`), not copies. The DOM shim
implements only the element API the app shell actually uses; it is not a jsdom
substitute and should not grow into one. Anything needing real layout or real
event dispatch belongs in a browser.

**`main_area_separation.test.mjs` stubs the renderer** with nothing beyond the
approved `mount`/`getValues`/`setValues`/`getGaps`/`getFindings`/`unmount`
surface. That the suite passes against that stub is the standing evidence that
separating suggested from user-entered values needed no renderer changes — if
`mainArea.js` ever reaches for a capability the renderer does not expose, these
tests break.

**Tests never touch `backend/uploads/`.** Every test that persists anything
redirects `ContentStore` at a temporary directory and restores it afterwards.

## Known coverage gaps

These are deliberate, and stated so they are not mistaken for coverage:

- **Workspace isolation is only enforced frontend-side.** `ContentStore` is
  still a flat pool — `all_extracts()` returns every document regardless of
  workspace, so `GET /api/suggestions/{form_id}` builds one profile from
  everything uploaded. `TestWorkspaceScopingBoundary` in
  `test_suggestions_api.py` records that boundary explicitly. Uploading
  documents for two different patents will merge them; the `workspaceId` field
  exists and is populated, but the backend does not yet filter on it.
- **The AcroForm tier (Tier 1) is tested via a stub, not a real AcroForm PDF.**
  Both fixtures are text-layer PDFs, so `_extract_acroform` returns nothing and
  `TestTierPrecedence` substitutes it to verify precedence.
- **No browser-level tests.** The renderer itself, real DOM events, CSS, and the
  `file://` path resolution are verified manually, not here.
- **OCR, LLM extraction, preview, and export** have no tests because they have
  no implementation.

## Confidence check

The suite was mutation-tested against the three real bugs found while building
the vertical slice, to confirm the tests actually fail when the code is wrong:

| Reintroduced bug | Caught by |
|---|---|
| `valuesEqual` reverted to strict `!==` | `an unchanged array value is not mistaken for an edit` |
| Repeatable array-wrap removed from the mapper | 3 mapper/integration tests |
| `EXTRACTOR_VERSION` class attribute removed | 3 extractor/builder tests |
