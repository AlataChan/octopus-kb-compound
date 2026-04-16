from pathlib import Path

from octopus_kb_compound.migrate import inspect_vault_for_migration, normalize_vault


def test_migrate_vault_dry_run_reports_missing_required_entry_files(tmp_path: Path):
    (tmp_path / "note.md").write_text("# Loose note\nBody\n", encoding="utf-8")

    report = inspect_vault_for_migration(tmp_path)

    assert report.missing_files == ["AGENTS.md", "wiki/INDEX.md", "wiki/LOG.md"]
    assert report.pages_missing_frontmatter == ["note.md"]


def test_normalize_vault_apply_writes_to_staging_without_touching_source(tmp_path: Path):
    note = tmp_path / "note.md"
    note.write_text("# Loose note\nBody\n", encoding="utf-8")

    report = normalize_vault(tmp_path, apply=True)

    assert report.staging_dir is not None
    staged_note = Path(report.staging_dir) / "note.md"
    assert staged_note.exists()
    assert staged_note.read_text(encoding="utf-8").startswith("---\n")
    assert note.read_text(encoding="utf-8") == "# Loose note\nBody\n"
