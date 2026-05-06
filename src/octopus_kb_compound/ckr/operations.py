from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypeAlias

from octopus_kb_compound.ckr.models import CanonicalPage, SourceSpan, StorageRef


@dataclass(frozen=True, slots=True)
class CreatePageOp:
    page: CanonicalPage
    rationale: str
    confidence: float
    source_span: SourceSpan | None = None

    def __post_init__(self) -> None:
        _validate_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "op": "create_page",
            "page": self.page.to_dict(),
            "rationale": self.rationale,
            "confidence": self.confidence,
        }
        if self.source_span is not None:
            data["source_span"] = self.source_span.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CreatePageOp:
        span = data.get("source_span")
        return cls(
            page=CanonicalPage.from_dict(data["page"]),
            rationale=str(data.get("rationale") or ""),
            confidence=float(data.get("confidence", 1.0)),
            source_span=SourceSpan.from_dict(span) if span else None,
        )


@dataclass(frozen=True, slots=True)
class AddAliasOp:
    target: StorageRef
    alias: str
    rationale: str
    confidence: float
    source_span: SourceSpan | None = None

    def __post_init__(self) -> None:
        _validate_confidence(self.confidence)
        if not self.alias.strip():
            raise ValueError("alias must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "op": "add_alias",
            "target": self.target.to_dict(),
            "alias": self.alias,
            "rationale": self.rationale,
            "confidence": self.confidence,
        }
        if self.source_span is not None:
            data["source_span"] = self.source_span.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AddAliasOp:
        span = data.get("source_span")
        return cls(
            target=StorageRef.from_dict(data["target"]),
            alias=str(data["alias"]),
            rationale=str(data.get("rationale") or ""),
            confidence=float(data.get("confidence", 1.0)),
            source_span=SourceSpan.from_dict(span) if span else None,
        )


@dataclass(frozen=True, slots=True)
class AppendLogOp:
    target: StorageRef
    entry: str
    rationale: str
    confidence: float

    def __post_init__(self) -> None:
        _validate_confidence(self.confidence)

    def to_dict(self) -> dict[str, Any]:
        return {
            "op": "append_log",
            "target": self.target.to_dict(),
            "entry": self.entry,
            "rationale": self.rationale,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppendLogOp:
        return cls(
            target=StorageRef.from_dict(data["target"]),
            entry=str(data["entry"]),
            rationale=str(data.get("rationale") or ""),
            confidence=float(data.get("confidence", 1.0)),
        )


CanonicalOp: TypeAlias = CreatePageOp | AddAliasOp | AppendLogOp


def operation_from_dict(data: dict[str, Any]) -> CanonicalOp:
    op = data.get("op")
    if op == "create_page":
        return CreatePageOp.from_dict(data)
    if op == "add_alias":
        return AddAliasOp.from_dict(data)
    if op == "append_log":
        return AppendLogOp.from_dict(data)
    raise ValueError(f"unsupported canonical operation: {op}")


def _validate_confidence(value: float) -> None:
    if value < 0 or value > 1:
        raise ValueError("confidence must be between 0 and 1")

