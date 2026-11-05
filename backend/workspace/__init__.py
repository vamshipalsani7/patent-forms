"""Workspace read-models — consolidated views over a PatentProfile.

This package is the Patent Workspace's data source. It is a projection layer,
the sibling of autofill/ (which projects the same profile onto a specific form):
it reads facts and never produces them, owns no persistence, and knows nothing
about any IPO form. Its only job is to answer "what do we know about this patent
matter, where did each fact come from, and what is missing or disputed?"
"""
