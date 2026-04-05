# v0.1.0 Release And Production Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship `octopus-kb-compound` as a first GitHub-ready release and migrate the existing LLM vault into the framework as the first production profile.

**Architecture:** Keep the repository generic while adding the minimum release-grade assets: changelog, release notes, CI, and migration scripts. Extend the core helpers just enough to support real Obsidian vault behavior, especially filename/path-based links and scoped vault scanning via a profile file.

**Tech Stack:** Python 3.11+, pytest, Git, GitHub Actions, markdown vault files.

---

### Task 1: Add release-grade repository assets

**Files:**
- Create: `CHANGELOG.md`
- Create: `docs/releases/v0.1.0.md`
- Create: `.github/workflows/ci.yml`
- Modify: `README.md`
- Modify: `docs/getting-started.md`

**Step 1: Add changelog and release notes**

- Summarize the framework scope, CLI, skills, prompts, and example vault.
- Include verification commands and a concise roadmap pointer.

**Step 2: Add CI workflow**

- Run pytest on push and pull_request.
- Keep it dependency-light and aligned with local commands.

**Step 3: Update README/docs**

- Surface release docs, CI, and production-profile support.
- Keep setup instructions stable for both editable install and `PYTHONPATH=src` use.

### Task 2: Extend core helpers for real production vaults

**Files:**
- Create: `src/octopus_kb_compound/profile.py`
- Modify: `src/octopus_kb_compound/models.py`
- Modify: `src/octopus_kb_compound/links.py`
- Modify: `src/octopus_kb_compound/lint.py`
- Modify: `src/octopus_kb_compound/vault.py`
- Modify: `src/octopus_kb_compound/cli.py`
- Test: `tests/test_links.py`
- Test: `tests/test_lint.py`
- Test: `tests/test_vault.py`
- Test: `tests/test_cli.py`

**Step 1: Add failing tests**

- Cover filename/path-based wikilinks.
- Cover folder-like and code-noise pseudo links that should not be linted as real wikilinks.
- Cover vault profile loading and ignore rules.

**Step 2: Implement minimal support**

- Load an optional vault profile file from the vault root.
- Extend alias resolution to include file stem and relative path aliases.
- Filter out hidden/config/tooling directories through profile-aware scanning.
- Keep collision detection and existing alias behavior intact.

**Step 3: Verify**

- Run focused tests, then full pytest.
- Run CLI smoke checks against both the minimal example and the production vault.

### Task 3: Migrate the current LLM vault into a production profile

**Files:**
- Create: `/Users/apple/Documents/2.1 AI Journey/7.1 LLMs/AGENTS.md`
- Create: `/Users/apple/Documents/2.1 AI Journey/7.1 LLMs/.octopus-kb.yml`
- Create: `/Users/apple/Documents/2.1 AI Journey/7.1 LLMs/wiki/LOG.md`
- Create: `docs/production-vault.md`
- Create: `scripts/bootstrap_vault.py`

**Step 1: Create framework entry files in the real vault**

- Add a root `AGENTS.md` that points to the schema and retrieval/maintenance flow.
- Add a scoped `.octopus-kb.yml` describing include/exclude behavior.
- Add a `wiki/LOG.md` maintenance trail for the production vault.

**Step 2: Add migration tooling/docs**

- Document the production profile format in the repo.
- Add a bootstrap script so the pattern is reusable beyond the current vault.

**Step 3: Verify**

- Run CLI lint against the real vault with the new profile-aware behavior.
- Confirm the new entry files are parseable and useful.

### Task 4: Cut the local release

**Files:**
- Modify: repository Git history only

**Step 1: Verify final state**

- Run full pytest.
- Run CLI smoke checks.
- Inspect `git status`.

**Step 2: Create first commit and tag**

- Commit the repository as the initial open-source release.
- Add tag `v0.1.0`.

**Step 3: Report push guidance**

- Explain remote setup status.
- Explain folder-move implications before or after pushing.
