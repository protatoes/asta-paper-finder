"""
CrewAI Tools

This module contains all tool implementations for the Paper Finder CrewAI agents.

Tool Categories:
1. Semantic Scholar Tools: s2_search_by_title, s2_search_by_author, etc.
2. Dense Retrieval Tools: dense_search_bifroest, reformulate_search_query
3. Document Processing Tools: judge_paper_relevance, filter_papers, rank_papers
4. Metadata Tools: extract_query_metadata, identify_query_type
5. LLM Tools: llm_suggest_papers

All tools are decorated with @tool and use ai2i libraries for implementation.

See DESIGN.md for complete tool specifications.
"""
