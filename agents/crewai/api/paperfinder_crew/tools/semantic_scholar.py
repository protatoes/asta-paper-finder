"""
Semantic Scholar Tools

CrewAI tools for searching and retrieving papers from Semantic Scholar.
Uses ai2i.dcollection library for the underlying implementation.
"""

import json
import os
from typing import Any

from crewai.tools import tool
from ai2i.dcollection import DocumentCollectionFactory, DocumentCollection


# Initialize factory - will be reused across tool calls
def _get_factory() -> DocumentCollectionFactory:
    """Get DocumentCollectionFactory with API key from environment."""
    s2_api_key = os.getenv("S2_API_KEY", "")
    return DocumentCollectionFactory(
        s2_api_key=s2_api_key,
        s2_api_timeout=30,
        cache_ttl=3600,
        cache_is_enabled=True,
    )


def _docs_to_json(docs: DocumentCollection) -> str:
    """Convert DocumentCollection to JSON string for CrewAI tools."""
    # Extract basic fields for each document
    papers = []
    for doc in docs.documents:
        paper_dict = {
            "corpus_id": doc.corpus_id if hasattr(doc, "corpus_id") else None,
            "title": doc.title if hasattr(doc, "title") else None,
            "authors": [str(a) for a in (doc.authors or [])] if hasattr(doc, "authors") else [],
            "year": doc.year if hasattr(doc, "year") else None,
            "abstract": doc.abstract if hasattr(doc, "abstract") else None,
            "citation_count": doc.citation_count if hasattr(doc, "citation_count") else None,
            "venue": doc.venue if hasattr(doc, "venue") else None,
        }
        papers.append(paper_dict)

    return json.dumps(papers, indent=2)


@tool("Search Semantic Scholar by paper title")
async def s2_search_by_title(title: str, year_range: str | None = None, limit: int = 10) -> str:
    """
    Search for papers on Semantic Scholar by title.

    This tool searches for academic papers using title keywords. It's best used when
    you have a specific paper title or part of a title you're looking for.

    Args:
        title: The paper title or title keywords to search for (e.g., "attention is all you need")
        year_range: Optional year range in format "start-end" (e.g., "2017-2023").
                    If not provided, searches all years.
        limit: Maximum number of results to return (default: 10, max recommended: 100)

    Returns:
        JSON string containing list of papers with fields:
        - corpus_id: Semantic Scholar unique ID
        - title: Paper title
        - authors: List of author names
        - year: Publication year
        - abstract: Paper abstract
        - citation_count: Number of citations
        - venue: Publication venue

    Example:
        >>> result = await s2_search_by_title("transformer neural networks", year_range="2017-2020", limit=5)
        >>> papers = json.loads(result)
        >>> print(f"Found {len(papers)} papers")
    """
    factory = _get_factory()

    # Parse year range if provided
    time_range = None
    if year_range:
        try:
            start, end = year_range.split("-")
            time_range = {"start_year": int(start), "end_year": int(end)}
        except (ValueError, AttributeError):
            pass  # Invalid format, ignore

    # Search using DocumentCollectionFactory
    docs = await factory.from_s2_by_title(
        query=title,
        time_range=time_range,
        limit=limit
    )

    # Load basic fields
    docs = await docs.with_fields(["title", "authors", "year", "abstract", "citation_count", "venue"])

    return _docs_to_json(docs)


@tool("Search Semantic Scholar by author names")
async def s2_search_by_author(author_names: str, limit: int = 50) -> str:
    """
    Search for papers by one or more authors on Semantic Scholar.

    This tool finds papers authored by specific researchers. Provide author names
    as they commonly appear in publications.

    Args:
        author_names: Comma-separated list of author names (e.g., "Yoshua Bengio, Ian Goodfellow")
        limit: Maximum number of results per author (default: 50, max recommended: 100)

    Returns:
        JSON string containing list of papers by these authors with fields:
        - corpus_id, title, authors, year, abstract, citation_count, venue

    Example:
        >>> result = await s2_search_by_author("Geoffrey Hinton", limit=20)
        >>> papers = json.loads(result)
        >>> print(f"{papers[0]['title']} ({papers[0]['year']})")

    Note:
        The tool attempts to disambiguate authors automatically. If multiple
        researchers share the same name, results may include papers from different individuals.
    """
    factory = _get_factory()

    # Parse author names
    authors = [name.strip() for name in author_names.split(",")]

    # Search using DocumentCollectionFactory
    docs = await factory.from_s2_by_author(
        authors=authors,
        limit=limit
    )

    # Load basic fields
    docs = await docs.with_fields(["title", "authors", "year", "abstract", "citation_count", "venue"])

    return _docs_to_json(docs)


