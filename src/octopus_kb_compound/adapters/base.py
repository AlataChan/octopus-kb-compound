from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from octopus_kb_compound.ckr.models import CanonicalPage, CanonicalRef, StorageRef
from octopus_kb_compound.ckr.operations import CanonicalOp


@dataclass(slots=True)
class WriteReceipt:
    """Adapter write result in path/storage terms for audit compatibility."""

    created: list[StorageRef] = field(default_factory=list)
    modified: list[StorageRef] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[dict[str, str]]]:
        return {
            "created": [ref.to_dict() for ref in self.created],
            "modified": [ref.to_dict() for ref in self.modified],
        }


class KnowledgeStore(Protocol):
    """Protocol implemented by endpoint adapters."""

    def list_pages(self) -> list[CanonicalPage]:
        ...

    def read_page(self, ref: CanonicalRef | StorageRef) -> CanonicalPage:
        ...

    def resolve_alias(self, term: str) -> CanonicalRef | None:
        ...

    def apply_ops(self, ops: list[CanonicalOp]) -> WriteReceipt:
        ...

