from pathlib import Path

from octopus_kb_compound.profile import VaultProfile
from octopus_kb_compound.vault import load_page, scan_markdown_files


def test_scan_markdown_files_skips_hidden_directories(tmp_path: Path):
    visible = tmp_path / "wiki" / "note.md"
    hidden = tmp_path / ".obsidian" / "ignore.md"
    visible.parent.mkdir(parents=True)
    hidden.parent.mkdir(parents=True)
    visible.write_text("# visible\n", encoding="utf-8")
    hidden.write_text("# hidden\n", encoding="utf-8")

    pages = scan_markdown_files(tmp_path)

    assert [Path(page.path).name for page in pages] == ["note.md"]


def test_load_page_replaces_invalid_utf8_bytes(tmp_path: Path):
    path = tmp_path / "broken.md"
    path.write_bytes(b'---\ntitle: "Bad\xff"\n---\nBody')

    page = load_page(path)

    assert page.title.startswith("Bad")
    assert "\ufffd" in page.title


def test_scan_markdown_files_respects_profile_excludes(tmp_path: Path):
    included = tmp_path / "wiki" / "note.md"
    excluded = tmp_path / "output" / "report.md"
    included.parent.mkdir(parents=True)
    excluded.parent.mkdir(parents=True)
    included.write_text("# wiki\n", encoding="utf-8")
    excluded.write_text("# report\n", encoding="utf-8")

    pages = scan_markdown_files(tmp_path, VaultProfile(exclude_globs=["output/**"]))

    assert [Path(page.path).as_posix() for page in pages] == ["wiki/note.md"]
