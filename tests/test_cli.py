from pathlib import Path

from octopus_kb_compound.cli import main


def test_cli_lint_missing_vault_returns_error(tmp_path: Path, capsys):
    exit_code = main(["lint", str(tmp_path / "missing")])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "does not exist" in captured.err


def test_cli_suggest_links_missing_page_returns_error(tmp_path: Path, capsys):
    vault = tmp_path / "vault"
    vault.mkdir()

    exit_code = main(["suggest-links", str(vault / "missing.md"), "--vault", str(vault)])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "does not exist" in captured.err


def test_cli_lint_uses_profile_to_exclude_directories(tmp_path: Path, capsys):
    (tmp_path / ".octopus-kb.yml").write_text("exclude_globs:\n  - output/**\n", encoding="utf-8")
    included = tmp_path / "wiki" / "note.md"
    excluded = tmp_path / "output" / "noise.md"
    included.parent.mkdir(parents=True)
    excluded.parent.mkdir(parents=True)
    included.write_text("---\ntitle: Note\nrole: concept\nlayer: wiki\nsummary: ok\n---\n", encoding="utf-8")
    excluded.write_text("---\ntitle: Noise\nlayer: wiki\n---\n", encoding="utf-8")

    exit_code = main(["lint", str(tmp_path)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "wiki/note.md" in captured.out
    assert "noise.md" not in captured.out
