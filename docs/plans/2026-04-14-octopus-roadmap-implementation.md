# Octopus Roadmap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the currently missing `octopus-kb-compound` roadmap capabilities in verified phases so the project evolves from scaffold to a usable knowledge-base operating system.

**Architecture:** Build the missing features from the deterministic core outward. First strengthen the metadata model and linting contract, then add operator-facing CLI surfaces, then add retrieval/planning/migration/export layers on top of the stabilized vault model. Every phase must be independently testable, must preserve current CLI behavior, and must stop behind a validation gate before the next phase starts.

**Tech Stack:** Python 3.11, `pytest`, setuptools CLI entrypoints, markdown vault fixtures, optional `markitdown` ingest path

---

## Delivery Rules

- Execute phases in order.
- Do not start the next phase until the current phase is green.
- Use TDD for every new behavior: failing test, verify failure, minimal implementation, verify pass.
- Regression guard tests are allowed in Phase 0 when no new runtime behavior is being introduced. Mark them explicitly as regression guards and expect PASS, not FAIL.
- Prefer deterministic helpers over LLM-only behavior when a workflow can be encoded in code.
- Keep raw-source mutation conservative: no body rewrites unless explicitly required.
- After each task, run the targeted test first, then the full `pytest -q` suite.
- Update `CHANGELOG.md` in every phase commit with a short `Unreleased` entry for user-visible commands, schema changes, migration behavior, exports, or docs/examples.
- Bump the package version when the feature set crosses a release boundary:
  - Keep `0.1.x` for internal plan/test/doc-only changes and bugfixes.
  - Bump `0.1.0` to `0.2.0` after Phase 2 is complete because the public CLI surface and metadata/lint contract have expanded.
  - Use patch bumps after `0.2.0` for compatible bugfixes and docs-only release polish.

## Current Baseline

- Existing CLI commands: `lint`, `suggest-links`, `ingest-url`, `ingest-file`
- Existing deterministic helpers: frontmatter parse/render, URL/file ingest, wikilink extraction, alias resolution, lint, vault profile scan
- Existing gaps from roadmap:
  - richer frontmatter helpers for entities, aliases, and change logs
  - lint support for duplicate canonical pages and unresolved aliases
  - CLI support for vault summaries and impacted-page reporting
  - larger example vault with entity, comparison, and timeline pages
  - graph-oriented retrieval helpers for concept-to-entity traversal
  - deterministic maintenance planners for ingest and wiki updates
  - migration and normalization support for existing Obsidian vaults
  - export paths for graph-aware retrieval and GraphRAG pipelines
  - packaging/install docs for skills and team workflows

## Phase Gates

- `Phase 0`: planning artifacts and baseline verification complete
- `Phase 1`: metadata and lint model stabilized
- `Phase 2`: operator CLI expanded and documented
- `Phase 3`: retrieval helpers added with deterministic traversal tests
- `Phase 4`: maintenance planner emits stable impacted-page plans
- `Phase 5`: migration/normalization supports dry-run and apply modes
- `Phase 6`: export layer emits validated graph-ready artifacts
- `Phase 7`: examples and docs represent the final workflow

## CLI Contract

- New CLI commands return exit code `0` on success, `2` for invalid user input such as missing paths or parseable but invalid vault state, and `1` only for unexpected runtime errors.
- Commands that write files must support a dry-run mode unless the task explicitly states the command is read-only.
- Help text tests must avoid brittle full-output snapshots. Assert command presence by checking the parser command registry or stable command tokens, not exact line ordering or complete help text.
- When new commands are added, update the baseline command list used by regression tests rather than freezing Phase 0 help output forever.

### Task 1: Phase 0 Baseline Audit

**Files:**
- Create: `docs/plans/2026-04-14-octopus-roadmap-implementation.md`
- Modify: `README.md`
- Modify: `docs/roadmap.md`
- Modify: `CHANGELOG.md`
- Test: `tests/test_cli.py`

**Step 1: Add the regression guard test**

Add a regression test in `tests/test_cli.py` that asserts the parser still exposes the current baseline commands after future additions. This is a regression guard, not a RED-phase test, because the current CLI commands already exist.

```python
def test_cli_parser_includes_existing_baseline_commands():
    parser = build_parser()
    subparsers_action = next(
        action
        for action in parser._actions
        if getattr(action, "dest", None) == "command"
    )
    commands = set(subparsers_action.choices)
    assert {"lint", "suggest-links", "ingest-url", "ingest-file"} <= commands
```

