# Phase 2 Implementation Plan - Simple Agents

**Phase**: Phase 2 - Simple Agents
**Duration Target**: 1-2 weeks
**Start Date**: 2025-11-08
**Status**: Planning

---

## Overview

Phase 2 focuses on implementing three simple, focused agents that handle specific types of paper search queries. These agents serve as the foundation for the more complex agents in later phases and demonstrate the basic CrewAI patterns we'll use throughout the migration.

### Goals

1. Implement three simple, focused agents
2. Create reusable agent and task patterns
3. Establish testing infrastructure for agents
4. Validate CrewAI workflow patterns
5. Build confidence with CrewAI framework

### Why These Three Agents?

These agents were chosen for Phase 2 because:
- **Simple & Focused**: Each has a clear, specific responsibility
- **Minimal Dependencies**: Don't require complex orchestration or state management
- **Essential Functionality**: Core use cases for paper search
- **Learning Value**: Cover different agent patterns (title search, name matching, metadata filtering)

---

## Agent Specifications

### 1. SpecificPaperByTitleAgent

**Purpose**: Find specific papers when the user provides an exact or near-exact title

**Mabool Reference**: `agents/mabool/api/mabool/agents/specific_paper_by_title/specific_paper_by_title_agent.py`

#### Agent Definition

```python
role = "Specific Paper Title Search Specialist"

goal = "Find specific papers when user provides an exact or near-exact title"

backstory = """You are an expert at matching paper titles against academic databases
and handling title variations. You understand that paper titles can have variations,
abbreviations, or slight differences across databases. You're skilled at finding the
right paper even when the title isn't exactly correct."""
```

#### Tools Needed

**Existing Tools** (from Phase 1):
- ✅ `s2_search_by_title` - Search Semantic Scholar by title
- ✅ `s2_get_paper_details` - Get detailed paper information
- ✅ `filter_papers` - Filter by metadata (year, venue, authors)

**New Tools** (to implement):
- ⚠️ `match_title_variants` - Handle title variations and abbreviations (optional - can use LLM reasoning instead)

#### Tasks

**Task 1: Find Paper by Title**
```python
description = """
Search for a specific paper with the following title: "{paper_title}"

Additional constraints:
- Year range: {year_range}
- Venues: {venues}
- Authors: {authors}

Steps:
1. Search Semantic Scholar using the provided title
2. If year_range is provided, filter results by publication year
3. If venues are provided, prioritize papers from those venues
4. If authors are provided, verify they match
5. Return the most relevant matching paper(s)

If no exact match is found, return the closest matches and explain why they might not be exact.
"""

expected_output = """
A JSON response containing:
- The matching paper(s) with full details (title, authors, year, abstract, citation_count, venue)
- A confidence score for the match (0.0-1.0)
- An explanation of why this paper was selected
- If no exact match: alternative suggestions with explanations
"""
```

#### Input Schema

```python
class SpecificPaperByTitleInput(BaseModel):
    paper_title: str
    year_range: str | None = None  # Format: "start-end" e.g., "2017-2020"
    venues: list[str] = []
    authors: list[str] = []
```

#### Output Schema

```python
class SpecificPaperByTitleOutput(BaseModel):
    papers: list[dict]  # List of matching papers
    confidence: float  # 0.0-1.0
    explanation: str  # Why this/these papers were selected
    suggestions: list[dict] = []  # Alternative matches if no exact match
```

#### Example Usage

```python
# Example 1: Simple title search
result = specific_paper_by_title_agent.execute({
    "paper_title": "Attention Is All You Need"
})

# Example 2: Title search with constraints
result = specific_paper_by_title_agent.execute({
    "paper_title": "BERT",
    "year_range": "2018-2019",
    "authors": ["Jacob Devlin"]
})
```

---

### 2. SpecificPaperByNameAgent

**Purpose**: Find papers by their commonly used names (e.g., "BERT", "AlexNet", "GPT-3")

**Mabool Reference**: `agents/mabool/api/mabool/agents/specific_paper_by_name/specific_paper_by_name_agent.py`

