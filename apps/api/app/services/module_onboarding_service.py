from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.models.document import Document
from app.repositories.contract_repository import ContractRepository
from app.repositories.decision_repository import DecisionRepository
from app.repositories.dispatch_repository import DispatchRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.procurement_repository import ProcurementRepository


CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.70

BUSINESS_TYPE_TO_MODULE: dict[str, str] = {
    "contract": "contract",
    "incoming_dispatch": "dispatch",
    "outgoing_dispatch": "dispatch",
    "decision": "decision",
    "procurement": "procurement",
}

BUSINESS_TYPE_TO_DISPATCH_TYPE: dict[str, str] = {
    "incoming_dispatch": "incoming",
    "outgoing_dispatch": "outgoing",
}


@dataclass(frozen=True)
class DocumentTypeMapping:
    target_module: str
    suggested_business_type: str | None
    module_kind: str | None
    confidence_base: float


DOCUMENT_TYPE_MAPPINGS: dict[str, DocumentTypeMapping] = {
    "HĐ": DocumentTypeMapping("contract", "contract", None, 0.90),
    "BGN": DocumentTypeMapping("contract", "contract", None, 0.82),
    "BTT": DocumentTypeMapping("contract", "contract", None, 0.82),
    "CV": DocumentTypeMapping("dispatch", None, None, 0.90),
    "CĐ": DocumentTypeMapping("dispatch", "incoming_dispatch", "incoming", 0.90),
    "PG": DocumentTypeMapping("dispatch", "incoming_dispatch", "incoming", 0.78),
    "PC": DocumentTypeMapping("dispatch", "incoming_dispatch", "incoming", 0.78),
    "PB": DocumentTypeMapping("dispatch", "incoming_dispatch", "incoming", 0.78),
    "TCg": DocumentTypeMapping("dispatch", "incoming_dispatch", "incoming", 0.78),
    "QĐ": DocumentTypeMapping("decision", "decision", "decision", 0.94),
    "TB": DocumentTypeMapping("decision", "decision", "notification", 0.93),
    "NQ": DocumentTypeMapping("decision", "decision", "decision", 0.80),
    "KH": DocumentTypeMapping("procurement", "procurement", "plan", 0.90),
    "TTr": DocumentTypeMapping("procurement", "procurement", "proposal", 0.91),
    "BB": DocumentTypeMapping("procurement", "procurement", "acceptance", 0.92),
    "BC": DocumentTypeMapping("procurement", "procurement", "proposal", 0.72),
    "PA": DocumentTypeMapping("procurement", "procurement", "proposal", 0.72),
    "ĐA": DocumentTypeMapping("procurement", "procurement", "proposal", 0.72),
    "DA": DocumentTypeMapping("procurement", "procurement", "proposal", 0.72),
    "CTr": DocumentTypeMapping("procurement", "procurement", "proposal", 0.72),
}


class ModuleOnboardingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.documents = DocumentRepository(db)

    def get_suggestions(self, document_id: str) -> dict[str, Any]:
        document = self.documents.get_document(document_id)
        if document is None:
            return None
        return build_onboarding_suggestion(document, db=self.db)

    def suggest_business_type(self, document: Document) -> dict[str, Any]:
        suggestion = build_onboarding_suggestion(document, db=self.db)
        return {
            "suggested_business_type": suggestion.get("suggested_business_type"),
            "business_type_confidence": suggestion.get("business_type_confidence"),
            "reasons": suggestion.get("reasons", []),
            "eligible": suggestion.get("eligible", False),
            "block_reason": suggestion.get("block_reason"),
        }

    def suggest_module_record(self, document: Document) -> dict[str, Any]:
        suggestion = build_onboarding_suggestion(document, db=self.db)
        return {
            "target_module": suggestion.get("target_module"),
            "module_confidence": suggestion.get("module_confidence"),
            "module_kind": suggestion.get("module_kind"),
            "suggested_module_fields": suggestion.get("suggested_module_fields", {}),
            "reasons": suggestion.get("reasons", []),
            "eligible": suggestion.get("eligible", False),
            "block_reason": suggestion.get("block_reason"),
        }


