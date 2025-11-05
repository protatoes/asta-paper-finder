"""
CrewAI Agent Definitions

This module contains all CrewAI agent definitions for the Paper Finder system.

Agents:
- QueryAnalyzerAgent: Analyzes queries and routes to appropriate specialists
- SpecificPaperByTitleAgent: Finds specific papers by title
- SpecificPaperByNameAgent: Finds papers by common name
- SearchByAuthorsAgent: Searches for papers by author
- BroadSearchAgent: Comprehensive research search (diligent mode)
- FastBroadSearchAgent: Quick research search (fast mode)
- DenseSearchAgent: Vector-based semantic search
- MetadataOnlyAgent: Metadata-based filtering
- MetadataPlannerAgent: Plans complex metadata queries
- SnowballAgent: Citation-based expansion
- LLMSuggestionAgent: Fallback LLM suggestions
- BroadSearchByKeywordAgent: Keyword-based search

See DESIGN.md for detailed agent specifications.
"""
