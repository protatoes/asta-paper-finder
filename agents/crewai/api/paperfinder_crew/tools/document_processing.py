"""
Document Processing Tools

CrewAI tools for filtering, judging relevance, ranking, and processing papers.
"""

import json
from typing import Any

from crewai.tools import tool


@tool("Filter papers by metadata criteria")
def filter_papers(
    papers_json: str,
    year_range: str | None = None,
    venues: str | None = None,
    min_citation_count: int | None = None,
    authors: str | None = None
) -> str:
    """
    Filter papers based on metadata criteria.

    Use this tool to narrow down a set of papers based on publication year,
    venue, citation count, or author criteria.

    Args:
        papers_json: JSON string of papers to filter (output from S2 tools)
        year_range: Optional year range in format "start-end" (e.g., "2018-2023")
        venues: Optional comma-separated list of venues to include (e.g., "ACL,EMNLP,NAACL")
        min_citation_count: Optional minimum citation count threshold
        authors: Optional comma-separated list of authors (paper must have at least one)

    Returns:
        JSON string of filtered papers

    Example:
        >>> filtered = filter_papers(
        ...     papers_json=all_papers,
        ...     year_range="2020-2023",
        ...     min_citation_count=10,
        ...     venues="NeurIPS,ICML"
        ... )
    """
    try:
        papers = json.loads(papers_json)
    except json.JSONDecodeError:
        return json.dumps([])

    filtered = papers

    # Filter by year range
    if year_range:
        try:
            start, end = year_range.split("-")
            start_year, end_year = int(start), int(end)
            filtered = [
                p for p in filtered
                if p.get("year") and start_year <= p["year"] <= end_year
            ]
        except (ValueError, AttributeError):
            pass  # Invalid format, skip filter

    # Filter by venues
    if venues:
        venue_list = [v.strip().lower() for v in venues.split(",")]
        filtered = [
            p for p in filtered
            if p.get("venue") and p["venue"].lower() in venue_list
        ]

    # Filter by minimum citation count
    if min_citation_count is not None:
        filtered = [
            p for p in filtered
            if p.get("citation_count", 0) >= min_citation_count
        ]

    # Filter by authors
    if authors:
        author_list = [a.strip().lower() for a in authors.split(",")]
        filtered = [
            p for p in filtered
            if any(
                author.lower() in author_list
                for author in p.get("authors", [])
            )
        ]

    return json.dumps(filtered, indent=2)


@tool("Remove duplicate papers")
def deduplicate_papers(papers_json: str) -> str:
    """
    Remove duplicate papers from a list based on corpus_id.

    Use this tool when combining results from multiple searches to ensure
    each paper appears only once.

    Args:
        papers_json: JSON string of papers that may contain duplicates

    Returns:
        JSON string of deduplicated papers (first occurrence kept)

    Example:
        >>> unique_papers = deduplicate_papers(combined_results)
    """
    try:
        papers = json.loads(papers_json)
    except json.JSONDecodeError:
        return json.dumps([])

    seen_ids = set()
    unique_papers = []

    for paper in papers:
        corpus_id = paper.get("corpus_id")
        if corpus_id and corpus_id not in seen_ids:
            seen_ids.add(corpus_id)
            unique_papers.append(paper)
        elif not corpus_id:
            # Keep papers without corpus_id
            unique_papers.append(paper)

    return json.dumps(unique_papers, indent=2)


@tool("Sort papers by criteria")
def sort_papers(papers_json: str, sort_by: str = "citation_count", descending: bool = True) -> str:
    """
    Sort papers by a specified criterion.

    Args:
        papers_json: JSON string of papers to sort
        sort_by: Field to sort by. Options: "citation_count", "year", "title"
                 Default: "citation_count"
        descending: If True, sort in descending order (highest first).
                   If False, ascending order. Default: True

    Returns:
        JSON string of sorted papers

    Example:
        >>> # Sort by citations (most cited first)
        >>> sorted_papers = sort_papers(papers_json, sort_by="citation_count", descending=True)

        >>> # Sort by year (oldest first)
        >>> sorted_papers = sort_papers(papers_json, sort_by="year", descending=False)
    """
    try:
        papers = json.loads(papers_json)
    except json.JSONDecodeError:
        return json.dumps([])

    # Define sort key function
    def get_sort_key(paper: dict) -> Any:
        value = paper.get(sort_by)
        # Handle None values - put them at the end
        if value is None:
            return float("-inf") if descending else float("inf")
        return value

    sorted_papers = sorted(papers, key=get_sort_key, reverse=descending)

    return json.dumps(sorted_papers, indent=2)


