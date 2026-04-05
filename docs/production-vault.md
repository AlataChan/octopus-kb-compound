# Production Vaults

A production vault is an existing Obsidian knowledge base that adopts the `octopus-kb-compound` operating model without becoming a toy example.

## Required Entry Files

- `AGENTS.md`: operational entry point for the LLM
- `.octopus-kb.yml`: scan scope, schema path, and excluded directories
- `wiki/LLM_wiki.md` or equivalent schema page
- `wiki/INDEX.md`: navigation hub
- `wiki/LOG.md`: append-only maintenance log

## Recommended Conventions

- Keep raw sources immutable except for frontmatter normalization.
- Put persistent synthesis in `wiki/concepts`, `wiki/entities`, or `wiki/topics`.
- Keep aliases explicit in frontmatter for pages with multiple names.
- Use relative-path wikilinks only when the file structure itself is meaningful.
- Exclude tooling, generated outputs, and editor state from lint with `.octopus-kb.yml`.

## Example Profile

```yaml
schema: AGENTS.md
index: wiki/INDEX.md
exclude_globs:
  - .obsidian/**
  - output/**
  - octopus-kb-compound/**
```

## Bootstrap

Use `scripts/bootstrap_vault.py` to create the initial entry files in an existing vault. The script is intentionally conservative: it creates missing files and leaves source documents untouched.