#### Agent Definition

```python
role = "Named Paper Search Specialist"

goal = "Find papers by their commonly used names, nicknames, or abbreviations"

backstory = """You are an expert at identifying papers by their popular names and
matching them to actual titles. You know that research papers are often referred to
by abbreviations (BERT, GPT-3), model names (AlexNet, ResNet), or short descriptive
names. You're skilled at understanding the context and finding the original paper
that introduced the concept."""
```

#### Tools Needed

**Existing Tools** (from Phase 1):
- ✅ `s2_search_by_title` - Search by title (will search by name)
- ✅ `s2_search_query` - General S2 search
- ✅ `filter_papers` - Filter by metadata

**New Tools** (to implement):
- ⚠️ `extract_paper_name_from_context` - Extract paper names from query (optional - can use LLM reasoning)

#### Tasks

**Task 1: Find Paper by Common Name**
```python
description = """
Find the paper commonly known as: "{paper_name}"

Context: {context}
Additional constraints:
- Year range: {year_range}
- Research domains: {domains}
- Authors (if known): {authors}

Steps:
1. Understand what the paper name refers to (e.g., "BERT" likely refers to a NLP model)
2. Search Semantic Scholar for papers matching this name
3. Look for papers that:
   - Introduced this concept/model/method
   - Have the name in the title or are commonly cited with this name
   - Match any provided constraints (year, domain, authors)
4. Return the most likely original/seminal paper

If multiple papers match, return them ranked by relevance and likelihood.
"""

expected_output = """
A JSON response containing:
- The matching paper(s) with full details
- Confidence score for each match
- Explanation of why each paper was selected
- Whether this is the original/seminal paper or a related work
"""
```

#### Input Schema

```python
class SpecificPaperByNameInput(BaseModel):
    paper_name: str  # e.g., "BERT", "AlexNet", "GPT-3"
    context: str = ""  # Additional context from user query
    year_range: str | None = None
    domains: list[str] = []
    authors: list[str] = []
```

#### Output Schema

```python
class SpecificPaperByNameOutput(BaseModel):
    papers: list[dict]
    confidence: float
    explanation: str
    is_original_paper: bool  # True if this is the seminal/original paper
```

#### Example Usage

```python
# Example 1: Find BERT paper
result = specific_paper_by_name_agent.execute({
    "paper_name": "BERT",
    "context": "the original paper that introduced BERT"
})

# Example 2: Find AlexNet with constraints
result = specific_paper_by_name_agent.execute({
    "paper_name": "AlexNet",
    "year_range": "2012-2013",
    "domains": ["Computer Vision"]
})
```

---

### 3. MetadataOnlyAgent

**Purpose**: Find papers using only metadata criteria (venue, year, domain) without content search

**Mabool Reference**: `agents/mabool/api/mabool/agents/metadata_only/metadata_only_agent.py`

#### Agent Definition

```python
role = "Metadata-based Filter Specialist"

goal = "Find papers using only metadata criteria such as venue, year range, and research domain"

backstory = """You are an expert at metadata-based filtering and aggregation. You understand
publication venues, research domains, and how to efficiently filter large sets of papers
based purely on their metadata. You don't search paper content - you work exclusively with
structured metadata like publication venue, year, research field, and citation counts."""
```

#### Tools Needed

**Existing Tools** (from Phase 1):
- ✅ `filter_papers` - Filter by year, venue, citations, authors
- ✅ `sort_papers` - Sort by various criteria
- ✅ `take_top_papers` - Limit results
- ✅ `get_paper_statistics` - Calculate statistics

**New Tools** (to implement):
- 🆕 `aggregate_by_venue` - Group and aggregate papers by venue
- 🆕 `aggregate_by_year` - Group and aggregate papers by year
- 🆕 `aggregate_by_domain` - Group and aggregate papers by research field
- ⚠️ Or a single `aggregate_papers` tool with aggregation_field parameter

#### Tasks