Do not assert full `--help` output or exact command ordering. Future commands should be added to the parser without breaking this guard.

**Step 2: Run regression guard**

Run: `PYTHONPATH=src python3 -m pytest tests/test_cli.py::test_cli_parser_includes_existing_baseline_commands -v`
Expected: PASS because the baseline commands already exist. If this fails, the existing CLI contract has regressed and must be fixed before continuing.

**Step 3: Write minimal implementation**

Add the test only. If the CLI help contract needs stabilization, make the smallest update in `src/octopus_kb_compound/cli.py` to keep command registration deterministic. This task does not introduce a new CLI command.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_cli.py::test_cli_parser_includes_existing_baseline_commands -v`
Expected: PASS

**Step 5: Verify baseline suite**

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add docs/plans/2026-04-14-octopus-roadmap-implementation.md README.md docs/roadmap.md CHANGELOG.md tests/test_cli.py src/octopus_kb_compound/cli.py
git commit -m "docs: add roadmap implementation plan and baseline contract"
```

### Task 2: Phase 1 Metadata Model Expansion

**Files:**
- Modify: `src/octopus_kb_compound/models.py`
- Modify: `src/octopus_kb_compound/frontmatter.py`
- Create: `src/octopus_kb_compound/page_types.py`
- Modify: `src/octopus_kb_compound/__init__.py`
- Modify: `CHANGELOG.md`
- Test: `tests/test_frontmatter.py`

**Module boundary:**
- `models.py` owns passive dataclasses only. Extend `PageMeta` there and do not add page-construction policy to this file.
- `page_types.py` owns opinionated factory helpers such as `make_concept_meta()`, `make_entity_meta()`, `make_comparison_meta()`, `make_timeline_meta()`, and `make_changelog_meta()`.
- `frontmatter.py` owns serialization/parsing of `PageMeta` fields to and from markdown frontmatter.
- All `make_*_meta()` helpers return `PageMeta`, not a new dataclass. Avoid introducing a parallel metadata model.

**New `PageMeta` fields:**
- `canonical_name: str | None = None`
- `status: str | None = None`; allowed values are `draft`, `active`, `deprecated`, and `archived`
- `source_of_truth: str | None = None`; allowed values are `canonical`, `supporting`, `derived`, and `external`
- `related_entities: list[str] = field(default_factory=list)`; values are canonical page titles or canonical entity names
- `changelog: list[str] = field(default_factory=list)`; values are short dated strings such as `2026-04-14: normalized aliases`

**Step 1: Write the failing test**

Add tests for richer page metadata helpers:
- concept page metadata
- entity page metadata
- comparison page metadata
- timeline page metadata
- changelog/log entry metadata

```python
def test_make_entity_meta_renders_expected_fields():
    meta = make_entity_meta(...)
    rendered = render_frontmatter(meta)
    assert 'type: entity' in rendered
    assert 'canonical_name:' in rendered
    assert 'source_of_truth: canonical' in rendered
    assert 'related_entities:' in rendered
    assert 'aliases:' in rendered
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_frontmatter.py::test_make_entity_meta_renders_expected_fields -v`
Expected: FAIL with missing helper import or missing field assertions.

**Step 3: Write minimal implementation**

Implement explicit helper constructors in `page_types.py` and extend `PageMeta` with fields needed for:
- `canonical_name: str | None`
- `status: str | None`
- `source_of_truth: str | None`
- `related_entities: list[str]`
- `changelog: list[str]`

Update `render_frontmatter()` and `parse_document()` support only for the new deterministic fields.
Update `src/octopus_kb_compound/__init__.py` so `page_types` is listed in `__all__`.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_frontmatter.py -q`
Expected: PASS

**Step 5: Verify full suite**

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add src/octopus_kb_compound/models.py src/octopus_kb_compound/frontmatter.py src/octopus_kb_compound/page_types.py src/octopus_kb_compound/__init__.py tests/test_frontmatter.py CHANGELOG.md
git commit -m "feat: add structured page metadata helpers"
```

### Task 3: Phase 1 Lint Expansion

**Files:**
- Modify: `src/octopus_kb_compound/lint.py`
- Modify: `src/octopus_kb_compound/links.py`
- Modify: `CHANGELOG.md`
- Test: `tests/test_lint.py`
- Test: `tests/test_links.py`