@tool("Get detailed paper information from Semantic Scholar")
async def s2_get_paper_details(corpus_ids: str) -> str:
    """
    Retrieve complete information for specific papers by their Semantic Scholar IDs.

    Use this tool when you have specific paper IDs and need detailed information
    including abstracts, citations, references, and full metadata.

    Args:
        corpus_ids: Comma-separated list of Semantic Scholar corpus IDs
                    (e.g., "204e3073870fae3d05bcbc2f6a8e263d9b72e776,e33b74fla2ba4a61922e8ba1b5f79b7e8ea4b7c3")

    Returns:
        JSON string containing detailed paper information with fields:
        - corpus_id, title, authors, year, abstract, citation_count, venue
        - reference_count: Number of papers this paper cites
        - fields_of_study: Research areas/domains

    Example:
        >>> result = await s2_get_paper_details("204e3073870fae3d05bcbc2f6a8e263d9b72e776")
        >>> papers = json.loads(result)
        >>> print(f"Title: {papers[0]['title']}")
        >>> print(f"Citations: {papers[0]['citation_count']}")
    """
    factory = _get_factory()

    # Parse corpus IDs
    ids = [id.strip() for id in corpus_ids.split(",")]

    # Get documents by IDs
    docs = await factory.from_ids(corpus_ids=ids)

    # Load detailed fields
    docs = await docs.with_fields([
        "title", "authors", "year", "abstract",
        "citation_count", "reference_count", "venue",
        "fields_of_study"
    ])

    # Convert to JSON with additional fields
    papers = []
    for doc in docs.documents:
        paper_dict = {
            "corpus_id": doc.corpus_id if hasattr(doc, "corpus_id") else None,
            "title": doc.title if hasattr(doc, "title") else None,
            "authors": [str(a) for a in (doc.authors or [])] if hasattr(doc, "authors") else [],
            "year": doc.year if hasattr(doc, "year") else None,
            "abstract": doc.abstract if hasattr(doc, "abstract") else None,
            "citation_count": doc.citation_count if hasattr(doc, "citation_count") else None,
            "reference_count": doc.reference_count if hasattr(doc, "reference_count") else None,
            "venue": doc.venue if hasattr(doc, "venue") else None,
            "fields_of_study": doc.fields_of_study if hasattr(doc, "fields_of_study") else [],
        }
        papers.append(paper_dict)

    return json.dumps(papers, indent=2)


@tool("General search on Semantic Scholar")
async def s2_search_query(
    query: str,
    fields_of_study: str | None = None,
    year_range: str | None = None,
    venues: str | None = None,
    limit: int = 100
) -> str:
    """
    Perform a general search query on Semantic Scholar with filtering options.

    This is the most flexible search tool, allowing you to combine keyword search
    with filters for research fields, publication years, and venues.

    Args:
        query: Natural language search query (e.g., "neural machine translation with attention")
        fields_of_study: Optional comma-separated list of research fields
                        (e.g., "Computer Science,Mathematics,Physics")
        year_range: Optional year range in format "start-end" (e.g., "2015-2023")
        venues: Optional comma-separated list of publication venues
                (e.g., "ACL,EMNLP,NAACL,NeurIPS")
        limit: Maximum results (default: 100, max recommended: 500)

    Returns:
        JSON string containing matching papers with standard fields

    Example:
        >>> result = await s2_search_query(
        ...     query="large language models",
        ...     fields_of_study="Computer Science",
        ...     year_range="2020-2023",
        ...     venues="NeurIPS,ICML",
        ...     limit=50
        ... )
        >>> papers = json.loads(result)

    Note:
        This tool is best for broad exploratory searches. For specific papers
        or authors, use s2_search_by_title or s2_search_by_author instead.
    """
    factory = _get_factory()

    # Parse filters
    time_range = None
    if year_range:
        try:
            start, end = year_range.split("-")
            time_range = {"start_year": int(start), "end_year": int(end)}
        except (ValueError, AttributeError):
            pass

    fos_list = None
    if fields_of_study:
        fos_list = [f.strip() for f in fields_of_study.split(",")]

    venue_list = None
    if venues:
        venue_list = [v.strip() for v in venues.split(",")]

    # Search using DocumentCollectionFactory
    docs = await factory.from_s2_search(
        query=query,
        fields_of_study=fos_list,
        time_range=time_range,
        venues=venue_list,
        limit=limit
    )

    # Load basic fields
    docs = await docs.with_fields(["title", "authors", "year", "abstract", "citation_count", "venue"])

    return _docs_to_json(docs)


