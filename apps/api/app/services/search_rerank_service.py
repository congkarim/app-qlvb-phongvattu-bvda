from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class PhraseBoostRule:
    query_phrase: str
    text_phrase: str
    boost: float


@dataclass(frozen=True)
class PrefixBoostRule:
    query_phrase: str
    text_prefix: str
    boost: float


@dataclass(frozen=True)
class MissingPhrasePenaltyRule:
    query_phrase: str
    required_text_phrase: str
    penalty: float


@dataclass(frozen=True)
class SearchRerankConfig:
    term_match_boost: float = 0.05
    term_coverage_boost: float = 0.12
    phrase_boosts: tuple[PhraseBoostRule, ...] = (
        PhraseBoostRule("dieu 1", "dieu 1", 0.25),
        PhraseBoostRule("pham vi dieu chinh", "pham vi dieu chinh", 0.3),
        PhraseBoostRule("luat dau thau", "luat dau thau", 0.25),
        PhraseBoostRule("pham vi dieu chinh", "dieu 1", 0.2),
        PhraseBoostRule("luat dau thau", "dau thau", 0.12),
    )
    prefix_boosts: tuple[PrefixBoostRule, ...] = (
        PrefixBoostRule("pham vi dieu chinh", "dieu 1", 0.55),
        PrefixBoostRule("luat dau thau", "dieu 1", 0.2),
    )
    missing_phrase_penalties: tuple[MissingPhrasePenaltyRule, ...] = (
        MissingPhrasePenaltyRule("pham vi dieu chinh", "pham vi dieu chinh", 0.18),
    )
    keyword_phrase_candidates: tuple[str, ...] = (
        "pham vi dieu chinh",
        "nguoi lien he",
        "so hieu",
        "kinh gui",
        "che do phu cap",
        "ho tro hang thang",
        "nhan vien y te thon",
        "co do thon ban",
    )


class SearchRerankService:
    def __init__(self, config: SearchRerankConfig | None = None) -> None:
        self.config = config or SearchRerankConfig()

    def score(self, query: str, text: str, *, vector_score: float, keyword_score: float) -> float:
        query_norm = normalize_search_text(query)
        text_norm = normalize_search_text(text)
        score = float(vector_score) + keyword_score

        query_terms = [term for term in re.findall(r"\w+", query_norm) if len(term) >= 3]
        if query_terms:
            unique_terms = set(query_terms)
            matched_terms = sum(1 for term in unique_terms if term in text_norm)
            score += self.config.term_match_boost * matched_terms
            score += self.config.term_coverage_boost * (matched_terms / len(unique_terms))

        for rule in self.config.phrase_boosts:
            if rule.query_phrase in query_norm and rule.text_phrase in text_norm:
                score += rule.boost

        for rule in self.config.prefix_boosts:
            if rule.query_phrase in query_norm and text_norm.startswith(rule.text_prefix):
                score += rule.boost

        for rule in self.config.missing_phrase_penalties:
            if rule.query_phrase in query_norm and rule.required_text_phrase not in text_norm:
                score -= rule.penalty

        return score

    def keyword_score(self, query: str, text: str, title: str = "") -> float:
        query_norm = normalize_search_text(query)
        text_norm = normalize_search_text(text)
        title_norm = normalize_search_text(title)
        query_terms = {term for term in re.findall(r"\w+", query_norm) if len(term) >= 3}
        if not query_terms:
            return 0.0

        matched_terms = sum(1 for term in query_terms if term in text_norm or term in title_norm)
        coverage = matched_terms / len(query_terms)
        score = 0.45 * coverage
        if query_norm and query_norm in text_norm:
            score += 0.75

        for phrase in self.query_phrases(query_norm):
            if phrase in text_norm:
                score += 0.2
        return score

    def query_phrases(self, query_norm: str) -> list[str]:
        return [phrase for phrase in self.config.keyword_phrase_candidates if phrase in query_norm]

    def is_weak_match(self, query: str, text: str) -> bool:
        query_terms = {term for term in re.findall(r"\w+", normalize_search_text(query)) if len(term) >= 4}
        if not query_terms:
            return False
        text_norm = normalize_search_text(text)
        matched_terms = sum(1 for term in query_terms if term in text_norm)
        return matched_terms < max(2, len(query_terms) // 2)


def normalize_search_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", without_accents.replace("đ", "d")).strip()