**Canonical semantics:**
- A page's canonical identity is the normalized value of the first available field in this order:
  1. `frontmatter["canonical_name"]`
  2. `frontmatter["title"]` when `frontmatter["source_of_truth"] == "canonical"`
  3. `frontmatter["title"]` for non-raw wiki pages where `role != "raw_source"` and `type != "raw_source"`
  4. the markdown path stem as a fallback for non-raw wiki pages only
- Raw source pages are not canonical pages unless they explicitly set `source_of_truth: canonical`.
- `DUPLICATE_CANONICAL_PAGE` is emitted when two or more canonical-eligible pages normalize to the same canonical identity.
- `CANONICAL_ALIAS_COLLISION` is emitted when a frontmatter alias normalizes to another page's canonical identity.

**Alias lint semantics:**
- Existing `BROKEN_LINK` remains body-only: it checks markdown wikilink targets extracted from page bodies against the alias index.
- New alias lint checks frontmatter declarations only. For every `frontmatter["aliases"]` item, normalize the alias and require it to resolve to exactly the declaring page in the alias index.
- Empty or punctuation-only aliases produce `UNRESOLVED_ALIAS` because they cannot produce a resolvable alias key.
- Aliases removed from `build_alias_index()` because they point to multiple pages remain `ALIAS_COLLISION`, not `UNRESOLVED_ALIAS`.
- Alias values that normalize to a canonical identity owned by a different page produce `CANONICAL_ALIAS_COLLISION`.

**Step 1: Write the failing test**

Add tests for:
- duplicate canonical pages
- unresolved aliases declared in frontmatter
- entity/concept canonical conflicts
- log/index expectations where appropriate

```python
def test_lint_reports_duplicate_canonical_pages():
    pages = [...]
    findings = lint_pages(pages)
    assert any(f.code == "DUPLICATE_CANONICAL_PAGE" for f in findings)


def test_lint_reports_unresolved_frontmatter_alias():
    pages = [...]
    findings = lint_pages(pages)
    assert any(f.code == "UNRESOLVED_ALIAS" for f in findings)
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_lint.py::test_lint_reports_duplicate_canonical_pages -v`
Expected: FAIL because the lint rule does not exist yet.

**Step 3: Write minimal implementation**

Add canonical-page detection logic using explicit metadata first and title/path fallback second.
Add alias validation that distinguishes:
- ambiguous aliases
- frontmatter aliases that cannot resolve to the declaring page
- aliases colliding with canonical titles

Keep the output in `LintFinding` form with deterministic codes and messages.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_lint.py tests/test_links.py -q`
Expected: PASS

**Step 5: Verify full suite**

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add src/octopus_kb_compound/lint.py src/octopus_kb_compound/links.py tests/test_lint.py tests/test_links.py CHANGELOG.md
git commit -m "feat: expand lint with canonical and alias validation"
```

### Task 4: Phase 2 Vault Summary CLI

**Files:**
- Modify: `src/octopus_kb_compound/cli.py`
- Create: `src/octopus_kb_compound/summary.py`
- Modify: `src/octopus_kb_compound/__init__.py`
- Modify: `CHANGELOG.md`
- Test: `tests/test_cli.py`
- Test: `tests/test_vault.py`

**Step 1: Write the failing test**

Add CLI tests for `vault-summary <vault>` that assert the command reports:
- total page count
- page counts by type/role/layer
- lint finding counts
- schema/index/log presence

```python
def test_cli_vault_summary_reports_structure(tmp_path, capsys):
    ...
    assert "total_pages" in output
    assert "concept" in output
    assert "raw_source" in output
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_cli.py::test_cli_vault_summary_reports_structure -v`
Expected: FAIL because `vault-summary` does not exist.

**Step 3: Write minimal implementation**

Implement a summary helper that scans the vault, computes deterministic counts, and prints stable text or JSON-like lines.
Expose it via `vault-summary` in `cli.py`.
Update `src/octopus_kb_compound/__init__.py` so `summary` is listed in `__all__`.
CLI exit codes: `0` for a valid summary, `2` when the vault path is missing, not a directory, or cannot be scanned as a markdown vault.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_cli.py::test_cli_vault_summary_reports_structure -v`
Expected: PASS

**Step 5: Verify full suite**

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add src/octopus_kb_compound/cli.py src/octopus_kb_compound/summary.py src/octopus_kb_compound/__init__.py tests/test_cli.py tests/test_vault.py CHANGELOG.md
git commit -m "feat: add vault summary command"
```

### Task 5: Phase 2 Impacted Pages CLI

