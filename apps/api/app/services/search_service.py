from datetime import date

from sqlalchemy.orm import Session

from app.repositories.contract_repository import ContractRepository
from app.repositories.decision_repository import DecisionRepository
from app.repositories.dispatch_repository import DispatchRepository
from app.repositories.procurement_repository import ProcurementRepository
from app.repositories.document_repository import DocumentRepository
from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import QdrantService
from app.services.search_rerank_service import SearchRerankService, normalize_search_text


class SearchService:
    def __init__(self, db: Session | None = None) -> None:
        self.db = db
        self.embeddings = EmbeddingService()
        self.qdrant = QdrantService()
        self.rerank = SearchRerankService()

    def semantic_search(
        self,
        *,
        query: str,
        limit: int,
        document_type: str | None = None,
        department_id: str | None = None,
        business_type: str | None = None,
        document_number: str | None = None,
        issuing_agency: str | None = None,
        issued_date: date | None = None,
        doc_group: str | None = None,
        section_role: str | None = None,
        requires_review: bool | None = None,
        contract_number: str | None = None,
        supplier_name: str | None = None,
        contract_status: str | None = None,
        dispatch_type: str | None = None,
        dispatch_status: str | None = None,
        decision_kind: str | None = None,
        decision_status: str | None = None,
        effective_from: date | None = None,
        effective_to: date | None = None,
        procurement_kind: str | None = None,
        procurement_status: str | None = None,
        reference_number: str | None = None,
        requesting_unit: str | None = None,
        procurement_item_name: str | None = None,
        procurement_item_code: str | None = None,
    ) -> list[dict]:
        module_document_ids = self._resolve_module_document_ids(
            contract_number=contract_number,
            supplier_name=supplier_name,
            contract_status=contract_status,
            dispatch_type=dispatch_type,
            dispatch_status=dispatch_status,
            decision_kind=decision_kind,
            decision_status=decision_status,
            document_number=document_number,
            issuing_agency=issuing_agency,
            effective_from=effective_from,
            effective_to=effective_to,
            procurement_kind=procurement_kind,
            procurement_status=procurement_status,
            reference_number=reference_number,
            requesting_unit=requesting_unit,
            procurement_item_name=procurement_item_name,
            procurement_item_code=procurement_item_code,
        )
        if module_document_ids is not None and not module_document_ids:
            return []

        vector = self.embeddings.embed(query)
        search_limit = min(max(limit * 8, limit + 20), 100)
        filters = {
            "document_type": document_type,
            "department_id": department_id,
            "business_type": business_type,
            "document_number": document_number,
            "issued_date": issued_date.isoformat() if issued_date else None,
            "doc_group": doc_group,
            "section_role": section_role,
            "requires_review": requires_review,
        }
        hits = self.qdrant.search(
            vector=vector,
            limit=search_limit,
            filters=filters,
        )
        allowed_chunk_ids = self._matching_chunk_ids(
            hits=hits,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issuing_agency=issuing_agency,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
            document_ids=module_document_ids,
        )
        candidates = []
        for hit in hits:
            payload = hit.payload or {}
            chunk_id = str(payload.get("chunk_id") or "")
            document_id = str(payload.get("document_id") or "")
            if module_document_ids is not None and document_id not in module_document_ids:
                continue
            if allowed_chunk_ids is not None and chunk_id not in allowed_chunk_ids:
                continue
            text = payload.get("text", "")
            candidate = {
                "document_id": document_id,
                "chunk_id": chunk_id,
                "score": hit.score,
                "text": text,
                "title": payload.get("title"),
                "document_type": payload.get("document_type"),
                "document_number": payload.get("document_number"),
                "issued_date": payload.get("issued_date"),
                "issuing_agency": payload.get("issuing_agency"),
                "business_type": payload.get("business_type"),
                "page_from": payload.get("page_from"),
                "page_to": payload.get("page_to"),
                "doc_group": payload.get("doc_group"),
                "section_role": payload.get("section_role"),
                "section_path": payload.get("section_path") or [],
                "requires_review": bool(payload.get("requires_review", False)),
                "_vector_score": float(hit.score),
                "_keyword_score": self.rerank.keyword_score(query, text, str(payload.get("title") or "")),
                "_dedup_key": self._dedup_key(payload),
            }
            candidate["_rerank_score"] = self.rerank.score(
                query,
                text,
                vector_score=candidate["_vector_score"],
                keyword_score=candidate["_keyword_score"],
            )
            candidates.append(candidate)

        candidates_by_chunk_id = {str(candidate["chunk_id"]): candidate for candidate in candidates}
        for candidate in self._keyword_candidates(
            query=query,
            limit=search_limit,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issuing_agency=issuing_agency,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
            document_ids=module_document_ids,
        ):
            existing = candidates_by_chunk_id.get(str(candidate["chunk_id"]))
            if existing:
                existing["_keyword_score"] = max(existing["_keyword_score"], candidate["_keyword_score"])
                existing["_rerank_score"] = self.rerank.score(
                    query,
                    str(existing.get("text") or ""),
                    vector_score=existing["_vector_score"],
                    keyword_score=existing["_keyword_score"],
                )
                continue
            candidates.append(candidate)
            candidates_by_chunk_id[str(candidate["chunk_id"])] = candidate

        ranked = sorted(candidates, key=lambda item: item["_rerank_score"], reverse=True)
        results = []
        seen_keys: set[str] = set()
        seen_documents: set[str] = set()
        seen_titles: set[str] = set()
        for item in ranked:
            dedup_key = str(item.pop("_dedup_key"))
            rank_score = float(item.pop("_rerank_score", item.get("score") or 0.0))
            item.pop("_vector_score", None)
            item.pop("_keyword_score", None)
            document_id = str(item.get("document_id") or "")
            title_key = self._normalize(str(item.get("title") or ""))
            if dedup_key in seen_keys:
                continue
            if document_id in seen_documents and self.rerank.is_weak_match(query, str(item.get("text") or "")):
                continue
            if title_key in seen_titles and self.rerank.is_weak_match(query, str(item.get("text") or "")):
                continue
            seen_keys.add(dedup_key)
            seen_documents.add(document_id)
            if title_key:
                seen_titles.add(title_key)
            results.append(
                {
                    "document_id": item["document_id"],
                    "chunk_id": item["chunk_id"],
                    "score": round(rank_score, 6),
                    "text": item["text"],
                    "title": item["title"],
                    "document_type": item["document_type"],
                    "document_number": item["document_number"],
                    "issued_date": item["issued_date"],
                    "issuing_agency": item["issuing_agency"],
                    "business_type": item["business_type"],
                    "page_from": item["page_from"],
                    "page_to": item["page_to"],
                    "doc_group": item["doc_group"],
                    "section_role": item["section_role"],
                    "section_path": item["section_path"],
                    "requires_review": item["requires_review"],
                }
            )
            if len(results) >= limit:
                break
        return self._attach_procurement_metadata(
            self._attach_decision_metadata(
                self._attach_dispatch_metadata(
                    self._attach_contract_metadata(results)
                )
            )
        )

    def _resolve_module_document_ids(
        self,
        *,
        contract_number: str | None,
        supplier_name: str | None,
        contract_status: str | None,
        dispatch_type: str | None,
        dispatch_status: str | None,
        decision_kind: str | None,
        decision_status: str | None,
        document_number: str | None,
        issuing_agency: str | None,
        effective_from: date | None,
        effective_to: date | None,
        procurement_kind: str | None,
        procurement_status: str | None,
        reference_number: str | None,
        requesting_unit: str | None,
        procurement_item_name: str | None,
        procurement_item_code: str | None,
    ) -> set[str] | None:
        active_sets: list[set[str]] = []
        for resolved in (
            self._resolve_contract_document_ids(
                contract_number=contract_number,
                supplier_name=supplier_name,
                contract_status=contract_status,
            ),
            self._resolve_dispatch_document_ids(
                dispatch_type=dispatch_type,
                dispatch_status=dispatch_status,
                document_number=document_number,
                issuing_agency=issuing_agency,
            ),
            self._resolve_decision_document_ids(
                decision_kind=decision_kind,
                decision_status=decision_status,
                document_number=document_number,
                issuing_agency=issuing_agency,
                effective_from=effective_from,
                effective_to=effective_to,
            ),
            self._resolve_procurement_document_ids(
                procurement_kind=procurement_kind,
                procurement_status=procurement_status,
                reference_number=reference_number,
                requesting_unit=requesting_unit,
                procurement_item_name=procurement_item_name,
                procurement_item_code=procurement_item_code,
            ),
        ):
            if resolved is None:
                continue
            if not resolved:
                return set()
            active_sets.append(resolved)
        if not active_sets:
            return None
        result = set(active_sets[0])
        for item in active_sets[1:]:
            result &= item
        return result

    def _resolve_contract_document_ids(
        self,
        *,
        contract_number: str | None,
        supplier_name: str | None,
        contract_status: str | None,
    ) -> set[str] | None:
        if self.db is None:
            return None
        if not any([contract_number, supplier_name, contract_status]):
            return None
        document_ids = ContractRepository(self.db).list_document_ids_by_metadata(
            contract_number=contract_number,
            supplier_name=supplier_name,
            status=contract_status,
        )
        return set(document_ids)

    def _resolve_dispatch_document_ids(
        self,
        *,
        dispatch_type: str | None,
        dispatch_status: str | None,
        document_number: str | None,
        issuing_agency: str | None,
    ) -> set[str] | None:
        if self.db is None:
            return None
        if not any([dispatch_type, dispatch_status]):
            return None
        document_ids = DispatchRepository(self.db).list_document_ids_by_metadata(
            dispatch_type=dispatch_type,
            document_number=document_number,
            issuing_agency=issuing_agency,
            status=dispatch_status,
        )
        return set(document_ids)

    def _resolve_decision_document_ids(
        self,
        *,
        decision_kind: str | None,
        decision_status: str | None,
        document_number: str | None,
        issuing_agency: str | None,
        effective_from: date | None,
        effective_to: date | None,
    ) -> set[str] | None:
        if self.db is None:
            return None
        if not any([decision_kind, decision_status, effective_from, effective_to]):
            return None
        document_ids = DecisionRepository(self.db).list_document_ids_by_metadata(
            decision_kind=decision_kind,
            document_number=document_number,
            issuing_agency=issuing_agency,
            status=decision_status,
            effective_from=effective_from,
            effective_to=effective_to,
        )
        return set(document_ids)

    def _resolve_procurement_document_ids(
        self,
        *,
        procurement_kind: str | None,
        procurement_status: str | None,
        reference_number: str | None,
        requesting_unit: str | None,
        procurement_item_name: str | None = None,
        procurement_item_code: str | None = None,
    ) -> set[str] | None:
        if self.db is None:
            return None
        if not any([
            procurement_kind,
            procurement_status,
            reference_number,
            requesting_unit,
            procurement_item_name,
            procurement_item_code,
        ]):
            return None
        document_ids = ProcurementRepository(self.db).list_document_ids_by_metadata(
            procurement_kind=procurement_kind,
            reference_number=reference_number,
            requesting_unit=requesting_unit,
            status=procurement_status,
            item_name=procurement_item_name,
            item_code=procurement_item_code,
        )
        return set(document_ids)

    def _attach_contract_metadata(self, results: list[dict]) -> list[dict]:
        if self.db is None or not results:
            return results
        document_ids = list({str(result.get("document_id") or "") for result in results if result.get("document_id")})
        contracts = ContractRepository(self.db).map_active_by_document_ids(document_ids)
        enriched = []
        for result in results:
            contract = contracts.get(str(result.get("document_id") or ""))
            enriched.append(
                {
                    **result,
                    "contract_id": contract.id if contract else None,
                    "contract_number": contract.contract_number if contract else None,
                    "supplier_name": contract.supplier_name if contract else None,
                    "contract_status": contract.status if contract else None,
                }
            )
        return enriched

    def _attach_dispatch_metadata(self, results: list[dict]) -> list[dict]:
        if self.db is None or not results:
            return results
        document_ids = list({str(result.get("document_id") or "") for result in results if result.get("document_id")})
        dispatches = DispatchRepository(self.db).map_active_by_document_ids(document_ids)
        enriched = []
        for result in results:
            dispatch = dispatches.get(str(result.get("document_id") or ""))
            enriched.append(
                {
                    **result,
                    "dispatch_id": dispatch.id if dispatch else None,
                    "dispatch_type": dispatch.dispatch_type if dispatch else None,
                    "dispatch_status": dispatch.status if dispatch else None,
                }
            )
        return enriched

    def _attach_decision_metadata(self, results: list[dict]) -> list[dict]:
        if self.db is None or not results:
            return results
        document_ids = list({str(result.get("document_id") or "") for result in results if result.get("document_id")})
        decisions = DecisionRepository(self.db).map_active_by_document_ids(document_ids)
        enriched = []
        for result in results:
            decision = decisions.get(str(result.get("document_id") or ""))
            enriched.append(
                {
                    **result,
                    "decision_id": decision.id if decision else None,
                    "decision_kind": decision.decision_kind if decision else None,
                    "decision_status": decision.status if decision else None,
                    "effective_from": decision.effective_from if decision else None,
                    "effective_to": decision.effective_to if decision else None,
                }
            )
        return enriched

    def _attach_procurement_metadata(self, results: list[dict]) -> list[dict]:
        if self.db is None or not results:
            return results
        document_ids = list({str(result.get("document_id") or "") for result in results if result.get("document_id")})
        procurements = ProcurementRepository(self.db).map_active_by_document_ids(document_ids)
        enriched = []
        for result in results:
            procurement = procurements.get(str(result.get("document_id") or ""))
            enriched.append(
                {
                    **result,
                    "procurement_id": procurement.id if procurement else None,
                    "procurement_kind": procurement.procurement_kind if procurement else None,
                    "procurement_status": procurement.status if procurement else None,
                    "reference_number": procurement.reference_number if procurement else None,
                    "requesting_unit": procurement.requesting_unit if procurement else None,
                }
            )
        return enriched

    def _keyword_candidates(
        self,
        *,
        query: str,
        limit: int,
        document_type: str | None,
        department_id: str | None,
        business_type: str | None,
        document_number: str | None,
        issuing_agency: str | None,
        issued_date: date | None,
        doc_group: str | None,
        section_role: str | None,
        requires_review: bool | None,
        document_ids: set[str] | None,
    ) -> list[dict]:
        if self.db is None:
            return []

        chunks = DocumentRepository(self.db).search_chunks_by_keyword(
            query=query,
            limit=limit,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issuing_agency=issuing_agency,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
            document_ids=document_ids,
        )
        candidates = []
        for chunk in chunks:
            document = chunk.document
            keyword_score = self.rerank.keyword_score(query, chunk.text, document.title)
            candidate = {
                "document_id": document.id,
                "chunk_id": chunk.id,
                "score": keyword_score,
                "text": chunk.text,
                "title": document.title,
                "document_type": document.document_type,
                "document_number": document.document_number,
                "issued_date": document.issued_date,
                "issuing_agency": document.issuing_agency,
                "business_type": document.business_type,
                "page_from": chunk.page_from,
                "page_to": chunk.page_to,
                "doc_group": chunk.doc_group,
                "section_role": chunk.section_role,
                "section_path": chunk.section_path or [],
                "requires_review": chunk.requires_review,
                "_vector_score": 0.0,
                "_keyword_score": keyword_score,
                "_dedup_key": chunk.content_hash or self._dedup_key(
                    {
                        "title": document.title,
                        "page_from": chunk.page_from,
                        "page_to": chunk.page_to,
                        "text": chunk.text,
                    }
                ),
            }
            candidate["_rerank_score"] = self.rerank.score(
                query,
                chunk.text,
                vector_score=0.0,
                keyword_score=keyword_score,
            )
            candidates.append(candidate)
        return candidates

    def _matching_chunk_ids(
        self,
        *,
        hits: list,
        document_type: str | None,
        department_id: str | None,
        business_type: str | None,
        document_number: str | None,
        issuing_agency: str | None,
        issued_date: date | None,
        doc_group: str | None,
        section_role: str | None,
        requires_review: bool | None,
        document_ids: set[str] | None,
    ) -> set[str] | None:
        if self.db is None:
            return None
        chunk_ids = [str((hit.payload or {}).get("chunk_id") or "") for hit in hits]
        chunk_ids = [chunk_id for chunk_id in chunk_ids if chunk_id]
        return DocumentRepository(self.db).list_matching_chunk_ids(
            chunk_ids=chunk_ids,
            document_type=document_type,
            department_id=department_id,
            business_type=business_type,
            document_number=document_number,
            issuing_agency=issuing_agency,
            issued_date=issued_date,
            doc_group=doc_group,
            section_role=section_role,
            requires_review=requires_review,
            document_ids=document_ids,
        )

    def _dedup_key(self, payload: dict) -> str:
        content_hash = payload.get("content_hash")
        if content_hash:
            return str(content_hash)
        title = str(payload.get("title") or "")
        page_from = payload.get("page_from")
        page_to = payload.get("page_to")
        text = str(payload.get("text") or "")
        normalized_text = self._normalize(text)[:320]
        return f"{self._normalize(title)}:{page_from}:{page_to}:{normalized_text}"

    def _normalize(self, text: str) -> str:
        return normalize_search_text(text)
