"""Filing package generation — the final step before a professional files.

This package turns a completed form (its definition plus the values the user
reviewed) into the four documents a patent professional needs at filing:

    1. the official IPO PDF   — the document that is actually filed
    2. an editable DOCX       — for internal review and last-minute edits
    3. a filing summary       — a one-page record of what was prepared
    4. a provenance report    — an audit trail; NOT filed with the IPO

Everything is generated from the SAME form definitions the renderer draws from,
so field content and section order cannot drift between the screen and the
filed document. There is no second field-mapping and no second source of truth:
the definition decides what a form contains, and this package decides only how
it is laid out on paper.

Nothing internal ever reaches these documents — no vocabulary keys, no
sourceTypes, no confidence figures, no review colours, no JSON.
"""
