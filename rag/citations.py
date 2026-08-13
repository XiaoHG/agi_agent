"""Citation validation helpers for grounded RAG answers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CitationValidationResult:
    """Validation result for answer/source citation alignment."""

    valid: bool                                     # citation 是否通过校验
    cited_sources: tuple[str, ...] = ()             # 答案中实际引用的来源
    missing_sources: tuple[str, ...] = ()           # 检索到但未在答案中提及的来源
    unsupported_citations: tuple[str, ...] = ()     # 答案里提到但不在 sources 中的来源
    reason: str = ""                                # 总体校验结论

    def to_dict(self) -> dict[str, object]:
        """Render the validation result as JSON-ready data."""

        return {
            "valid": self.valid,
            "cited_sources": list(self.cited_sources),
            "missing_sources": list(self.missing_sources),
            "unsupported_citations": list(self.unsupported_citations),
            "reason": self.reason,
        }


def validate_answer_citations(answer: str, sources: list[str]) -> CitationValidationResult:
    """Validate that the answer cites only retrieved sources."""

    normalized_sources = tuple(dict.fromkeys(source.strip() for source in sources if source.strip()))
    cited_sources = tuple(source for source in normalized_sources if source in answer)
    missing_sources = tuple(source for source in normalized_sources if source not in answer)
    unsupported = _extract_unsupported_citations(answer, normalized_sources)

    if unsupported:
        return CitationValidationResult(
            valid=False,
            cited_sources=cited_sources,
            missing_sources=missing_sources,
            unsupported_citations=unsupported,
            reason=f"Answer cited unsupported source(s): {', '.join(unsupported)}",
        )
    if normalized_sources and not cited_sources:
        return CitationValidationResult(
            valid=False,
            cited_sources=(),
            missing_sources=missing_sources,
            unsupported_citations=(),
            reason="Answer did not cite any retrieved source label.",
        )
    if missing_sources:
        return CitationValidationResult(
            valid=True,
            cited_sources=cited_sources,
            missing_sources=missing_sources,
            unsupported_citations=(),
            reason="Answer cited at least one retrieved source, but not all retrieved sources were mentioned.",
        )
    return CitationValidationResult(
        valid=True,
        cited_sources=cited_sources,
        missing_sources=(),
        unsupported_citations=(),
        reason="Answer citations match the retrieved source set.",
    )


def _extract_unsupported_citations(answer: str, sources: tuple[str, ...]) -> tuple[str, ...]:
    """Collect source-like labels that appear in the answer but not in retrieval sources."""

    unsupported: list[str] = []
    for token in answer.split():
        normalized = token.strip(".,:;()[]{}")
        if ".md:" not in normalized and "docs/" not in normalized and "versions/" not in normalized:
            continue
        if ":" not in normalized:
            continue
        if normalized not in sources and normalized not in unsupported:
            unsupported.append(normalized)
    return tuple(unsupported)
