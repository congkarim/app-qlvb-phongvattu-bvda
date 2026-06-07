from typing import Any, Literal

from pydantic import BaseModel, Field


TargetModule = Literal["contract", "dispatch", "decision", "procurement"]
BlockReason = Literal[
    "not_searchable",
    "module_exists",
    "manual_metadata",
    "unmapped_document_type",
    "low_confidence",
]


class OnboardingSuggestionResponse(BaseModel):
    document_id: str
    eligible: bool
    block_reason: BlockReason | None = None
    needs_metadata_review: bool = False
    suggested_business_type: str | None = None
    business_type_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    target_module: TargetModule | None = None
    module_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    module_kind: str | None = None
    reasons: list[str] = Field(default_factory=list)
    suggested_module_fields: dict[str, Any] = Field(default_factory=dict)