def build_onboarding_suggestion(
    document: Document,
    *,
    db: Session | None = None,
    require_searchable: bool = True,
) -> dict[str, Any]:
    reasons: list[str] = []
    base = {
        "document_id": document.id,
        "eligible": False,
        "block_reason": None,
        "needs_metadata_review": False,
        "suggested_business_type": None,
        "business_type_confidence": None,
        "target_module": None,
        "module_confidence": None,
        "module_kind": None,
        "reasons": reasons,
        "suggested_module_fields": {},
    }

    if require_searchable and document.status != "searchable":
        base["block_reason"] = "not_searchable"
        reasons.append("document_not_searchable")
        return base

    if _has_manual_metadata_guard(document):
        base["block_reason"] = "manual_metadata"
        reasons.append("metadata_manual_or_reviewed")
        return base

    resolved = resolve_module_target(document, reasons)
    if resolved is None:
        base["block_reason"] = "unmapped_document_type"
        base["needs_metadata_review"] = document.document_type == "UNKNOWN"
        if document.document_type == "UNKNOWN":
            reasons.append("document_type_unknown")
        else:
            reasons.append("document_type_unmapped")
        return base

    target_module, suggested_business_type, module_kind, confidence_base = resolved
    module_confidence = compute_module_confidence(confidence_base, document.classification_confidence)

    base.update(
        {
            "suggested_business_type": suggested_business_type,
            "business_type_confidence": module_confidence,
            "target_module": target_module,
            "module_confidence": module_confidence,
            "module_kind": module_kind,
        }
    )

    if module_confidence < CONFIDENCE_MEDIUM:
        base["block_reason"] = "low_confidence"
        base["needs_metadata_review"] = True
        reasons.append("confidence_below_medium")
        return base

    if db is not None and _module_exists(db, target_module, document.id):
        base["block_reason"] = "module_exists"
        reasons.append("module_record_active")
        return base

    base["eligible"] = True
    base["needs_metadata_review"] = module_confidence < CONFIDENCE_HIGH
    if base["needs_metadata_review"]:
        reasons.append("confidence_needs_confirmation")
    base["suggested_module_fields"] = build_suggested_module_fields(
        target_module=target_module,
        document=document,
        module_kind=module_kind,
    )
    return base


def resolve_module_target(
    document: Document,
    reasons: list[str],
) -> tuple[str, str, str | None, float] | None:
    business_type = _normalize_business_type(document.business_type)
    type_mapping = DOCUMENT_TYPE_MAPPINGS.get(document.document_type or "")

    if business_type and business_type in BUSINESS_TYPE_TO_MODULE:
        target_module = BUSINESS_TYPE_TO_MODULE[business_type]
        suggested_business_type = business_type
        module_kind = _module_kind_from_business_type(business_type, type_mapping)
        confidence_base = type_mapping.confidence_base if type_mapping else 0.80
        reasons.append(f"business_type={business_type}")

        if type_mapping and type_mapping.target_module != target_module:
            reasons.append(
                f"document_type={document.document_type}_differs_from_business_type"
            )
        return target_module, suggested_business_type, module_kind, confidence_base

    if type_mapping is None:
        return None

    if type_mapping.target_module == "dispatch":
        return resolve_dispatch_mapping(document, type_mapping, reasons)

    reasons.append(f"document_type={document.document_type}")
    reasons.append(f"mapping_{type_mapping.target_module}")
    return (
        type_mapping.target_module,
        type_mapping.suggested_business_type,
        type_mapping.module_kind,
        type_mapping.confidence_base,
    )


def resolve_dispatch_mapping(
    document: Document,
    type_mapping: DocumentTypeMapping,
    reasons: list[str],
) -> tuple[str, str, str | None, float]:
    reasons.append(f"document_type={document.document_type}")

    if type_mapping.suggested_business_type and type_mapping.module_kind:
        reasons.append("mapping_dispatch_fixed")
        return (
            "dispatch",
            type_mapping.suggested_business_type,
            type_mapping.module_kind,
            type_mapping.confidence_base,
        )

    business_type, dispatch_type, direction_reasons, confidence_cap = infer_dispatch_direction(document)
    reasons.extend(direction_reasons)
    confidence_base = min(type_mapping.confidence_base, confidence_cap)
    return "dispatch", business_type, dispatch_type, confidence_base


def infer_dispatch_direction(document: Document) -> tuple[str, str, list[str], float]:
    reasons: list[str] = []
    excerpt = (document.excerpt or "").strip()
    recipient = (document.recipient or "").strip()

    if re.search(r"(?i)^V/v\s", excerpt):
        reasons.append("dispatch_excerpt_vv")
        return "outgoing_dispatch", "outgoing", reasons, 0.90

    if (document.document_type or "") == "CĐ":
        reasons.append("dispatch_cong_dien")
        return "incoming_dispatch", "incoming", reasons, 0.90

    if re.search(r"(?i)kính\s+gửi", excerpt):
        reasons.append("dispatch_excerpt_kinh_gui")
        return "incoming_dispatch", "incoming", reasons, 0.90

    if recipient:
        reasons.append("dispatch_recipient_incoming")
        return "incoming_dispatch", "incoming", reasons, 0.86

    reasons.append("dispatch_direction_ambiguous")
    return "incoming_dispatch", "incoming", reasons, 0.75