@tool("Get papers citing a specific paper")
async def s2_get_citations(corpus_id: str, limit: int = 100) -> str:
    """
    Get papers that cite a specific paper on Semantic Scholar.

    Use this tool to find papers that reference/cite a given paper. Useful for
    forward citation search and finding related recent work.

    Args:
        corpus_id: Semantic Scholar corpus ID of the paper
        limit: Maximum number of citing papers to return (default: 100)

    Returns:
        JSON string containing papers that cite the given paper

    Example:
        >>> result = await s2_get_citations("204e3073870fae3d05bcbc2f6a8e263d9b72e776", limit=50)
        >>> citing_papers = json.loads(result)
        >>> print(f"Found {len(citing_papers)} papers citing this work")
    """
    factory = _get_factory()

    # Get the paper first
    docs = await factory.from_ids(corpus_ids=[corpus_id])

    if len(docs.documents) == 0:
        return json.dumps([])

    # Get citations using the citations field
    docs = await docs.with_fields(["citations"])

    paper = docs.documents[0]
    if not hasattr(paper, "citations") or not paper.citations:
        return json.dumps([])

    # Get details for citing papers (limited by limit parameter)
    citing_ids = [c.corpus_id for c in paper.citations[:limit] if hasattr(c, "corpus_id")]

    if not citing_ids:
        return json.dumps([])

    citing_docs = await factory.from_ids(corpus_ids=citing_ids)
    citing_docs = await citing_docs.with_fields(["title", "authors", "year", "abstract", "citation_count", "venue"])

    return _docs_to_json(citing_docs)


@tool("Get papers referenced by a specific paper")
async def s2_get_references(corpus_id: str, limit: int = 100) -> str:
    """
    Get papers referenced/cited by a specific paper on Semantic Scholar.

    Use this tool for backward citation search to find the papers that a given
    paper builds upon.

    Args:
        corpus_id: Semantic Scholar corpus ID of the paper
        limit: Maximum number of referenced papers to return (default: 100)

    Returns:
        JSON string containing papers referenced by the given paper

    Example:
        >>> result = await s2_get_references("204e3073870fae3d05bcbc2f6a8e263d9b72e776", limit=50)
        >>> references = json.loads(result)
        >>> print(f"This paper cites {len(references)} papers")
    """
    factory = _get_factory()

    # Get the paper first
    docs = await factory.from_ids(corpus_ids=[corpus_id])

    if len(docs.documents) == 0:
        return json.dumps([])

    # Get references using the references field
    docs = await docs.with_fields(["references"])

    paper = docs.documents[0]
    if not hasattr(paper, "references") or not paper.references:
        return json.dumps([])

    # Get details for referenced papers (limited by limit parameter)
    ref_ids = [r.corpus_id for r in paper.references[:limit] if hasattr(r, "corpus_id")]

    if not ref_ids:
        return json.dumps([])

    ref_docs = await factory.from_ids(corpus_ids=ref_ids)
    ref_docs = await ref_docs.with_fields(["title", "authors", "year", "abstract", "citation_count", "venue"])

    return _docs_to_json(ref_docs)