**Files:**
- Modify: `src/octopus_kb_compound/cli.py`
- Create: `src/octopus_kb_compound/impact.py`
- Modify: `src/octopus_kb_compound/__init__.py`
- Modify: `CHANGELOG.md`
- Modify: `pyproject.toml`
- Test: `tests/test_cli.py`
- Create: `tests/test_impact.py`

**Step 1: Write the failing test**

Add tests for `impacted-pages <page> --vault <vault>` that assert the command returns:
- the page itself
- index/log pages when relevant
- linked concepts/entities
- source pages or backlinks influencing maintenance

```python
def test_impacted_pages_includes_index_and_related_pages(...):
    impacted = find_impacted_pages(...)
    assert "wiki/INDEX.md" in impacted
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_impact.py::test_impacted_pages_includes_index_and_related_pages -v`
Expected: FAIL because no impact module exists.

**Step 3: Write minimal implementation**

Implement deterministic impacted-page discovery using:
- page frontmatter
- inbound/outbound wikilinks
- special handling for schema/index/log pages
- raw-to-concept and concept-to-entity relationships from metadata

Expose it via CLI.
Update `src/octopus_kb_compound/__init__.py` so `impact` is listed in `__all__`.
CLI exit codes: `0` when impacted pages are found or the result is an empty valid set, `2` when the vault or page path is invalid.
Because Phase 2 completes the first expanded public CLI surface, bump `pyproject.toml` from `0.1.0` to `0.2.0` in this task and record the release boundary in `CHANGELOG.md`.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_impact.py tests/test_cli.py -q`
Expected: PASS

**Step 5: Verify full suite**

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add src/octopus_kb_compound/cli.py src/octopus_kb_compound/impact.py src/octopus_kb_compound/__init__.py tests/test_cli.py tests/test_impact.py pyproject.toml CHANGELOG.md
git commit -m "feat: add impacted pages reporting"
```

### Task 6: Phase 3 Retrieval Graph Helpers

**Files:**
- Create: `src/octopus_kb_compound/retrieve.py`
- Modify: `src/octopus_kb_compound/__init__.py`
- Modify: `CHANGELOG.md`
- Test: `tests/test_retrieve.py`
- Modify: `skills/kb-retrieve/SKILL.md`

**Step 1: Write the failing test**

Add tests that verify deterministic traversal helpers can:
- load schema/index entry pages
- walk concept to related entity pages
- gather supporting raw pages
- return structured evidence bundles

```python
def test_build_retrieval_bundle_prefers_concepts_then_raw():
    bundle = build_retrieval_bundle(...)
    assert bundle.concepts == [...]
    assert bundle.raw_sources == [...]
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_retrieve.py::test_build_retrieval_bundle_prefers_concepts_then_raw -v`
Expected: FAIL because retrieval helpers are missing.

**Step 3: Write minimal implementation**

Implement deterministic retrieval bundle helpers that encode the project contract:
`schema -> index -> concept -> raw`

The helper should not answer questions itself; it should produce the ordered page set and evidence metadata.
Update `src/octopus_kb_compound/__init__.py` so `retrieve` is listed in `__all__`.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_retrieve.py -q`
Expected: PASS

**Step 5: Verify full suite**

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add src/octopus_kb_compound/retrieve.py src/octopus_kb_compound/__init__.py tests/test_retrieve.py skills/kb-retrieve/SKILL.md CHANGELOG.md
git commit -m "feat: add deterministic retrieval helpers"
```

### Task 7: Phase 4 Maintenance Planner

**Files:**
- Create: `src/octopus_kb_compound/planner.py`
- Modify: `src/octopus_kb_compound/cli.py`
- Modify: `src/octopus_kb_compound/__init__.py`
- Modify: `CHANGELOG.md`
- Create: `tests/test_planner.py`
- Modify: `skills/kb-maintain/SKILL.md`

**Step 1: Write the failing test**

Add tests for a planner that, given a changed page or newly ingested raw source, returns:
- impacted concept pages
- impacted entity pages
- whether `wiki/INDEX.md` should update
- whether `wiki/LOG.md` should update
- suggested actions (`update`, `create_stub`, `review_aliases`)

```python
def test_plan_maintenance_for_new_raw_source_returns_follow_up_actions():
    plan = plan_maintenance(...)
    assert "wiki/LOG.md" in plan.changed_pages
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_planner.py::test_plan_maintenance_for_new_raw_source_returns_follow_up_actions -v`
Expected: FAIL because planner support does not exist.

**Step 3: Write minimal implementation**

