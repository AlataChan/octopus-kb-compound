---
name: kb-ingest
description: Use when acquiring a public URL and converting it into a new raw source page for the knowledge base.
---

# KB Ingest

## Overview

Acquire external content and stop at the raw layer.

The goal is to turn a public URL into a new `raw/*.md` evidence page with complete frontmatter and provenance. `kb-ingest` does not update wiki concept pages, indexes, or logs.

## Workflow

1. Validate that the target is a public `http/https` URL.
2. Fetch markdown through the configured acquisition path.
3. Generate standard raw-source frontmatter and provenance fields.
4. Write a new file under `raw/` without overwriting an existing source.
5. Hand off to `kb-maintain` if the wiki needs to be updated afterward.

## Rules

- Never overwrite an existing raw file.
- Keep provenance in frontmatter, not in ad hoc inline notes.
- Reject localhost and private-network URLs.
- Stop after creating the raw source. Wiki maintenance belongs to `kb-maintain`.

## Output Contract

- created raw page path
- extracted or fallback title
- provenance fields written
- follow-up note when `kb-maintain` should run next

See `references/ingest-checklist.md` when you need the compact acquisition checklist.
