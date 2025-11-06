"""
CrewAI Tools

This module contains all tool implementations for the Paper Finder CrewAI agents.

Tool Categories:
1. Semantic Scholar Tools: s2_search_by_title, s2_search_by_author, etc.
2. Dense Retrieval Tools: dense_search_bifroest, reformulate_search_query (TODO)
3. Document Processing Tools: filter_papers, sort_papers, combine_papers, etc.
4. Metadata Tools: extract_query_metadata, identify_query_type (TODO)
5. LLM Tools: llm_suggest_papers (TODO)

All tools are decorated with @tool and use ai2i libraries for implementation.

See DESIGN.md for complete tool specifications.
"""

# Semantic Scholar Tools
from paperfinder_crew.tools.semantic_scholar import (
    s2_search_by_title,
    s2_search_by_author,
    s2_get_paper_details,
    s2_search_query,
    s2_get_citations,
    s2_get_references,
)

# Document Processing Tools
from paperfinder_crew.tools.document_processing import (
    filter_papers,
    deduplicate_papers,
    sort_papers,
    take_top_papers,
    combine_papers,
    extract_corpus_ids,
    count_papers,
    get_paper_statistics,
)

# Export all tools
__all__ = [
    # Semantic Scholar Tools
    "s2_search_by_title",
    "s2_search_by_author",
    "s2_get_paper_details",
    "s2_search_query",
    "s2_get_citations",
    "s2_get_references",
    # Document Processing Tools
    "filter_papers",
    "deduplicate_papers",
    "sort_papers",
    "take_top_papers",
    "combine_papers",
    "extract_corpus_ids",
    "count_papers",
    "get_paper_statistics",
]