Implement a deterministic planner that emits a stable plan object and CLI output.
Do not auto-edit pages in this phase. Only plan and classify follow-up work.
Update `src/octopus_kb_compound/__init__.py` so `planner` is listed in `__all__`.
CLI exit codes: `0` when a plan is produced, `2` when the vault or changed page argument is invalid.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_planner.py -q`
Expected: PASS

**Step 5: Verify full suite**

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add src/octopus_kb_compound/planner.py src/octopus_kb_compound/cli.py src/octopus_kb_compound/__init__.py tests/test_planner.py skills/kb-maintain/SKILL.md CHANGELOG.md
git commit -m "feat: add deterministic maintenance planner"
```

### Task 8: Phase 5 Migration and Normalization

**Files:**
- Create: `src/octopus_kb_compound/migrate.py`
- Modify: `src/octopus_kb_compound/cli.py`
- Modify: `src/octopus_kb_compound/__init__.py`
- Modify: `CHANGELOG.md`
- Create: `tests/test_migrate.py`
- Modify: `docs/production-vault.md`

**Migration safety contract:**
- `inspect-vault <vault>` is read-only and never writes files.
- `normalize-vault <vault>` defaults to dry-run and never writes files unless `--apply` is present.
- `normalize-vault <vault> --apply` writes to a staging directory by default: `<vault>/.octopus-kb-migration/staging/<timestamp>/`. It copies normalized markdown there and leaves the original vault untouched.
- In-place writes require both `--apply` and `--in-place`. Before any in-place write, create a backup under `<vault>/.octopus-kb-migration/backups/<timestamp>/` preserving relative paths.
- Migration uses two phases: preflight scan first, writes second. If any markdown file cannot be read or parsed during preflight, apply mode aborts before writing anything and returns exit code `2` with a report of failed relative paths.
- If an unexpected write failure happens after in-place writes begin, restore every changed file from the backup directory, leave the backup in place, emit the rollback report, and return exit code `1`.
- Writes must be atomic per file: write a temporary file next to the target, then replace the target.
- Apply mode is limited to frontmatter normalization and required entry-file creation. It must not rewrite markdown bodies.

**Step 1: Write the failing test**

Add tests for:
- scanning an existing vault with missing frontmatter
- identifying missing schema/index/log files
- dry-run normalization output
- safe apply mode for frontmatter normalization only

```python
def test_migrate_vault_dry_run_reports_missing_required_entry_files():
    report = inspect_vault_for_migration(...)
    assert "AGENTS.md" in report.missing_files
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_migrate.py::test_migrate_vault_dry_run_reports_missing_required_entry_files -v`
Expected: FAIL because migration support does not exist.

**Step 3: Write minimal implementation**

Implement migration inspection and normalization helpers with a conservative contract:
- report mode first
- dry-run before apply
- frontmatter normalization only for apply mode
- no destructive content rewrites

Expose through CLI commands such as `inspect-vault` and `normalize-vault`.
Update `src/octopus_kb_compound/__init__.py` so `migrate` is listed in `__all__`.
CLI exit codes: `0` for successful inspection/dry-run/apply, `2` for invalid vaults or preflight parse failures, `1` for unexpected I/O failures after rollback.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_migrate.py -q`
Expected: PASS

**Step 5: Verify full suite**

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add src/octopus_kb_compound/migrate.py src/octopus_kb_compound/cli.py src/octopus_kb_compound/__init__.py tests/test_migrate.py docs/production-vault.md CHANGELOG.md
git commit -m "feat: add vault migration and normalization tools"
```

### Task 9: Phase 6 Graph Export

**Files:**
- Create: `src/octopus_kb_compound/export.py`
- Modify: `src/octopus_kb_compound/cli.py`
- Modify: `src/octopus_kb_compound/__init__.py`
- Modify: `CHANGELOG.md`
- Create: `tests/test_export.py`
- Modify: `README.md`

**Export JSON schema:**

`nodes.json` is a JSON array. Every node object must contain:

```json
{
  "id": "page:wiki/concepts/example.md",
  "title": "Example",
  "type": "concept",
  "role": "concept",
  "layer": "wiki",
  "aliases": ["Example Alias"]
}
```

Required node fields:
- `id: str`; stable export id. Page ids use `page:<relative_posix_path>`. Alias ids use `alias:<normalized_alias>`.
- `title: str`; page title, alias text, or hierarchy label.
- `type: str`; examples: `raw_source`, `concept`, `entity`, `comparison`, `timeline`, `log`, `alias`, `folder`.
- `role: str | None`
- `layer: str | None`
- `aliases: list[str]`