@tool("Take top N papers from a list")
def take_top_papers(papers_json: str, n: int = 10) -> str:
    """
    Take the first N papers from a list.

    Use this tool to limit results to a specific number, typically after
    sorting or ranking.

    Args:
        papers_json: JSON string of papers
        n: Number of papers to return (default: 10)

    Returns:
        JSON string of top N papers

    Example:
        >>> top_10 = take_top_papers(sorted_papers, n=10)
    """
    try:
        papers = json.loads(papers_json)
    except json.JSONDecodeError:
        return json.dumps([])

    return json.dumps(papers[:n], indent=2)


@tool("Combine multiple paper lists")
def combine_papers(papers_json_1: str, papers_json_2: str, deduplicate: bool = True) -> str:
    """
    Combine two lists of papers into one.

    Use this tool to merge results from different searches or tools.

    Args:
        papers_json_1: First JSON string of papers
        papers_json_2: Second JSON string of papers
        deduplicate: If True, remove duplicates based on corpus_id (default: True)

    Returns:
        JSON string of combined papers

    Example:
        >>> all_papers = combine_papers(title_results, author_results, deduplicate=True)
    """
    try:
        papers1 = json.loads(papers_json_1)
        papers2 = json.loads(papers_json_2)
    except json.JSONDecodeError:
        return json.dumps([])

    combined = papers1 + papers2

    if deduplicate:
        seen_ids = set()
        unique_papers = []
        for paper in combined:
            corpus_id = paper.get("corpus_id")
            if corpus_id and corpus_id not in seen_ids:
                seen_ids.add(corpus_id)
                unique_papers.append(paper)
            elif not corpus_id:
                unique_papers.append(paper)
        combined = unique_papers

    return json.dumps(combined, indent=2)


@tool("Extract corpus IDs from papers")
def extract_corpus_ids(papers_json: str) -> str:
    """
    Extract a comma-separated list of corpus IDs from papers.

    Useful for passing paper IDs to other tools that require corpus_id input.

    Args:
        papers_json: JSON string of papers

    Returns:
        Comma-separated string of corpus IDs (e.g., "id1,id2,id3")

    Example:
        >>> ids = extract_corpus_ids(papers_json)
        >>> details = await s2_get_paper_details(ids)
    """
    try:
        papers = json.loads(papers_json)
    except json.JSONDecodeError:
        return ""

    corpus_ids = [
        paper["corpus_id"]
        for paper in papers
        if paper.get("corpus_id")
    ]

    return ",".join(corpus_ids)


@tool("Count papers in a list")
def count_papers(papers_json: str) -> str:
    """
    Count the number of papers in a list.

    Args:
        papers_json: JSON string of papers

    Returns:
        String containing the count

    Example:
        >>> count = count_papers(filtered_papers)
        >>> print(f"Found {count} papers matching criteria")
    """
    try:
        papers = json.loads(papers_json)
        return str(len(papers))
    except json.JSONDecodeError:
        return "0"


@tool("Get paper statistics")
def get_paper_statistics(papers_json: str) -> str:
    """
    Calculate statistics about a list of papers.

    Provides useful summary information including year range, average citations,
    venue distribution, and author counts.

    Args:
        papers_json: JSON string of papers

    Returns:
        JSON string containing statistics:
        - total_count: Number of papers
        - year_range: Earliest and latest publication years
        - avg_citations: Average citation count
        - total_citations: Sum of all citations
        - venues: Count by venue
        - top_authors: Most frequent authors

    Example:
        >>> stats = get_paper_statistics(papers_json)
        >>> stats_dict = json.loads(stats)
        >>> print(f"Average citations: {stats_dict['avg_citations']:.1f}")
    """
    try:
        papers = json.loads(papers_json)
    except json.JSONDecodeError:
        return json.dumps({})

    if not papers:
        return json.dumps({})

    # Calculate statistics
    years = [p["year"] for p in papers if p.get("year")]
    citations = [p["citation_count"] for p in papers if p.get("citation_count") is not None]

    # Venue counts
    venues = {}
    for paper in papers:
        venue = paper.get("venue", "Unknown")
        venues[venue] = venues.get(venue, 0) + 1

    # Author counts
    author_counts = {}
    for paper in papers:
        for author in paper.get("authors", []):
            author_counts[author] = author_counts.get(author, 0) + 1

    # Top authors
    top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    stats = {
        "total_count": len(papers),
        "year_range": {
            "earliest": min(years) if years else None,
            "latest": max(years) if years else None
        },
        "avg_citations": sum(citations) / len(citations) if citations else 0,
        "total_citations": sum(citations) if citations else 0,
        "max_citations": max(citations) if citations else 0,
        "min_citations": min(citations) if citations else 0,
        "venue_distribution": venues,
        "top_authors": [{"author": author, "count": count} for author, count in top_authors]
    }

    return json.dumps(stats, indent=2)