**Task 1: Filter Papers by Metadata**
```python
description = """
Filter a collection of papers based on metadata criteria:

Criteria:
- Venues: {venues}
- Year range: {year_range}
- Minimum citation count: {min_citations}
- Authors: {authors}
- Research domains: {domains}

Steps:
1. Start with the provided paper collection: {papers_json}
2. Apply each filter criterion sequentially
3. Sort results by: {sort_by} ({sort_order})
4. Limit to top {limit} results
5. Return filtered papers with statistics

Provide summary statistics about:
- Total papers before/after filtering
- Year distribution
- Venue distribution
- Citation statistics
"""

expected_output = """
A JSON response containing:
- Filtered papers list with full metadata
- Statistics about the filtered set
- Explanation of how filters were applied
- Summary of what was found
"""
```

#### Input Schema

```python
class MetadataOnlyInput(BaseModel):
    papers_json: str  # JSON string of papers to filter
    venues: list[str] = []
    year_range: str | None = None
    min_citations: int | None = None
    authors: list[str] = []
    domains: list[str] = []
    sort_by: str = "citation_count"  # citation_count, year, title
    sort_order: str = "desc"  # desc or asc
    limit: int = 100
```

#### Output Schema

```python
class MetadataOnlyOutput(BaseModel):
    papers: list[dict]
    statistics: dict  # Total, year dist, venue dist, citation stats
    explanation: str
    filters_applied: list[str]  # List of filters that were applied
```

#### Example Usage

```python
# Example 1: Filter by venue and year
result = metadata_only_agent.execute({
    "papers_json": large_paper_collection,
    "venues": ["NeurIPS", "ICML", "ICLR"],
    "year_range": "2020-2023",
    "sort_by": "citation_count",
    "limit": 50
})

# Example 2: High-impact papers by specific authors
result = metadata_only_agent.execute({
    "papers_json": author_papers,
    "min_citations": 100,
    "year_range": "2015-2025",
    "sort_by": "year",
    "sort_order": "desc"
})
```

---

## Implementation Strategy

### Step 1: Review Mabool Implementations (1-2 hours)

**Goal**: Understand existing logic before implementing CrewAI versions

**Files to Review**:
```bash
# SpecificPaperByTitleAgent
agents/mabool/api/mabool/agents/specific_paper_by_title/specific_paper_by_title_agent.py

# SpecificPaperByNameAgent
agents/mabool/api/mabool/agents/specific_paper_by_name/specific_paper_by_name_agent.py

# MetadataOnlyAgent
agents/mabool/api/mabool/agents/metadata_only/metadata_only_agent.py
```

**What to Extract**:
- Business logic patterns
- How they handle edge cases
- What tools/methods they use
- Input/output formats
- Error handling strategies

### Step 2: Implement Missing Tools (2-4 hours)

**Tools to Create** (if needed after mabool review):

1. **Aggregation Tools** (for MetadataOnlyAgent)
   - `aggregate_papers` - Group and aggregate by field

