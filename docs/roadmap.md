# Roadmap

## Near Term

- Expand `kb-ingest` with local file conversion through an optional dependency while keeping the core package standard-library only.
- Add richer frontmatter helpers for entities, aliases, and change logs.
- Expand lint to catch duplicate canonical pages and unresolved aliases.
- Add CLI support for vault summaries and impacted-page reporting.
- Publish a larger example vault with entity, comparison, and timeline pages.

## Mid Term

- Add graph-oriented retrieval helpers for concept-to-entity traversal.
- Add deterministic maintenance planners for ingest and wiki updates.
- Provide packaging instructions for installing the skills into local agent environments.
- Add CI so tests and smoke checks run on every push.

## Longer Term

- Support knowledge-base migration and normalization from existing Obsidian vaults.
- Add export paths for graph-aware retrieval systems and GraphRAG pipelines.
- Offer templates for team workflows, not just solo vaults.

## 0.2.1 Remediation (2026-04-17)

Applied the Codex 2026-04-17 review findings on the 0.2.0 roadmap release:

- lint: raw sources no longer canonicalize on `canonical_name` alone; wiki pages without a title now fall back to their path stem.
- frontmatter: user-content scalars (`tags`, `related_entities`, `workflow`, `status`, `source_of_truth`, `original_format`, `ingest_method`) are quoted for safe YAML round-trips.
- export: alias nodes deduplicated by id, `related_entities` resolved as page-to-page `wikilink` edges, artifact directory writes are atomic with backup/restore.
- migrate: in-place apply uses two-phase commit with an explicit `_replace_staged_file` boundary, rolls back modified *and* created files, and cleans up staged temp files on failure.
- migrate preflight: malformed frontmatter (opening fence without closing) is reported as `parse_failures` and blocks `--apply`.
- cli: exit codes match the plan contract (`0`/`2`/`1`). Validation factored into `_validate_vault_dir` and `_validate_page_file`.

### Deferred follow-ups

- Vault sandbox (`Path.resolve().is_relative_to(vault.resolve())`) for vault-scoped CLI commands. Requires a policy decision on whether the tool may operate on paths outside the vault.
- SSRF hardening by DNS resolution in `ingest.py`. Currently rejects literal private IPs; hostnames that resolve to private addresses are still accepted. Requires a policy decision on adding DNS to the ingest hot path.