`edges.json` is a JSON array. Every edge object must contain:

```json
{
  "source": "page:wiki/concepts/example.md",
  "target": "page:raw/source.md",
  "relation_type": "wikilink"
}
```

Required edge fields:
- `source: str`; source node id from `nodes.json`
- `target: str`; target node id from `nodes.json`
- `relation_type: str`; allowed values are `wikilink`, `alias`, and `hierarchy`

Relation rules:
- `wikilink`: page-to-page edge for markdown body wikilinks resolved through the alias index.
- `alias`: alias node to canonical page node edge for each frontmatter alias.
- `hierarchy`: folder/index/schema/log containment or navigation edge when hierarchy nodes are emitted.

**Step 1: Write the failing test**

Add tests for export helpers that emit graph-aware retrieval artifacts:
- nodes JSON
- edges JSON
- page manifest
- canonical/alias mapping

```python
def test_export_graph_artifacts_emits_nodes_and_edges(tmp_path):
    export_graph_artifacts(...)
    assert (tmp_path / "nodes.json").exists()
    assert (tmp_path / "edges.json").exists()
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_export.py::test_export_graph_artifacts_emits_nodes_and_edges -v`
Expected: FAIL because export support does not exist.

**Step 3: Write minimal implementation**

Implement export helpers based on deterministic vault structure:
- pages become nodes
- wikilinks and metadata references become edges
- aliases and canonical targets become explicit mappings

Expose CLI command such as `export-graph`.
Update `src/octopus_kb_compound/__init__.py` so `export` is listed in `__all__`.
CLI exit codes: `0` for a completed export, `2` for invalid vault or output arguments, `1` for unexpected write failures.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_export.py -q`
Expected: PASS

**Step 5: Verify full suite**

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add src/octopus_kb_compound/export.py src/octopus_kb_compound/cli.py src/octopus_kb_compound/__init__.py tests/test_export.py README.md CHANGELOG.md
git commit -m "feat: add graph export artifacts"
```

### Task 10: Phase 7 Example Vault and Packaging Docs

**Files:**
- Create: `examples/expanded-vault/...`
- Modify: `README.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/repository-layout.md`
- Modify: `prompts/obsidian-graph/README.md`
- Modify: `CHANGELOG.md`
- Test: `tests/test_prompt_assets.py`
- Test: `tests/test_vault.py`

**Step 1: Write the failing test**

Add tests asserting the repository now includes a richer example vault with:
- concept pages
- entity pages
- comparison pages
- timeline pages
- log/index/schema entry files

```python
def test_expanded_example_vault_contains_expected_page_categories():
    ...
    assert ...
```

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m pytest tests/test_vault.py::test_expanded_example_vault_contains_expected_page_categories -v`
Expected: FAIL because the expanded fixture does not exist yet.

**Step 3: Write minimal implementation**

Add the new example vault content and update docs for:
- local skill installation
- team workflow usage
- phase-by-phase operator flow

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m pytest tests/test_vault.py tests/test_prompt_assets.py -q`
Expected: PASS

**Step 5: Verify full suite**

Run: `PYTHONPATH=src python3 -m pytest -q`
Expected: PASS

**Step 6: Commit**

```bash
git add examples README.md docs/getting-started.md docs/repository-layout.md prompts/obsidian-graph/README.md tests/test_vault.py tests/test_prompt_assets.py CHANGELOG.md
git commit -m "docs: add expanded example vault and operator docs"
```

## Execution Notes

- Start with `Phase 0` and `Phase 1`; do not skip directly to CLI or migration work.
- New modules should remain small and deterministic. Avoid building a heavyweight framework if a few clear helpers are enough.
- When adding new CLI commands, keep output stable and human-readable so the skills can depend on it.
- If a phase reveals a schema or metadata mismatch, update the metadata model first and adjust later phases rather than introducing compatibility hacks.

## Final Verification Command

Run after each completed phase:

```bash
PYTHONPATH=src python3 -m pytest -q
PYTHONPATH=src python3 -m octopus_kb_compound.cli --help
```

Run at the end of the full program:

```bash
PYTHONPATH=src python3 -m octopus_kb_compound.cli lint examples/minimal-vault
PYTHONPATH=src python3 -m octopus_kb_compound.cli vault-summary examples/minimal-vault
PYTHONPATH=src python3 -m octopus_kb_compound.cli export-graph examples/minimal-vault --out /tmp/octopus-export
```
