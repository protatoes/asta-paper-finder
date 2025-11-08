"""
Tests for document processing tools.
"""

import json
import pytest

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


def test_filter_papers_by_year(sample_papers_json):
    """Test filtering papers by year range"""
    result = filter_papers.run(papers_json=sample_papers_json, year_range="2017-2020")
    papers = json.loads(result)

    assert len(papers) == 3  # 2017, 2019, 2020 (excludes 2021 and 2010)
    assert all(2017 <= p["year"] <= 2020 for p in papers)


def test_filter_papers_by_venue(sample_papers_json):
    """Test filtering papers by venue"""
    result = filter_papers.run(papers_json=sample_papers_json, venues="NeurIPS,ICLR")
    papers = json.loads(result)

    assert len(papers) == 3  # 2 NeurIPS + 1 ICLR
    assert all(p["venue"] in ["NeurIPS", "ICLR"] for p in papers)


def test_filter_papers_by_citations(sample_papers_json):
    """Test filtering by minimum citation count"""
    result = filter_papers.run(papers_json=sample_papers_json, min_citation_count=25000)
    papers = json.loads(result)

    assert len(papers) == 3  # Only papers with >= 25000 citations
    assert all(p["citation_count"] >= 25000 for p in papers)


def test_filter_papers_by_author(sample_papers_json):
    """Test filtering by author name"""
    result = filter_papers.run(papers_json=sample_papers_json, authors="Tom B. Brown")
    papers = json.loads(result)

    assert len(papers) == 1
    assert "Tom B. Brown" in papers[0]["authors"]


def test_filter_papers_combined(sample_papers_json):
    """Test filtering with multiple criteria"""
    result = filter_papers.run(
        papers_json=sample_papers_json,
        year_range="2019-2021",
        venues="NeurIPS",
        min_citation_count=25000
    )
    papers = json.loads(result)

    assert len(papers) == 1  # Only GPT-3 paper
    assert papers[0]["title"] == "Language Models are Few-Shot Learners"


def test_deduplicate_papers():
    """Test deduplication of papers"""
    papers_with_dupes = [
        {"corpus_id": "id1", "title": "Paper 1"},
        {"corpus_id": "id2", "title": "Paper 2"},
        {"corpus_id": "id1", "title": "Paper 1"},  # Duplicate
        {"corpus_id": "id3", "title": "Paper 3"},
    ]
    papers_json = json.dumps(papers_with_dupes)

    result = deduplicate_papers.run(papers_json=papers_json)
    papers = json.loads(result)

    assert len(papers) == 3
    assert [p["corpus_id"] for p in papers] == ["id1", "id2", "id3"]


def test_sort_papers_by_citations(sample_papers_json):
    """Test sorting by citation count"""
    result = sort_papers.run(papers_json=sample_papers_json, sort_by="citation_count", descending=True)
    papers = json.loads(result)

    citations = [p["citation_count"] for p in papers]
    assert citations == sorted(citations, reverse=True)
    assert papers[0]["title"] == "Attention Is All You Need"  # Most cited


def test_sort_papers_by_year_ascending(sample_papers_json):
    """Test sorting by year in ascending order"""
    result = sort_papers.run(papers_json=sample_papers_json, sort_by="year", descending=False)
    papers = json.loads(result)

    years = [p["year"] for p in papers]
    assert years == sorted(years)
    assert papers[0]["year"] == 2010  # Oldest first


def test_take_top_papers(sample_papers_json):
    """Test taking top N papers"""
    result = take_top_papers.run(papers_json=sample_papers_json, n=3)
    papers = json.loads(result)

    assert len(papers) == 3


def test_combine_papers():
    """Test combining two paper lists"""
    papers1 = [{"corpus_id": "id1", "title": "Paper 1"}]
    papers2 = [{"corpus_id": "id2", "title": "Paper 2"}]

    result = combine_papers.run(
        papers_json_1=json.dumps(papers1),
        papers_json_2=json.dumps(papers2),
        deduplicate=False
    )
    combined = json.loads(result)

    assert len(combined) == 2


def test_combine_papers_with_deduplication():
    """Test combining with deduplication"""
    papers1 = [
        {"corpus_id": "id1", "title": "Paper 1"},
        {"corpus_id": "id2", "title": "Paper 2"}
    ]
    papers2 = [
        {"corpus_id": "id2", "title": "Paper 2"},  # Duplicate
        {"corpus_id": "id3", "title": "Paper 3"}
    ]

    result = combine_papers.run(
        papers_json_1=json.dumps(papers1),
        papers_json_2=json.dumps(papers2),
        deduplicate=True
    )
    combined = json.loads(result)

    assert len(combined) == 3


def test_extract_corpus_ids(sample_papers_json):
    """Test extracting corpus IDs"""
    result = extract_corpus_ids.run(papers_json=sample_papers_json)

    ids = result.split(",")
    assert len(ids) == 5
    assert "204e3073870fae3d05bcbc2f6a8e263d9b72e776" in ids


def test_count_papers(sample_papers_json):
    """Test counting papers"""
    count = count_papers.run(papers_json=sample_papers_json)

    assert count == "5"


def test_get_paper_statistics(sample_papers_json):
    """Test getting paper statistics"""
    result = get_paper_statistics.run(papers_json=sample_papers_json)
    stats = json.loads(result)

    assert stats["total_count"] == 5
    assert stats["year_range"]["earliest"] == 2010
    assert stats["year_range"]["latest"] == 2021
    assert stats["avg_citations"] == (50000 + 45000 + 30000 + 20000 + 100) / 5
    assert stats["max_citations"] == 50000
    assert stats["min_citations"] == 100

    # Check venue distribution
    assert "NeurIPS" in stats["venue_distribution"]
    assert stats["venue_distribution"]["NeurIPS"] == 2

    # Check top authors
    assert len(stats["top_authors"]) > 0


def test_empty_papers_list():
    """Test tools with empty papers list"""
    empty_json = json.dumps([])

    # Should handle gracefully
    assert filter_papers.run(papers_json=empty_json) == "[]"
    assert count_papers.run(papers_json=empty_json) == "0"
    assert extract_corpus_ids.run(papers_json=empty_json) == ""


def test_invalid_json():
    """Test tools with invalid JSON"""
    invalid_json = "not valid json"

    # Should return empty/default results
    assert filter_papers.run(papers_json=invalid_json) == "[]"
    assert count_papers.run(papers_json=invalid_json) == "0"
    assert extract_corpus_ids.run(papers_json=invalid_json) == ""