2. **Optional Helper Tools**:
   - `match_title_variants` - Handle title variations (only if needed)
   - `extract_paper_name` - Extract paper names (only if LLM can't handle it)

**Location**: `agents/crewai/api/paperfinder_crew/tools/aggregation.py`

### Step 3: Create Agent Definitions (3-4 hours)

**For Each Agent**:

1. Create agent file in `agents/crewai/api/paperfinder_crew/agents/`
2. Define agent with role, goal, backstory
3. Assign appropriate tools
4. Create helper functions if needed
5. Add comprehensive docstrings

**Files to Create**:
```
agents/crewai/api/paperfinder_crew/agents/
├── __init__.py
├── specific_paper_by_title_agent.py
├── specific_paper_by_name_agent.py
└── metadata_only_agent.py
```

### Step 4: Create Task Definitions (2-3 hours)

**For Each Agent**:

1. Create task file in `agents/crewai/api/paperfinder_crew/tasks/`
2. Define task templates with clear descriptions
3. Define expected outputs
4. Add validation logic if needed

**Files to Create**:
```
agents/crewai/api/paperfinder_crew/tasks/
├── __init__.py
├── specific_paper_by_title_tasks.py
├── specific_paper_by_name_tasks.py
└── metadata_only_tasks.py
```

### Step 5: Create Simple Crews for Testing (2-3 hours)

Create simple crews that test each agent individually:

```python
# agents/crewai/api/paperfinder_crew/crews/test_crews.py

def create_title_search_crew():
    """Simple crew for testing SpecificPaperByTitleAgent"""
    agent = create_specific_paper_by_title_agent()
    task = create_title_search_task(
        paper_title="{paper_title}",
        year_range="{year_range}",
        venues="{venues}",
        authors="{authors}"
    )
    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential
    )
```

**Files to Create**:
```
agents/crewai/api/paperfinder_crew/crews/
├── __init__.py
└── test_crews.py
```

### Step 6: Create Testing Infrastructure (3-4 hours)

**Test Strategy**:

1. **Unit Tests for Agents**: Test agent creation, tool assignment
2. **Integration Tests**: Test agent execution with real/mock data
3. **End-to-End Tests**: Test complete crew workflows

**Files to Create**:
```
agents/crewai/api/paperfinder_crew/tests/
├── test_agents/
│   ├── __init__.py
│   ├── test_specific_paper_by_title_agent.py
│   ├── test_specific_paper_by_name_agent.py
│   └── test_metadata_only_agent.py
├── test_tasks/
│   ├── __init__.py
│   └── test_task_definitions.py
└── test_crews/
    ├── __init__.py
    └── test_simple_crews.py
```

### Step 7: Write Tests and Validate (4-6 hours)

**Test Cases to Cover**:

For **SpecificPaperByTitleAgent**:
- Exact title match
- Partial title match
- Title with year constraint
- Title with venue constraint
- Title not found (should suggest alternatives)

For **SpecificPaperByNameAgent**:
- Common abbreviation (e.g., "BERT")
- Model name (e.g., "AlexNet")
- Method name (e.g., "Word2Vec")
- Ambiguous name (multiple matches)
- Unknown name (should explain and suggest)

For **MetadataOnlyAgent**:
- Filter by single criterion
- Filter by multiple criteria
- Sort by different fields
- Aggregation by venue/year
- Empty results (all filtered out)

---

## Dependencies & Prerequisites

### From Phase 1 (Already Complete)

✅ **Tools Available**:
- S2 search tools (6 tools)
- Document processing tools (8 tools)
- Testing infrastructure

✅ **Infrastructure**:
- Package structure
- Dependencies installed
- Test fixtures

### New Dependencies Needed

**None** - All dependencies from Phase 1 are sufficient for Phase 2

### Environment Requirements

- Python 3.12.8+
- CrewAI 0.193.2+
- Access to Semantic Scholar API (S2_API_KEY)
- OpenAI API for LLM (OPENAI_API_KEY)

---

## Success Criteria

### Functionality

- [📋] All three agents can be instantiated successfully
- [📋] Each agent can execute its assigned tasks
- [📋] Agents use tools correctly
- [📋] Agents return properly formatted outputs
- [📋] Error handling works (graceful degradation)

### Testing

- [📋] >90% test coverage for agent code
- [📋] All unit tests pass
- [📋] All integration tests pass
- [📋] End-to-end crew tests pass

### Code Quality

- [📋] Comprehensive docstrings for all agents
- [📋] Type hints for all functions
- [📋] Clean, readable code following Phase 1 patterns
- [📋] Exports properly configured in __init__.py files

### Documentation

- [📋] Agent usage examples documented
- [📋] Task templates documented
- [📋] SESSION.md updated with progress
- [📋] PROGRESS.md updated with completion status

### Learning Goals

- [📋] Understand CrewAI Agent creation patterns
- [📋] Understand CrewAI Task definition patterns
- [📋] Understand Crew composition patterns
- [📋] Identify differences from Operative pattern

---

## Timeline Estimate

| Task | Estimated Time | Dependencies |
|------|----------------|--------------|
| Review mabool implementations | 1-2 hours | None |
| Create aggregation tools (if needed) | 2-4 hours | Mabool review |
| Implement SpecificPaperByTitleAgent | 2-3 hours | Tools ready |
| Implement SpecificPaperByNameAgent | 2-3 hours | Tools ready |
| Implement MetadataOnlyAgent | 2-3 hours | Tools ready |
| Create task definitions | 2-3 hours | Agents created |
| Create test crews | 2-3 hours | Agents + tasks |
| Write agent tests | 4-6 hours | All agents complete |
| Documentation updates | 1-2 hours | Implementation complete |

**Total Estimated Time**: 18-29 hours (~2-4 days of focused work)

---

## Risk Assessment

### Low Risk

✅ **Tools Already Available**: Most tools from Phase 1 can be reused
✅ **Simple Agents**: These agents have focused, well-defined responsibilities
✅ **Reference Implementation**: Mabool provides clear examples

### Medium Risk

⚠️ **CrewAI Learning Curve**: First time creating actual agents
⚠️ **Task Definition Format**: Need to learn proper task description patterns
⚠️ **LLM Behavior**: May need prompt tuning to get desired behavior

### Mitigation Strategies

1. **Start Simple**: Begin with SpecificPaperByTitleAgent (simplest)
2. **Iterative Testing**: Test each agent thoroughly before moving to next
3. **Mabool Reference**: Use mabool code as reference for business logic
4. **Prompt Engineering**: Iterate on agent backstories and task descriptions

---

## Open Questions

### Question 1: Tool Selection

**Question**: Should we create specialized tools (e.g., `match_title_variants`) or rely on LLM reasoning within tasks?

**Options**:
- A) Create specialized tools for specific logic
- B) Use LLM reasoning in task descriptions
- C) Hybrid - simple tools + LLM reasoning

