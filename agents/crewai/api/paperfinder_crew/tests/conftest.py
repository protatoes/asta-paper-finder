"""
Pytest configuration and shared fixtures for Paper Finder CrewAI tests.
"""

import json
import pytest


@pytest.fixture
def sample_papers_json():
    """Sample papers in JSON format for testing"""
    papers = [
        {
            "corpus_id": "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
            "year": 2017,
            "abstract": "The dominant sequence transduction models...",
            "citation_count": 50000,
            "venue": "NeurIPS",
        },
        {
            "corpus_id": "df2b0e26d0599ce3e70df8a9da02e51594e0e992",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee"],
            "year": 2019,
            "abstract": "We introduce BERT...",
            "citation_count": 45000,
            "venue": "NAACL",
        },
        {
            "corpus_id": "cd18800a0fe0b668a1cc19f2ec95b5003d0a5035",
            "title": "Language Models are Few-Shot Learners",
            "authors": ["Tom B. Brown", "Benjamin Mann", "Nick Ryder"],
            "year": 2020,
            "abstract": "We demonstrate that scaling...",
            "citation_count": 30000,
            "venue": "NeurIPS",
        },
        {
            "corpus_id": "e33b74f1a2ba4a61922e8ba1b5f79b7e8ea4b7c3",
            "title": "An Image is Worth 16x16 Words",
            "authors": ["Alexey Dosovitskiy", "Lucas Beyer"],
            "year": 2021,
            "abstract": "Vision Transformer (ViT)...",
            "citation_count": 20000,
            "venue": "ICLR",
        },
        {
            "corpus_id": "a1234567890abcdef1234567890abcdef123456",
            "title": "Old Paper from 2010",
            "authors": ["Alice Smith"],
            "year": 2010,
            "abstract": "An older paper...",
            "citation_count": 100,
            "venue": "ACL",
        },
    ]
    return json.dumps(papers, indent=2)


@pytest.fixture
def sample_papers_list():
    """Sample papers as Python list"""
    return [
        {
            "corpus_id": "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
            "title": "Attention Is All You Need",
            "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
            "year": 2017,
            "citation_count": 50000,
            "venue": "NeurIPS",
        },
        {
            "corpus_id": "df2b0e26d0599ce3e70df8a9da02e51594e0e992",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee"],
            "year": 2019,
            "citation_count": 45000,
            "venue": "NAACL",
        },
        {
            "corpus_id": "cd18800a0fe0b668a1cc19f2ec95b5003d0a5035",
            "title": "Language Models are Few-Shot Learners",
            "authors": ["Tom B. Brown", "Benjamin Mann", "Nick Ryder"],
            "year": 2020,
            "citation_count": 30000,
            "venue": "NeurIPS",
        },
    ]