def build_suggested_module_fields(
    *,
    target_module: str,
    document: Document,
    module_kind: str | None,
) -> dict[str, Any]:
    builders = {
        "contract": _contract_fields,
        "dispatch": _dispatch_fields,
        "decision": _decision_fields,
        "procurement": _procurement_fields,
    }
    builder = builders.get(target_module)
    if builder is None:
        return {}
    return builder(document, module_kind)


def _contract_fields(document: Document, _module_kind: str | None) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "currency": "VND",
        "status": "draft",
    }
    _set_if_value(fields, "contract_number", document.document_number or document.document_symbol)
    _set_if_value(fields, "contract_title", document.excerpt or document.title)
    _set_date(fields, "sign_date", document.issued_date)
    return fields


def _dispatch_fields(document: Document, module_kind: str | None) -> dict[str, Any]:
    fields: dict[str, Any] = {"status": "draft"}
    if module_kind in {"incoming", "outgoing"}:
        fields["dispatch_type"] = module_kind
    _set_if_value(fields, "document_number", document.document_number)
    _set_if_value(fields, "document_symbol", document.document_symbol)
    _set_date(fields, "issued_date", document.issued_date)
    _set_if_value(fields, "issuing_agency", document.issuing_agency)
    _set_if_value(fields, "recipient", document.recipient)
    _set_if_value(fields, "excerpt", document.excerpt)
    return fields


def _decision_fields(document: Document, module_kind: str | None) -> dict[str, Any]:
    fields: dict[str, Any] = {"status": "draft"}
    if module_kind in {"decision", "notification"}:
        fields["decision_kind"] = module_kind
    _set_if_value(fields, "document_number", document.document_number)
    _set_if_value(fields, "document_symbol", document.document_symbol)
    _set_date(fields, "issued_date", document.issued_date)
    _set_if_value(fields, "issuing_agency", document.issuing_agency)
    _set_if_value(fields, "excerpt", document.excerpt)
    _set_date(fields, "effective_from", document.issued_date)
    return fields


def _procurement_fields(document: Document, module_kind: str | None) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "currency": "VND",
        "status": "draft",
    }
    if module_kind in {"proposal", "plan", "acceptance"}:
        fields["procurement_kind"] = module_kind
    _set_if_value(fields, "reference_number", document.document_number)
    _set_if_value(fields, "title_summary", document.excerpt or document.title)
    _set_if_value(fields, "requesting_unit", document.issuing_agency)
    _set_date(fields, "requested_date", document.issued_date)
    return fields


def compute_module_confidence(confidence_base: float, classification_confidence: float | None) -> float:
    if classification_confidence is None:
        return round(confidence_base, 4)
    return round(min(confidence_base, classification_confidence), 4)


def _module_kind_from_business_type(
    business_type: str,
    type_mapping: DocumentTypeMapping | None,
) -> str | None:
    if business_type in BUSINESS_TYPE_TO_DISPATCH_TYPE:
        return BUSINESS_TYPE_TO_DISPATCH_TYPE[business_type]
    if type_mapping and type_mapping.module_kind:
        return type_mapping.module_kind
    return None


def _module_exists(db: Session, target_module: str, document_id: str) -> bool:
    repositories = {
        "contract": ContractRepository,
        "dispatch": DispatchRepository,
        "decision": DecisionRepository,
        "procurement": ProcurementRepository,
    }
    repository_cls = repositories.get(target_module)
    if repository_cls is None:
        return False
    return repository_cls(db).get_active_by_document_id(document_id) is not None


def _has_manual_metadata_guard(document: Document) -> bool:
    return document.metadata_reviewed_at is not None or document.metadata_source in {"manual", "mixed"}


def is_upload_business_type_unset(document: Document) -> bool:
    return _normalize_business_type(document.business_type) is None


def build_worker_onboarding_audit_metadata(
    document: Document,
    *,
    db: Session | None = None,
    upload_business_type_unset: bool,
) -> dict[str, Any] | None:
    if not upload_business_type_unset:
        return None

    suggestion = build_onboarding_suggestion(
        document,
        db=db,
        require_searchable=False,
    )
    if suggestion.get("block_reason") == "manual_metadata":
        return None

    return {
        "applied": False,
        "eligible": suggestion.get("eligible", False),
        "block_reason": suggestion.get("block_reason"),
        "needs_metadata_review": suggestion.get("needs_metadata_review", False),
        "suggested_business_type": suggestion.get("suggested_business_type"),
        "business_type_confidence": suggestion.get("business_type_confidence"),
        "target_module": suggestion.get("target_module"),
        "module_confidence": suggestion.get("module_confidence"),
        "module_kind": suggestion.get("module_kind"),
        "reasons": suggestion.get("reasons", []),
    }


def _normalize_business_type(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def _set_if_value(fields: dict[str, Any], key: str, value: str | None) -> None:
    if value:
        fields[key] = value


def _set_date(fields: dict[str, Any], key: str, value: date | None) -> None:
    if value is not None:
        fields[key] = value.isoformat()