**Recommendation**: Start with option B (LLM reasoning), add tools only if needed

**Decision Point**: During Step 2 (after mabool review)

---

### Question 2: Output Format

**Question**: Should agents return JSON strings or structured Pydantic models?

**Options**:
- A) Return JSON strings (like tools do)
- B) Return Pydantic models (more type-safe)
- C) Support both

**Recommendation**: Use Pydantic models for type safety, convert to JSON when needed

**Decision Point**: During Step 3 (agent implementation)

---

### Question 3: Testing Approach

**Question**: Should we test with real S2 API calls or use mocks?

**Options**:
- A) Real API calls (integration tests)
- B) Mocked API calls (unit tests)
- C) Both (unit tests with mocks + integration tests with real API)

**Recommendation**: Option C - Both types of tests

**Decision Point**: During Step 6 (test infrastructure)

---

## Next Steps

1. **Update SESSION.md** to reflect Phase 2 start
2. **Update PROGRESS.md** with Phase 2 tasks
3. **Review mabool agent implementations** to extract business logic
4. **Start implementing first agent** (SpecificPaperByTitleAgent)

---

## Phase 2 Completion Checklist

### Planning & Setup
- [x] Phase 2 plan document created
- [ ] SESSION.md updated for Phase 2
- [ ] PROGRESS.md updated with Phase 2 tasks
- [ ] Mabool agents reviewed and documented

### Implementation
- [ ] Aggregation tools created (if needed)
- [ ] SpecificPaperByTitleAgent implemented
- [ ] SpecificPaperByNameAgent implemented
- [ ] MetadataOnlyAgent implemented
- [ ] Task definitions created for all agents
- [ ] Test crews created

### Testing
- [ ] Unit tests written for all agents
- [ ] Integration tests written
- [ ] All tests passing
- [ ] Test coverage >90%

### Documentation
- [ ] Agent usage examples added
- [ ] Task templates documented
- [ ] SESSION.md updated with learnings
- [ ] PROGRESS.md marked complete

### Review & Commit
- [ ] Code review completed
- [ ] All files committed
- [ ] Phase 2 branch pushed to remote
- [ ] Ready for Phase 3

---

**Document Version**: 1.0
**Last Updated**: 2025-11-08
**Author**: Claude (Phase 2 Planning)
