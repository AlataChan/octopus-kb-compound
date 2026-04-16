from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import os
import shutil

from octopus_kb_compound.frontmatter import parse_document, render_frontmatter
from octopus_kb_compound.models import PageMeta


REQUIRED_FILES = ("AGENTS.md", "wiki/INDEX.md", "wiki/LOG.md")


@dataclass(slots=True)
class MigrationReport:
    missing_files: list[str] = field(default_factory=list)
    pages_missing_frontmatter: list[str] = field(default_factory=list)
    parse_failures: list[str] = field(default_factory=list)
    normalized_files: list[str] = field(default_factory=list)
    staging_dir: str | None = None
    backup_dir: str | None = None


def inspect_vault_for_migration(root: str | Path) -> MigrationReport:
    root_path = Path(root)
    report = MigrationReport()
    report.missing_files = [path for path in REQUIRED_FILES if not (root_path / path).exists()]

    for path in sorted(root_path.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(root_path).parts):
            continue
        rel = path.relative_to(root_path).as_posix()
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            frontmatter, _ = parse_document(raw)
        except OSError:
            report.parse_failures.append(rel)
            continue
        if not frontmatter:
            report.pages_missing_frontmatter.append(rel)
    return report


def normalize_vault(root: str | Path, *, apply: bool = False, in_place: bool = False) -> MigrationReport:
    root_path = Path(root)
    report = inspect_vault_for_migration(root_path)
    if not apply or report.parse_failures:
        return report

    timestamp = _timestamp()
    if in_place:
        backup_dir = root_path / ".octopus-kb-migration" / "backups" / timestamp
        report.backup_dir = str(backup_dir)
        try:
            _backup_files(root_path, backup_dir, report.pages_missing_frontmatter + report.missing_files)
            _write_normalized_files(root_path, root_path, report)
        except OSError:
            _restore_backup(root_path, backup_dir)
            raise
        return report

    staging_dir = root_path / ".octopus-kb-migration" / "staging" / timestamp
    report.staging_dir = str(staging_dir)
    _copy_markdown_tree(root_path, staging_dir)
    _write_normalized_files(root_path, staging_dir, report)
    return report


def render_migration_report(report: MigrationReport) -> str:
    lines: list[str] = []
    for path in report.missing_files:
        lines.append(f"missing_file\t{path}")
    for path in report.pages_missing_frontmatter:
        lines.append(f"missing_frontmatter\t{path}")
    for path in report.parse_failures:
        lines.append(f"parse_failure\t{path}")
    for path in report.normalized_files:
        lines.append(f"normalized\t{path}")
    if report.staging_dir:
        lines.append(f"staging_dir\t{report.staging_dir}")
    if report.backup_dir:
        lines.append(f"backup_dir\t{report.backup_dir}")
    return "\n".join(lines)


def _write_normalized_files(source_root: Path, target_root: Path, report: MigrationReport) -> None:
    for rel in report.pages_missing_frontmatter:
        source = source_root / rel
        target = target_root / rel
        raw = source.read_text(encoding="utf-8", errors="replace")
        content = f"{render_frontmatter(_default_meta_for_path(Path(rel)))}\n{raw.rstrip()}\n"
        _atomic_write(target, content)
        report.normalized_files.append(rel)

    for rel in report.missing_files:
        target = target_root / rel
        content = _default_required_file(rel)
        _atomic_write(target, content)
        report.normalized_files.append(rel)


def _copy_markdown_tree(source_root: Path, target_root: Path) -> None:
    for source in sorted(source_root.rglob("*.md")):
        relative = source.relative_to(source_root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _backup_files(source_root: Path, backup_root: Path, relatives: list[str]) -> None:
    for rel in relatives:
        source = source_root / rel
        if not source.exists():
            continue
        target = backup_root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _restore_backup(target_root: Path, backup_root: Path) -> None:
    if not backup_root.exists():
        return
    for backup in sorted(backup_root.rglob("*")):
        if not backup.is_file():
            continue
        target = target_root / backup.relative_to(backup_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup, target)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _default_meta_for_path(path: Path) -> PageMeta:
    return PageMeta(
        title=path.stem,
        page_type="note",
        lang="en",
        role="note",
        layer="wiki",
        tags=[],
        summary="",
    )


def _default_required_file(rel: str) -> str:
    title = Path(rel).stem
    role = {"AGENTS.md": "schema", "wiki/INDEX.md": "index", "wiki/LOG.md": "log"}[rel]
    meta = PageMeta(title=title, page_type="meta", lang="en", role=role, layer="wiki", tags=[], summary="")
    return f"{render_frontmatter(meta)}\n# {title}\n"


def _timestamp() -> str:
    return datetime.now().astimezone().strftime("%Y%m%d%H%M%S")
