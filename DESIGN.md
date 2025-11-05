# Paper Finder CrewAI Migration - Design Document

**Version**: 1.0
**Last Updated**: 2025-11-05
**Status**: Planning Phase

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Comparison](#architecture-comparison)
3. [Design Decisions](#design-decisions)
4. [CrewAI Concepts & Mappings](#crewai-concepts--mappings)
5. [Agent Specifications](#agent-specifications)
6. [Tool Specifications](#tool-specifications)
7. [Workflow Designs](#workflow-designs)
8. [State Management Strategy](#state-management-strategy)
9. [API Integration](#api-integration)
10. [Testing Strategy](#testing-strategy)

---

## Overview

### Purpose

This document outlines the design for migrating the Paper Finder agent system from a custom "Operative" pattern to CrewAI framework. This migration serves dual purposes:
1. **Learning**: Deep understanding of CrewAI architecture and patterns
2. **Modernization**: Leveraging a community-supported framework for better maintainability and extensibility

### Goals

- ✅ Maintain all existing functionality
- ✅ Side-by-side implementation (mabool + crewai coexist)
- ✅ Preserve valuable libraries (ai2i.dcollection, ai2i.chain, ai2i.config, ai2i.di)
- ✅ Replace custom Operative pattern with CrewAI
- ✅ Improve extensibility for future features
- ✅ Learn CrewAI through practical implementation

### Non-Goals

- ❌ Complete removal of mabool implementation (keeping for comparison)
- ❌ Rewriting ai2i libraries
- ❌ Changing external API contracts initially

---

## Architecture Comparison

### Current Architecture (Mabool)

```
┌─────────────────────────────────────────────────┐
│           FastAPI REST API Layer                │
│         (round_v2_routes.py)                    │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│         PaperFinderAgent (Orchestrator)         │
│         Custom Operative Pattern                 │
│         - handle_operation()                     │
│         - register() sub-agents                  │
│         - State management                       │
└─────────────────────────────────────────────────┘
                     ↓
        ┌────────────┴────────────┐
        ↓                          ↓
┌──────────────┐          ┌──────────────────┐
│ Query        │          │ 13 Specialized   │
│ Analyzer     │ ──────→  │ Sub-Agents       │
│ (Operative)  │          │ (Operatives)     │
└──────────────┘          └──────────────────┘
        ↓                          ↓
┌─────────────────────────────────────────────────┐
│        ai2i Libraries + External APIs            │
│  - dcollection (document handling)               │
│  - chain (LLM interactions)                      │
│  - Semantic Scholar, Dense Search, Cohere        │
└─────────────────────────────────────────────────┘
```

### Target Architecture (CrewAI)

```
┌─────────────────────────────────────────────────┐
│           FastAPI REST API Layer                │
│     (NEW: crewai_routes.py + feature flags)     │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│         PaperFinderCrew (Orchestrator)          │
│         CrewAI Crew + Manager Agent              │
│         - Sequential/Hierarchical Process        │
│         - Task-based orchestration               │
│         - CrewAI Memory (state)                  │
└─────────────────────────────────────────────────┘
                     ↓
        ┌────────────┴────────────┐
        ↓                          ↓
┌──────────────┐          ┌──────────────────┐
│ Query        │          │ 13+ CrewAI       │
│ Analyzer     │ ──────→  │ Agents           │
│ (Agent)      │          │ (w/ Tools)       │
└──────────────┘          └──────────────────┘
        ↓                          ↓
┌─────────────────────────────────────────────────┐
│     Fine-Grained CrewAI Tools (@tool)            │
│  - S2SearchByTitle, S2SearchByAuthor            │
│  - DenseRetrievalSearch, SnippetExtraction      │
│  - DocumentFilter, DocumentSort, RerankDocs     │
└─────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────┐
│        ai2i Libraries + External APIs            │
│  (PRESERVED - used by tools)                     │
└─────────────────────────────────────────────────┘
```

---

## Design Decisions

### 1. Coexistence Strategy: Side-by-Side ✅

**Decision**: Implement CrewAI alongside existing mabool implementation

**Rationale**:
- Allows for A/B testing and comparison
- Provides fallback if issues arise
- Enables gradual migration of features
- Learning safety net

**Implementation**:
```
agents/
├── mabool/          # Existing implementation (preserved)
│   └── api/
│       └── mabool/
└── crewai/          # New CrewAI implementation
    └── api/
        └── paperfinder_crew/
```

**Feature Flags**:
```python
# In config
USE_CREWAI_IMPLEMENTATION = os.getenv("USE_CREWAI", "false").lower() == "true"
```

### 2. Replace Operative Pattern ✅

**Decision**: Replace custom Operative pattern with CrewAI Agents, Crews, and Tasks

**Mapping**:

| Mabool Concept | CrewAI Equivalent |
|----------------|-------------------|
| `Operative[INPUT, OUTPUT, STATE]` | `Agent` + `Task` |
| `handle_operation()` | `Agent.execute_task()` via Task |
| `register()` sub-agents | Crew composition |
| `OperativeResponse` | Task output |
| `CompleteResponse/PartialResponse/VoidResponse` | Task result with error handling |
| State management | CrewAI Memory (TBD approach) |
| `operative_session()` | Crew kickoff with context |

### 3. State Management: Investigate & Implement ⚠️

**Status**: Design in progress

**Current Approach (Mabool)**:
- Each Operative maintains typed state: `STATE` type parameter
- State persisted across operations: `tuple[STATE, OperativeResponse]`
- Session-based state storage with TTL cache

**CrewAI Options**:

**Option A: CrewAI Memory (Built-in)**
```python
from crewai import Crew
from crewai.memory import ShortTermMemory, LongTermMemory, EntityMemory

crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # Enable all memory types
    # OR selective:
    short_term_memory=ShortTermMemory(),
    long_term_memory=LongTermMemory(),
    entity_memory=EntityMemory()
)
```

**Option B: Custom State via Context/Callbacks**
```python
# Pass state through task context
task = Task(
    description="...",
    context={"state": previous_state, "corpus_ids": [...]},
    agent=agent
)
```

**Option C: Hybrid - CrewAI Memory + Custom State Store**
```python
# Use CrewAI memory for agent-to-agent communication
# Use external state store (Redis/File) for complex state
class StatefulCrew:
    def __init__(self):
        self.state_store = StateStore()
        self.crew = Crew(memory=True, ...)

    async def run(self, session_id: str, input_data: dict):
        state = await self.state_store.get(session_id)
        result = self.crew.kickoff(inputs={**input_data, "state": state})
        await self.state_store.save(session_id, result.state)
        return result
```

**Recommendation**: Start with Option B (simple), evaluate Option A as we learn CrewAI memory capabilities, consider Option C if needed for complex state.

### 4. Query Analyzer: Agent-Based Router ✅

**Decision**: Implement QueryAnalyzer as a CrewAI Agent that routes to specialized agents

```python
query_analyzer_agent = Agent(
    role="Query Analyzer & Router",
    goal="Analyze user queries and route to appropriate search agents",
    backstory="Expert at understanding paper search intents...",
    tools=[
        analyze_query_tool,
        extract_metadata_tool,
        identify_query_type_tool
    ],
    verbose=True
)

# Routing logic in manager agent or sequential tasks
```

**Alternative Considered**: Separate preprocessing step (rejected - less integrated)

### 5. Tool Granularity: Fine-Grained ✅

**Decision**: Create multiple specific tools per capability

**Rationale**:
- Better agent autonomy (agents choose specific tools)
- Clearer tool purposes and documentation
- More natural CrewAI patterns
- Easier to add/modify individual capabilities

**Example**:
```python
# ✅ Fine-grained (CHOSEN)
@tool("Search papers by title on Semantic Scholar")
def s2_search_by_title(title: str, year_range: tuple[int, int] | None = None) -> list[dict]:
    """Search for papers by title with optional year filtering"""
    ...

@tool("Search papers by author on Semantic Scholar")
def s2_search_by_author(author_names: list[str], limit: int = 10) -> list[dict]:
    """Search for papers by author names"""
    ...

@tool("Get paper details from Semantic Scholar")
def s2_get_paper_details(corpus_id: str) -> dict:
    """Retrieve detailed information for a specific paper"""
    ...

# ❌ Coarse-grained (REJECTED)
@tool("Semantic Scholar search")
def semantic_scholar_search(query_type: str, **kwargs) -> list[dict]:
    """Multipurpose Semantic Scholar search"""
    ...
```

---

## CrewAI Concepts & Mappings

### Core CrewAI Components

#### 1. Agent

**Definition**: An autonomous unit that performs tasks using tools and LLM reasoning.

**Key Attributes**:
```python
Agent(
    role="Agent's job title",
    goal="What the agent aims to achieve",
    backstory="Context about the agent's expertise",
    tools=[list of @tool decorated functions],
    llm=llm_instance,  # Optional: default uses ChatOpenAI
    verbose=True,
    allow_delegation=True,  # Can delegate to other agents
    memory=True  # Remember past interactions
)
```

**Mapping from Operative**:
```python
# Mabool Operative
class SearchByAuthorsAgent(Operative[SearchByAuthorsInput, SearchByAuthorsOutput, AgentState]):
    async def handle_operation(self, state, inputs):
        # Custom logic here
        return state, CompleteResponse(data=output)

# CrewAI Agent (rough equivalent)
search_by_authors_agent = Agent(
    role="Author-based Paper Search Specialist",
    goal="Find relevant papers by specific authors",
    tools=[s2_search_by_author, filter_papers_by_content, rank_papers],
    ...
)
```

#### 2. Task

**Definition**: A specific job to be performed by an agent.

**Key Attributes**:
```python
Task(
    description="Detailed description with context and variables {variable}",
    expected_output="Clear description of expected output format",
    agent=agent_instance,
    tools=[optional_task_specific_tools],
    context=[list of previous tasks this task depends on],
    output_json=OutputModel,  # Pydantic model for structured output
    output_file="path/to/save/output.json"  # Optional
)
```

**Mapping from handle_operation**:
```python
# Mabool operation
await self.search_by_authors(SearchByAuthorsInput(...))

# CrewAI task
search_task = Task(
    description="""
        Search for papers by authors: {authors}
        Filter by content: {content_query}
        Time range: {time_range}
    """,
    expected_output="List of papers with relevance scores",
    agent=search_by_authors_agent,
    output_json=SearchByAuthorsOutput
)
```

#### 3. Tool

**Definition**: A function that agents can use to perform actions.

**Implementation**:
```python
from crewai_tools import tool

@tool("Tool name for agent to see")
def tool_function(param1: str, param2: int) -> str:
    """
    Detailed description of what the tool does.
    The LLM reads this to understand when to use the tool.

    Args:
        param1: Description of parameter
        param2: Description of parameter

    Returns:
        Description of return value
    """
    # Implementation using ai2i libraries
    result = some_ai2i_library_function(param1, param2)
    return result
```

#### 4. Crew

**Definition**: Orchestrates agents working together on a set of tasks.

**Key Attributes**:
```python
Crew(
    agents=[list of agents],
    tasks=[list of tasks in execution order],
    process=Process.sequential,  # or Process.hierarchical
    manager_llm=manager_llm,  # Required for hierarchical
    memory=True,
    verbose=True,
    cache=True  # Cache tool results
)
```

**Processes**:
- **Sequential**: Tasks execute one after another in order
- **Hierarchical**: Manager agent delegates tasks to other agents

**Mapping from PaperFinderAgent**:
```python
# Mabool PaperFinderAgent
class PaperFinderAgent(Operative):
    def register(self):
        self.broad_search_agent = self.init_operative("broad_search", BroadSearchAgent)
        self.specific_by_title = self.init_operative("specific_title", SpecificByTitleAgent)
        # ... more agents

    async def handle_operation(self, state, inputs):
        # Route based on query type
        match inputs.query_type:
            case "BROAD_BY_DESCRIPTION":
                return await self.broad_search_agent(...)
            # ... more cases

# CrewAI Crew
paper_finder_crew = Crew(
    agents=[
        query_analyzer_agent,
        broad_search_agent,
        specific_title_agent,
        # ... more agents
    ],
    tasks=[
        analyze_query_task,
        # Conditional routing via manager in hierarchical mode
        # OR dynamic task creation based on analysis
    ],
    process=Process.hierarchical,  # Manager handles routing
    manager_agent=query_analyzer_agent,
    memory=True
)
```

### CrewAI Memory System

**Short-Term Memory**:
- Remembers context within current conversation
- Useful for multi-turn interactions
- Cleared after crew execution completes

**Long-Term Memory**:
- Persists across multiple crew executions
- Uses embeddings to retrieve relevant past interactions
- Useful for learning from past queries

**Entity Memory**:
- Tracks entities (authors, papers, venues) mentioned
- Maintains entity relationships
- Useful for contextual understanding

**Usage**:
```python
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # Enables all memory types
    # OR customize:
    short_term_memory=ShortTermMemory(storage=CustomStorage()),
    long_term_memory=LongTermMemory(storage=CustomStorage()),
    entity_memory=EntityMemory(storage=CustomStorage())
)
```

### CrewAI Process Flows

#### Sequential Process

Tasks execute in order, each receiving output from previous:

```python
crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[task1, task2, task3],
    process=Process.sequential
)

# Execution: task1 → task2 (gets task1 output) → task3 (gets task2 output)
```

#### Hierarchical Process

Manager agent delegates tasks to worker agents:

```python
manager = Agent(
    role="Manager",
    goal="Coordinate team to accomplish goal",
    allow_delegation=True
)

crew = Crew(
    agents=[manager, worker1, worker2, worker3],
    tasks=[task1, task2, task3],
    process=Process.hierarchical,
    manager_agent=manager  # OR manager_llm for auto-manager
)

# Manager decides which agent handles which task
```

---

## Agent Specifications

### Agent Hierarchy

```
PaperFinderCrew (Crew with Manager)
├── QueryAnalyzerAgent (Manager/Router)
└── Specialist Agents
    ├── SpecificPaperByTitleAgent
    ├── SpecificPaperByNameAgent
    ├── SearchByAuthorsAgent
    ├── BroadSearchAgent
    ├── FastBroadSearchAgent
    ├── DenseSearchAgent
    ├── MetadataOnlyAgent
    ├── MetadataPlannerAgent
    ├── SnowballAgent
    ├── LLMSuggestionAgent
    └── BroadSearchByKeywordAgent
```

### Agent Specifications

#### QueryAnalyzerAgent

**Role**: Query Analyzer & Router
**Goal**: Analyze paper search queries and route to appropriate specialized agents
**Backstory**: Expert at understanding research paper search intents, metadata extraction, and determining optimal search strategies.

**Tools**:
- `analyze_query_structure`: Parse query for content vs metadata
- `extract_query_metadata`: Extract authors, venues, time ranges
- `identify_query_type`: Classify query type (BROAD, SPECIFIC_BY_TITLE, BY_AUTHOR, etc.)
- `extract_paper_title`: Extract potential paper titles from query
- `extract_author_names`: Extract and normalize author names
- `identify_research_domains`: Identify research fields/domains

**Inputs**:
```python
class QueryAnalyzerInput(BaseModel):
    query: str
    conversation_context: dict | None = None
```

**Outputs**:
```python
class AnalyzedQueryOutput(BaseModel):
    query_type: QueryType  # BROAD_BY_DESCRIPTION, SPECIFIC_BY_TITLE, etc.
    content: str  # Content-based search query
    authors: list[str]
    venues: list[str]
    time_range: TimeRange | None
    domains: DomainsIdentified
    matched_title: MatchedTitle | None
    extracted_properties: ExtractedProperties
```

**Tasks**:
1. Analyze query structure and intent
2. Extract metadata (authors, venues, dates)
3. Classify query type
4. Prepare routing information

---

#### SpecificPaperByTitleAgent

**Role**: Specific Paper Title Search Specialist
**Goal**: Find specific papers when user provides an exact or near-exact title
**Backstory**: Expert at matching paper titles against academic databases and handling title variations.

**Tools**:
- `s2_search_by_title`: Search Semantic Scholar by title
- `match_title_variants`: Handle title variations and abbreviations
- `verify_paper_metadata`: Confirm paper matches criteria (year, venue, authors)
- `get_paper_full_details`: Fetch complete paper information

**Source**: `agents/mabool/api/mabool/agents/specific_paper_by_title/specific_paper_by_title_agent.py`

**Inputs**:
```python
class SpecificPaperByTitleInput(BaseModel):
    matched_title: str
    matched_corpus_ids: list[str]
    time_range: ExtractedYearlyTimeRange | None = None
    venues: list[str]
    doc_collection: DocumentCollection
```

**Outputs**:
```python
class SpecificPaperByTitleOutput(BaseModel):
    doc_collection: DocumentCollection
    response_text: str
```

---

#### SpecificPaperByNameAgent

**Role**: Named Paper Search Specialist
**Goal**: Find papers by commonly used names (e.g., "BERT", "AlexNet")
**Backstory**: Expert at identifying papers by their popular names and matching to actual titles.

**Tools**:
- `search_paper_by_common_name`: Search using known paper names
- `extract_paper_name_from_context`: Extract paper names from query
- `verify_name_to_paper_match`: Confirm correct paper found
- `s2_search_combined`: Combined search by name + metadata

**Source**: `agents/mabool/api/mabool/agents/specific_paper_by_name/specific_paper_by_name_agent.py`

**Inputs**:
```python
class SpecificPaperByNameInput(BaseModel):
    user_input: str
    extracted_name: str
    extracted_content: str
    time_range: ExtractedYearlyTimeRange | None = None
    venues: list[str]
    authors: list[str]
    doc_collection: DocumentCollection
    domains: DomainsIdentified
```

---

#### SearchByAuthorsAgent

**Role**: Author-based Paper Search Specialist
**Goal**: Find papers by specific authors, optionally filtered by content
**Backstory**: Expert at author search, name disambiguation, and content relevance filtering.

**Tools**:
- `s2_search_by_author`: Search papers by author
- `normalize_author_names`: Handle name variations
- `filter_papers_by_content_relevance`: LLM-based relevance filtering
- `rank_author_papers`: Sort by relevance + metadata

**Source**: `agents/mabool/api/mabool/agents/search_by_authors/search_by_authors_agent.py`

**Inputs**:
```python
class SearchByAuthorsInput(BaseModel):
    authors: list[str]
    broad_or_specific: str
    user_content_input: str
    relevance_criteria: str
    time_range: ExtractedYearlyTimeRange | None = None
    venues: list[str]
    doc_collection: DocumentCollection
    domains: DomainsIdentified
```

---

#### BroadSearchAgent

**Role**: Comprehensive Research Search Specialist
**Goal**: Conduct exhaustive search for papers on a research topic
**Backstory**: Expert at multi-strategy search combining dense retrieval, keyword search, and citation analysis.

**Tools**:
- `dense_retrieval_search`: Vector-based semantic search
- `keyword_search`: Traditional keyword-based search
- `extract_relevant_snippets`: Get relevant text snippets
- `judge_relevance`: LLM-based relevance judgment
- `snowball_citations`: Expand via citations
- `rerank_results`: Cohere-based reranking

**Source**: `agents/mabool/api/mabool/agents/complex_search/broad_search.py`

**Inputs**:
```python
class BroadSearchInput(BaseModel):
    user_input: str
    content_query: str
    relevance_criteria: str
    anchor_doc_collection: DocumentCollection
    extracted_name: str | None
    recent_first: bool
    recent_last: bool
    central_first: bool
    central_last: bool
    suitable_for_by_citing: bool
    time_range: ExtractedYearlyTimeRange | None = None
    venues: list[str]
    authors: list[str]
    domains: DomainsIdentified
    doc_collection: DocumentCollection
```

---

#### FastBroadSearchAgent

**Role**: Quick Research Search Specialist
**Goal**: Rapidly find relevant papers on a research topic (~30 seconds)
**Backstory**: Expert at efficient search strategies, balancing speed and quality.

**Tools**: (Subset of BroadSearchAgent tools, optimized for speed)
- `dense_retrieval_search_fast`: Single-pass vector search
- `judge_relevance_batch`: Batch relevance judgment
- `quick_rerank`: Fast reranking

**Source**: `agents/mabool/api/mabool/agents/complex_search/fast_broad_search.py`

---

#### DenseSearchAgent

**Role**: Dense Retrieval Search Specialist
**Goal**: Perform vector-based semantic search across dense indices
**Backstory**: Expert at query reformulation and dense retrieval optimization.

**Tools**:
- `reformulate_dense_queries`: Create alternative query phrasings
- `search_dense_index`: Query vector databases
- `fetch_from_bifroest`: Internal dense search
- `fetch_from_vespa`: Public dense search

**Source**: `agents/mabool/api/mabool/agents/dense/dense_agent.py`

---

#### MetadataOnlyAgent

**Role**: Metadata-based Filter Specialist
**Goal**: Find papers using only metadata criteria (no content search)
**Backstory**: Expert at metadata-based filtering and aggregation.

**Tools**:
- `filter_by_venue`: Filter papers by publication venue
- `filter_by_time_range`: Filter by publication year
- `filter_by_domain`: Filter by research field
- `aggregate_metadata_filters`: Combine multiple filters

**Source**: `agents/mabool/api/mabool/agents/metadata_only/metadata_only_agent.py`

---

#### SnowballAgent

**Role**: Citation Snowball Search Specialist
**Goal**: Expand paper sets via citation networks
**Backstory**: Expert at citation analysis and iterative expansion.

**Tools**:
- `get_paper_citations`: Fetch papers citing a paper
- `get_paper_references`: Fetch papers referenced by a paper
- `filter_citations_by_relevance`: Relevance-based filtering
- `snowball_iteration`: Iterative expansion

**Source**: `agents/mabool/api/mabool/agents/snowball/snowball_agent.py`

---

#### LLMSuggestionAgent

**Role**: Fallback LLM Suggestion Specialist
**Goal**: Suggest papers when other search methods fail
**Backstory**: Expert at using LLM knowledge to suggest relevant papers.

**Tools**:
- `llm_suggest_papers`: Direct LLM paper suggestions
- `verify_suggested_papers`: Verify papers exist in S2

**Source**: `agents/mabool/api/mabool/agents/llm_suggestion/llm_suggestion_agent.py`

---

## Tool Specifications

### Tool Categories

1. **Semantic Scholar Tools**: Interact with S2 API
2. **Dense Retrieval Tools**: Vector search
3. **Document Processing Tools**: Filtering, ranking, relevance
4. **Metadata Tools**: Extract and manipulate metadata
5. **LLM Tools**: Query analysis, reformulation, suggestions

---

### 1. Semantic Scholar Tools

#### s2_search_by_title

```python
@tool("Search Semantic Scholar by paper title")
def s2_search_by_title(
    title: str,
    year_range: tuple[int, int] | None = None,
    limit: int = 10
) -> str:
    """
    Search for papers on Semantic Scholar by title.

    Args:
        title: The paper title to search for
        year_range: Optional (start_year, end_year) tuple to filter results
        limit: Maximum number of results to return (default: 10)

    Returns:
        JSON string of list of papers with basic metadata (title, authors, year, corpus_id)
    """
    # Implementation uses ai2i.dcollection
    factory = DocumentCollectionFactory()
    docs = await factory.from_s2_by_title(
        title=title,
        year_range=year_range,
        limit=limit
    )
    return json.dumps([doc.to_dict() for doc in docs])
```

#### s2_search_by_author

```python
@tool("Search Semantic Scholar by author names")
def s2_search_by_author(
    author_names: list[str],
    limit: int = 50
) -> str:
    """
    Search for papers by one or more authors on Semantic Scholar.

    Args:
        author_names: List of author names to search for
        limit: Maximum number of results per author (default: 50)

    Returns:
        JSON string of list of papers by these authors
    """
    # Implementation
    factory = DocumentCollectionFactory()
    docs = await factory.from_s2_by_author(
        authors=author_names,
        limit=limit
    )
    return json.dumps([doc.to_dict() for doc in docs])
```

#### s2_get_paper_details

```python
@tool("Get detailed paper information from Semantic Scholar")
def s2_get_paper_details(corpus_ids: list[str]) -> str:
    """
    Retrieve complete information for specific papers.

    Args:
        corpus_ids: List of Semantic Scholar corpus IDs

    Returns:
        JSON string of detailed paper information including abstract, citations, references
    """
    factory = DocumentCollectionFactory()
    docs = await factory.from_ids(corpus_ids)
    docs = await docs.with_fields([
        "title", "authors", "year", "abstract",
        "citation_count", "reference_count", "venue",
        "citations", "references"
    ])
    return json.dumps([doc.to_dict() for doc in docs])
```

#### s2_search_query

```python
@tool("General search on Semantic Scholar")
def s2_search_query(
    query: str,
    fields_of_study: list[str] | None = None,
    year_range: tuple[int, int] | None = None,
    venues: list[str] | None = None,
    limit: int = 100
) -> str:
    """
    Perform a general search query on Semantic Scholar.

    Args:
        query: Natural language search query
        fields_of_study: Optional list of research fields to filter by
        year_range: Optional (start_year, end_year) tuple
        venues: Optional list of publication venues
        limit: Maximum results (default: 100)

    Returns:
        JSON string of matching papers
    """
    # Implementation
    factory = DocumentCollectionFactory()
    docs = await factory.from_s2_search(
        query=query,
        fields_of_study=fields_of_study,
        year_range=year_range,
        venues=venues,
        limit=limit
    )
    return json.dumps([doc.to_dict() for doc in docs])
```

---

### 2. Dense Retrieval Tools

#### dense_search_bifroest

```python
@tool("Search using dense retrieval (Bifroest)")
def dense_search_bifroest(
    queries: list[str],
    dataset: str = "s2-corpus",
    top_k: int = 20,
    fields_of_study: list[str] | None = None
) -> str:
    """
    Perform dense vector search using Bifroest (internal dense index).

    Args:
        queries: List of search queries to use
        dataset: Dataset name (e.g., "s2-corpus", "cs-corpus")
        top_k: Number of results per query
        fields_of_study: Optional field filters

    Returns:
        JSON string of papers from dense retrieval
    """
    # Implementation uses ai2i.dcollection dense retrieval
    factory = DocumentCollectionFactory()
    dataset_obj = DenseDataset(name=dataset, provider="bifroest")
    docs = await factory.from_dense_retrieval(
        queries=queries,
        dataset=dataset_obj,
        top_k=top_k,
        fields_of_study=fields_of_study
    )
    return json.dumps([doc.to_dict() for doc in docs])
```

#### reformulate_search_query

```python
@tool("Reformulate search query for better retrieval")
def reformulate_search_query(
    original_query: str,
    num_variants: int = 3,
    example_papers: list[dict] | None = None
) -> str:
    """
    Generate alternative phrasings of a search query.

    Args:
        original_query: The original search query
        num_variants: Number of reformulated queries to generate
        example_papers: Optional example papers to guide reformulation

    Returns:
        JSON string of reformulated queries
    """
    # Implementation uses ai2i.chain LLM call
    from mabool.agents.dense.formulation import get_reformulated_dense_queries

    queries, _ = await get_reformulated_dense_queries(
        search_query=original_query,
        documents=example_papers or [],
        num_queries=num_variants
    )
    return json.dumps(queries)
```

---

### 3. Document Processing Tools

#### judge_paper_relevance

```python
@tool("Judge if papers are relevant to a query")
def judge_paper_relevance(
    papers: list[dict],
    query: str,
    relevance_criteria: str = ""
) -> str:
    """
    Use LLM to judge relevance of papers to a query.

    Args:
        papers: List of papers to judge (must have 'abstract' field)
        query: The search query or topic
        relevance_criteria: Optional additional criteria for relevance

    Returns:
        JSON string of papers with added 'relevance_score' and 'relevance_explanation'
    """
    # Implementation uses ai2i.chain for LLM-based relevance
    from mabool.agents.common.relevance_judgement_utils import judge_relevance

    results = []
    for paper in papers:
        relevance = await judge_relevance(
            content=paper.get("abstract", ""),
            query=query,
            criteria=relevance_criteria
        )
        results.append({
            **paper,
            "relevance_score": relevance.score,
            "relevance_explanation": relevance.explanation
        })

    return json.dumps(results)
```

#### filter_papers

```python
@tool("Filter papers by metadata criteria")
def filter_papers(
    papers: list[dict],
    year_range: tuple[int, int] | None = None,
    venues: list[str] | None = None,
    min_citation_count: int | None = None,
    authors: list[str] | None = None
) -> str:
    """
    Filter papers based on metadata criteria.

    Args:
        papers: List of papers to filter
        year_range: Optional (start_year, end_year) filter
        venues: Optional list of allowed venues
        min_citation_count: Optional minimum citation count
        authors: Optional list of authors (paper must have at least one)

    Returns:
        JSON string of filtered papers
    """
    filtered = papers

    if year_range:
        start, end = year_range
        filtered = [p for p in filtered if start <= p.get("year", 0) <= end]

    if venues:
        venues_lower = [v.lower() for v in venues]
        filtered = [p for p in filtered if p.get("venue", "").lower() in venues_lower]

    if min_citation_count:
        filtered = [p for p in filtered if p.get("citation_count", 0) >= min_citation_count]

    if authors:
        author_names = [a.lower() for a in authors]
        filtered = [
            p for p in filtered
            if any(a.lower() in author_names for a in p.get("authors", []))
        ]

    return json.dumps(filtered)
```

#### rank_papers

```python
@tool("Rank papers by multiple criteria")
def rank_papers(
    papers: list[dict],
    criteria: dict[str, float]
) -> str:
    """
    Rank papers using weighted criteria.

    Args:
        papers: List of papers to rank
        criteria: Dictionary of {criterion: weight}, e.g.,
                  {"relevance_score": 0.6, "citation_count": 0.3, "recency": 0.1}

    Returns:
        JSON string of papers sorted by computed score
    """
    # Implementation uses ai2i.dcollection sorting utilities
    from mabool.agents.common.sorting import sorted_docs_by_preferences, SortPreferences

    # Convert to DocumentCollection
    # Apply sorting
    # Return sorted papers

    return json.dumps(sorted_papers)
```

#### rerank_papers_cohere

```python
@tool("Rerank papers using Cohere reranking API")
def rerank_papers_cohere(
    papers: list[dict],
    query: str,
    top_n: int = 20
) -> str:
    """
    Rerank papers using Cohere's reranking model.

    Args:
        papers: List of papers with 'abstract' or 'title' fields
        query: The query to rank against
        top_n: Return top N papers after reranking

    Returns:
        JSON string of reranked papers
    """
    # Implementation uses Cohere API via mabool.external_api
    from mabool.external_api.rerank.cohere import rerank_with_cohere

    reranked = await rerank_with_cohere(
        query=query,
        documents=papers,
        top_n=top_n
    )

    return json.dumps(reranked)
```

---

### 4. Metadata Tools

#### extract_query_metadata

```python
@tool("Extract metadata from a natural language query")
def extract_query_metadata(query: str) -> str:
    """
    Extract structured metadata from a search query.

    Args:
        query: Natural language paper search query

    Returns:
        JSON with extracted: authors, venues, year_range, domains, properties
    """
    # Implementation uses QueryAnalyzer logic
    from mabool.agents.query_analyzer.query_analyzer import extract_metadata_from_query

    metadata = await extract_metadata_from_query(query)

    return json.dumps({
        "authors": metadata.authors,
        "venues": metadata.venues,
        "time_range": metadata.time_range,
        "domains": metadata.domains,
        "properties": metadata.extracted_properties
    })
```

#### identify_query_type

```python
@tool("Identify the type of paper search query")
def identify_query_type(query: str, metadata: dict) -> str:
    """
    Classify the query type for routing to appropriate agents.

    Args:
        query: Natural language query
        metadata: Extracted metadata from the query

    Returns:
        JSON with query_type: one of BROAD_BY_DESCRIPTION, SPECIFIC_BY_TITLE,
        SPECIFIC_BY_NAME, BY_AUTHOR, METADATA_ONLY, etc.
    """
    # Implementation
    from mabool.agents.query_analyzer.query_analyzer import classify_query_type

    query_type = await classify_query_type(query, metadata)

    return json.dumps({"query_type": query_type})
```

---

### 5. LLM Tools

#### llm_suggest_papers

```python
@tool("Ask LLM to suggest relevant papers")
def llm_suggest_papers(
    query: str,
    domains: list[str] | None = None,
    num_suggestions: int = 5
) -> str:
    """
    Use LLM's knowledge to suggest papers relevant to a query.
    Fallback method when search methods fail.

    Args:
        query: Research topic or question
        domains: Optional research domains to focus on
        num_suggestions: Number of papers to suggest

    Returns:
        JSON string of suggested papers with titles and brief descriptions
    """
    # Implementation
    from mabool.agents.llm_suggestion.llm_suggestion_agent import get_llm_suggested_papers

    papers = await get_llm_suggested_papers(
        query=query,
        domains=domains,
        n_suggestions=num_suggestions
    )

    return json.dumps([p.to_dict() for p in papers])
```

---

## Workflow Designs

### Query Flow Architecture

```
User Query
    ↓
[QueryAnalyzerAgent]
    ↓
Analyze & Route
    ↓
    ├─→ [SPECIFIC_BY_TITLE] → SpecificPaperByTitleAgent → Results
    ├─→ [SPECIFIC_BY_NAME] → SpecificPaperByNameAgent → Results
    ├─→ [BY_AUTHOR] → SearchByAuthorsAgent → Results
    ├─→ [BROAD_BY_DESCRIPTION] → BroadSearchAgent/FastBroadSearchAgent → Results
    └─→ [METADATA_ONLY] → MetadataOnlyAgent → Results
        ↓
    Rank & Sort
        ↓
    Return to User
```

### Workflow Implementation Approaches

#### Approach 1: Sequential with Dynamic Task Creation

```python
def create_paper_finder_crew():
    # Step 1: Query Analysis (always runs)
    query_analysis_task = Task(
        description="Analyze the query: {query}",
        expected_output="Query analysis with routing decision",
        agent=query_analyzer_agent,
        output_json=AnalyzedQueryOutput
    )

    # Step 2: Create crew with callback for dynamic routing
    crew = Crew(
        agents=[
            query_analyzer_agent,
            specific_title_agent,
            specific_name_agent,
            author_search_agent,
            broad_search_agent,
            fast_broad_search_agent,
            metadata_only_agent
        ],
        tasks=[query_analysis_task],
        process=Process.sequential
    )

    # After query_analysis_task completes, dynamically add appropriate task
    def on_task_complete(task_output):
        analysis = task_output.json

        if analysis.query_type == "SPECIFIC_BY_TITLE":
            crew.tasks.append(create_specific_title_task(analysis))
        elif analysis.query_type == "BROAD_BY_DESCRIPTION":
            crew.tasks.append(create_broad_search_task(analysis))
        # ... etc

    return crew
```

**Pros**: Flexible, efficient (only runs needed tasks)
**Cons**: More complex implementation

#### Approach 2: Hierarchical with Manager Agent

```python
def create_paper_finder_crew():
    # Manager agent makes routing decisions
    manager_agent = Agent(
        role="Paper Search Coordinator",
        goal="Route queries to appropriate specialist agents",
        backstory="Expert coordinator...",
        allow_delegation=True
    )

    # Create single high-level task
    search_task = Task(
        description="""
            For the query: {query}

            1. Analyze the query to understand the search intent
            2. Route to the appropriate specialist agent
            3. Ensure results are ranked and formatted correctly
        """,
        expected_output="Ranked list of relevant papers",
        agent=manager_agent
    )

    crew = Crew(
        agents=[
            manager_agent,
            query_analyzer_agent,
            specific_title_agent,
            # ... all specialist agents
        ],
        tasks=[search_task],
        process=Process.hierarchical,
        manager_agent=manager_agent
    )

    return crew
```

**Pros**: Simpler setup, CrewAI handles routing
**Cons**: Manager overhead, less control

#### Approach 3: Hybrid (Recommended for Learning)

```python
def create_paper_finder_crew():
    """
    Hybrid approach:
    - Use QueryAnalyzerAgent to determine route (sequential)
    - Use hierarchical for complex multi-step workflows
    """

    # Stage 1: Analysis
    query_analysis_task = Task(
        description="Analyze query: {query}",
        agent=query_analyzer_agent,
        output_json=AnalyzedQueryOutput
    )

    # Stage 2: Execution (based on analysis result)
    # This will be determined programmatically

    crew = PaperFinderCrew(
        agents=[...],
        process=Process.sequential  # Or hierarchical for complex cases
    )

    return crew

class PaperFinderCrew:
    """Custom crew class that handles routing logic"""

    def __init__(self, agents, process):
        self.agents_map = {agent.role: agent for agent in agents}
        self.process = process

    async def kickoff(self, inputs: dict):
        # Step 1: Analyze
        analysis_crew = Crew(
            agents=[self.agents_map["Query Analyzer"]],
            tasks=[create_analysis_task(inputs["query"])],
            process=Process.sequential
        )
        analysis_result = analysis_crew.kickoff(inputs)

        # Step 2: Route based on analysis
        query_type = analysis_result.query_type

        # Step 3: Execute appropriate workflow
        if query_type == "SPECIFIC_BY_TITLE":
            return await self._run_specific_title_workflow(analysis_result)
        elif query_type == "BROAD_BY_DESCRIPTION":
            return await self._run_broad_search_workflow(analysis_result)
        # ... etc

    async def _run_specific_title_workflow(self, analysis):
        crew = Crew(
            agents=[self.agents_map["Specific Title Specialist"]],
            tasks=[create_specific_title_task(analysis)],
            process=Process.sequential
        )
        return crew.kickoff({"analysis": analysis})
```

**Pros**: Best of both worlds, good for learning CrewAI patterns
**Cons**: More code, custom routing logic

**Recommendation**: Start with Approach 3 for learning, can refine to Approach 2 later.

---

## State Management Strategy

### Current State Requirements (from Mabool)

1. **Document Collections**: Papers found so far
2. **Checkpoint State**: Results at each stage
3. **Session Context**: Multi-turn conversation state
4. **Exclusion Lists**: Already-seen corpus IDs
5. **Intermediate Results**: Query analysis, reformulations, etc.

### Proposed State Management

#### Level 1: Task Context (Immediate State)

Pass state between tasks via context:

```python
task1 = Task(
    description="Analyze query",
    agent=analyzer_agent,
    output_json=AnalysisOutput
)

task2 = Task(
    description="Search based on analysis: {analysis}",
    agent=search_agent,
    context=[task1],  # task1 output available as {analysis}
    output_json=SearchOutput
)
```

#### Level 2: CrewAI Memory (Agent Memory)

Use CrewAI's built-in memory for agent-level state:

```python
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # Enable memory
    # Memory stores:
    # - Recent task outputs (short-term)
    # - Past successful searches (long-term)
    # - Entities mentioned (entity memory)
)
```

#### Level 3: Custom State Store (Complex State)

For complex state like document collections:

```python
class StateManager:
    """Manages complex state across crew execution"""

    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=3600)

    def save_state(self, session_id: str, state: dict):
        self.cache[session_id] = {
            "doc_collection": state.get("documents", []),
            "excluded_ids": state.get("excluded", set()),
            "checkpoint": state.get("checkpoint"),
            "metadata": state.get("metadata", {})
        }

    def get_state(self, session_id: str) -> dict:
        return self.cache.get(session_id, {})

# Usage in crew
state_manager = StateManager()

def run_crew_with_state(session_id: str, query: str):
    # Load state
    state = state_manager.get_state(session_id)

    # Run crew with state in inputs
    result = crew.kickoff({
        "query": query,
        "existing_documents": state.get("doc_collection", []),
        "excluded_ids": state.get("excluded_ids", set())
    })

    # Save updated state
    state_manager.save_state(session_id, {
        "documents": result.documents,
        "excluded": result.excluded_ids,
        "checkpoint": result.final_state
    })

    return result
```

#### Recommended Hybrid Approach

```python
class StatefulPaperFinderCrew:
    """
    Combines all three state management levels:
    1. Task context for immediate task-to-task data
    2. CrewAI memory for agent learning
    3. Custom state store for document collections and complex state
    """

    def __init__(self):
        self.state_manager = StateManager()

        self.crew = Crew(
            agents=[...],
            tasks=[...],
            memory=True,  # Enable CrewAI memory
            process=Process.sequential
        )

    async def execute(self, session_id: str, query: str, operation_mode: str = "fast"):
        # Get existing state
        state = self.state_manager.get_state(session_id)

        # Prepare inputs with state
        inputs = {
            "query": query,
            "operation_mode": operation_mode,
            "session_id": session_id,
            # Include state as context
            "existing_documents": json.dumps(state.get("doc_collection", [])),
            "excluded_corpus_ids": json.dumps(list(state.get("excluded_ids", set())))
        }

        # Execute crew (uses CrewAI memory + task context automatically)
        result = self.crew.kickoff(inputs=inputs)

        # Update state store with results
        self.state_manager.save_state(session_id, {
            "doc_collection": result.documents,
            "excluded_ids": set(result.excluded_corpus_ids),
            "checkpoint": result.checkpoint,
            "last_query": query,
            "last_analysis": result.analysis
        })

        return result
```

---

## API Integration

### Side-by-Side Implementation

#### Directory Structure

```
agents/
├── mabool/              # Existing (preserved)
│   └── api/
│       ├── mabool/
│       └── pyproject.toml
└── crewai/              # New implementation
    └── api/
        ├── paperfinder_crew/
        │   ├── __init__.py
        │   ├── agents/        # Agent definitions
        │   ├── tasks/         # Task definitions
        │   ├── tools/         # Tool implementations
        │   ├── crews/         # Crew compositions
        │   ├── state/         # State management
        │   └── config/        # CrewAI configs
        ├── tests/
        └── pyproject.toml
```

#### FastAPI Routes

```python
# agents/crewai/api/paperfinder_crew/api/routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["crewai"], prefix="/api/v3/rounds")

class CrewAIRoundRequest(BaseModel):
    paper_description: str
    operation_mode: str = "fast"
    session_id: str | None = None
    use_cache: bool = False

@router.post("")
async def start_crewai_round(request: CrewAIRoundRequest):
    """Execute paper search using CrewAI implementation"""

    from paperfinder_crew.crews.paper_finder_crew import StatefulPaperFinderCrew

    # Initialize crew
    crew = StatefulPaperFinderCrew()

    # Generate or use provided session ID
    session_id = request.session_id or generate_session_id()

    try:
        # Execute
        result = await crew.execute(
            session_id=session_id,
            query=request.paper_description,
            operation_mode=request.operation_mode
        )

        return {
            "status": "success",
            "session_id": session_id,
            "documents": result.documents,
            "response_text": result.response_text,
            "analysis": result.analysis,
            "metadata": {
                "implementation": "crewai",
                "operation_mode": request.operation_mode
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CrewAI execution failed: {str(e)}"
        )
```

#### Feature Flag Integration

```python
# agents/crewai/api/paperfinder_crew/api/unified_routes.py

from fastapi import APIRouter, Request
import os

router = APIRouter(tags=["unified"], prefix="/api/rounds")

USE_CREWAI = os.getenv("USE_CREWAI", "false").lower() == "true"

@router.post("")
async def unified_round_endpoint(request: RoundRequest):
    """
    Unified endpoint that routes to either mabool or crewai
    based on configuration or request header.
    """

    # Check for override in request header
    use_crewai = request.headers.get("X-Use-CrewAI", str(USE_CREWAI)).lower() == "true"

    if use_crewai:
        from paperfinder_crew.api.routes import start_crewai_round
        return await start_crewai_round(request)
    else:
        from mabool.api.round_v2_routes import start_round
        return await start_round(request)
```

#### App Composition

```python
# agents/crewai/api/paperfinder_crew/api/app.py

from fastapi import FastAPI
from mabool.api.app import app as mabool_app
from paperfinder_crew.api.routes import router as crewai_router
from paperfinder_crew.api.unified_routes import router as unified_router

# Create new app that includes both
app = FastAPI(title="Paper Finder - Unified API")

# Include mabool routes (existing)
app.include_router(mabool_app.router)

# Include new CrewAI routes
app.include_router(crewai_router)

# Include unified route
app.include_router(unified_router)

# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "implementations": {
            "mabool": "available",
            "crewai": "available"
        }
    }
```

---

## Testing Strategy

### Testing Levels

#### 1. Unit Tests (Tools)

Test individual tools in isolation:

```python
# tests/tools/test_s2_tools.py

import pytest
from paperfinder_crew.tools.semantic_scholar import s2_search_by_title

@pytest.mark.asyncio
async def test_s2_search_by_title():
    result = await s2_search_by_title(
        title="attention is all you need",
        limit=5
    )

    papers = json.loads(result)
    assert len(papers) > 0
    assert any("attention" in p["title"].lower() for p in papers)
    assert all("corpus_id" in p for p in papers)

@pytest.mark.asyncio
async def test_s2_search_by_title_with_year_filter():
    result = await s2_search_by_title(
        title="bert",
        year_range=(2018, 2020),
        limit=10
    )

    papers = json.loads(result)
    assert all(2018 <= p["year"] <= 2020 for p in papers)
```

#### 2. Unit Tests (Agents)

Test agents with mock tools:

```python
# tests/agents/test_query_analyzer.py

import pytest
from unittest.mock import Mock, patch
from crewai import Agent, Task, Crew
from paperfinder_crew.agents.query_analyzer import create_query_analyzer_agent

@pytest.mark.asyncio
async def test_query_analyzer_broad_query():
    agent = create_query_analyzer_agent()

    task = Task(
        description="Analyze: papers about transformer models",
        expected_output="Query analysis",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential)
    result = crew.kickoff(inputs={"query": "papers about transformer models"})

    assert result.query_type == "BROAD_BY_DESCRIPTION"
    assert "transformer" in result.content.lower()

@pytest.mark.asyncio
async def test_query_analyzer_author_query():
    agent = create_query_analyzer_agent()

    result = await analyze_query("papers by Yoshua Bengio")

    assert result.query_type == "BY_AUTHOR"
    assert "Yoshua Bengio" in result.authors
```

#### 3. Integration Tests (Workflows)

Test complete workflows:

```python
# tests/integration/test_workflows.py

import pytest
from paperfinder_crew.crews.paper_finder_crew import StatefulPaperFinderCrew

@pytest.mark.asyncio
async def test_specific_title_workflow():
    crew = StatefulPaperFinderCrew()

    result = await crew.execute(
        session_id="test-123",
        query="find the paper 'attention is all you need'",
        operation_mode="fast"
    )

    assert result.status == "success"
    assert len(result.documents) > 0
    assert any("attention" in doc["title"].lower() for doc in result.documents)

@pytest.mark.asyncio
async def test_broad_search_workflow():
    crew = StatefulPaperFinderCrew()

    result = await crew.execute(
        session_id="test-456",
        query="recent papers on large language models",
        operation_mode="fast"
    )

    assert result.status == "success"
    assert len(result.documents) >= 10
    # Check that papers are recent
    assert most papers have year >= 2020
```

#### 4. Comparison Tests (Mabool vs CrewAI)

```python
# tests/comparison/test_mabool_vs_crewai.py

import pytest
from mabool.api.round_v2_routes import run_round_with_cache as mabool_run
from paperfinder_crew.crews.paper_finder_crew import StatefulPaperFinderCrew

@pytest.mark.asyncio
async def test_results_similarity():
    """Compare results from both implementations"""

    query = "papers about neural machine translation"

    # Run mabool
    mabool_result = await mabool_run(
        paper_description=query,
        anchor_corpus_ids=[],
        operation_mode="fast"
    )

    # Run crewai
    crew = StatefulPaperFinderCrew()
    crewai_result = await crew.execute(
        session_id="comparison-test",
        query=query,
        operation_mode="fast"
    )

    # Compare
    mabool_ids = {doc["corpus_id"] for doc in mabool_result["documents"]}
    crewai_ids = {doc["corpus_id"] for doc in crewai_result.documents}

    # Expect significant overlap (>50%)
    overlap = len(mabool_ids & crewai_ids)
    overlap_ratio = overlap / max(len(mabool_ids), len(crewai_ids))

    assert overlap_ratio > 0.5, f"Only {overlap_ratio*100}% overlap between implementations"
```

#### 5. Performance Tests

```python
# tests/performance/test_latency.py

import pytest
import time
from paperfinder_crew.crews.paper_finder_crew import StatefulPaperFinderCrew

@pytest.mark.asyncio
async def test_fast_mode_latency():
    crew = StatefulPaperFinderCrew()

    start = time.time()
    result = await crew.execute(
        session_id="perf-test",
        query="papers on computer vision",
        operation_mode="fast"
    )
    duration = time.time() - start

    # Fast mode should complete in < 60 seconds
    assert duration < 60, f"Fast mode took {duration}s, expected < 60s"

@pytest.mark.asyncio
async def test_diligent_mode_latency():
    crew = StatefulPaperFinderCrew()

    start = time.time()
    result = await crew.execute(
        session_id="perf-test-2",
        query="papers on computer vision",
        operation_mode="diligent"
    )
    duration = time.time() - start

    # Diligent mode should complete in < 300 seconds (5 min)
    assert duration < 300, f"Diligent mode took {duration}s, expected < 300s"
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goal**: Set up infrastructure and implement first tools

**Tasks**:
1. Create directory structure
2. Set up pyproject.toml with CrewAI dependencies
3. Implement 5-10 core tools:
   - s2_search_by_title
   - s2_search_by_author
   - s2_get_paper_details
   - filter_papers
   - judge_paper_relevance
4. Write unit tests for tools
5. Create tool documentation

**Success Criteria**:
- All tools have tests
- Tools successfully use ai2i libraries
- Documentation complete

---

### Phase 2: Simple Agents (Week 3-4)

**Goal**: Implement 2-3 simple agents

**Target Agents**:
1. SpecificPaperByTitleAgent
2. SpecificPaperByNameAgent
3. MetadataOnlyAgent

**Tasks**:
1. Define agent roles, goals, backstories
2. Assign tools to agents
3. Create tasks for each agent
4. Test agents individually
5. Create simple crews for testing

**Success Criteria**:
- Agents can execute tasks successfully
- Unit tests pass
- Can find specific papers by title/name

---

### Phase 3: Query Analyzer (Week 5)

**Goal**: Implement query analysis and routing

**Tasks**:
1. Implement QueryAnalyzerAgent
2. Create query analysis tools
3. Test query classification
4. Implement routing logic

**Success Criteria**:
- Correctly classifies query types
- Routes to appropriate workflows
- Handles edge cases

---

### Phase 4: Complex Agents (Week 6-7)

**Goal**: Implement remaining complex agents

**Target Agents**:
1. BroadSearchAgent
2. FastBroadSearchAgent
3. SearchByAuthorsAgent
4. DenseSearchAgent
5. SnowballAgent

**Tasks**:
1. Implement agents
2. Create complex workflows
3. Test multi-step processes
4. Integrate with QueryAnalyzer

**Success Criteria**:
- All agents operational
- Complex workflows function correctly
- Integration tests pass

---

### Phase 5: Crew Orchestration (Week 8)

**Goal**: Create complete PaperFinderCrew

**Tasks**:
1. Implement StatefulPaperFinderCrew
2. Create routing logic
3. Implement state management
4. Test end-to-end workflows

**Success Criteria**:
- Complete workflows execute successfully
- State management works
- Comparable results to mabool

---

### Phase 6: API Integration (Week 9)

**Goal**: Expose CrewAI via FastAPI

**Tasks**:
1. Create FastAPI routes
2. Implement feature flags
3. Create unified endpoint
4. Test API thoroughly

**Success Criteria**:
- API endpoints work
- Feature flags function
- Both implementations accessible

---

### Phase 7: Testing & Refinement (Week 10)

**Goal**: Comprehensive testing and comparison

**Tasks**:
1. Run comparison tests
2. Performance benchmarking
3. Fix issues
4. Optimize slow operations

**Success Criteria**:
- Comparison tests show >50% result overlap
- Performance meets requirements
- All tests pass

---

### Phase 8: Documentation (Week 11)

**Goal**: Complete all documentation

**Tasks**:
1. Update this design doc
2. Create user guide
3. Write migration guide
4. Create examples and tutorials

**Success Criteria**:
- Complete documentation
- Examples work
- Ready for use

---

## Open Questions & Investigation Areas

### 1. CrewAI Memory Capabilities

**Question**: Can CrewAI memory handle our state requirements?

**Investigation Needed**:
- Test memory with large document collections
- Evaluate memory retrieval accuracy
- Test memory persistence across sessions

**Timeline**: Phase 5 (Week 8)

---

### 2. Performance Impact

**Question**: How does CrewAI overhead compare to custom Operative pattern?

**Investigation Needed**:
- Benchmark individual agent execution
- Measure crew orchestration overhead
- Compare total latency

**Timeline**: Phase 7 (Week 10)

---

### 3. Tool Error Handling

**Question**: How should tools handle errors and retry logic?

**Options**:
A. Tools handle errors internally, return error messages in JSON
B. Tools raise exceptions, let CrewAI handle
C. Hybrid: Tools retry once, then raise exception

**Investigation Needed**:
- Test CrewAI error handling behavior
- Determine best practices

**Timeline**: Phase 2 (Week 3-4)

---

### 4. LLM Cost Management

**Question**: How to optimize LLM calls to control costs?

**Strategies**:
- Cache tool results
- Use cheaper models for simple tasks
- Batch similar operations
- Limit agent verbosity

**Investigation Needed**:
- Measure token usage per workflow
- Compare costs between implementations

**Timeline**: Phase 7 (Week 10)

---

## Risk Mitigation

### Risk 1: CrewAI Learning Curve

**Risk**: CrewAI behavior differs from expectations

**Mitigation**:
- Start with simple agents
- Incremental complexity
- Extensive testing at each phase
- Keep mabool as reference

---

### Risk 2: Performance Degradation

**Risk**: CrewAI implementation is slower than mabool

**Mitigation**:
- Performance tests early (Phase 2)
- Optimize critical paths
- Consider hybrid approaches
- Profile and optimize

---

### Risk 3: State Management Complexity

**Risk**: State management doesn't work as planned

**Mitigation**:
- Multiple state management options designed
- Test state management early (Phase 5)
- Fallback to custom state store
- Document limitations

---

### Risk 4: Tool Granularity Issues

**Risk**: Fine-grained tools are too numerous or confusing

**Mitigation**:
- Group related tools
- Clear naming conventions
- Good documentation
- Can consolidate later if needed

---

## Success Metrics

### Functional Metrics

- ✅ All query types handled correctly
- ✅ >90% test coverage
- ✅ >50% result overlap with mabool on test queries
- ✅ All agents operational

### Performance Metrics

- ✅ Fast mode: < 60 seconds
- ✅ Diligent mode: < 300 seconds
- ✅ <20% latency increase vs mabool

### Learning Metrics

- ✅ Understand CrewAI agent patterns
- ✅ Understand CrewAI tool system
- ✅ Understand CrewAI orchestration
- ✅ Understand CrewAI memory system

---

## Appendix

### A. Mabool Agent File Locations

```
agents/mabool/api/mabool/agents/
├── paper_finder/paper_finder_agent.py        # Main orchestrator
├── query_analyzer/query_analyzer.py          # Query analysis
├── specific_paper_by_title/                  # Title search
├── specific_paper_by_name/                   # Name search
├── search_by_authors/                        # Author search
├── broad_search_by_keyword/                  # Keyword search
├── complex_search/broad_search.py            # Comprehensive search
├── complex_search/fast_broad_search.py       # Fast search
├── dense/dense_agent.py                      # Dense retrieval
├── metadata_only/metadata_only_agent.py      # Metadata filtering
├── snowball/snowball_agent.py                # Citation expansion
└── llm_suggestion/llm_suggestion_agent.py    # LLM fallback
```

### B. Key Libraries and Their Roles

| Library | Purpose | Keep/Replace |
|---------|---------|--------------|
| ai2i.dcollection | Document collection management | KEEP - wrap in tools |
| ai2i.chain | LLM interaction wrapper | KEEP - use in tools |
| ai2i.di | Dependency injection | KEEP - for tools/config |
| ai2i.config | Configuration management | KEEP |
| Operative pattern | Agent orchestration | REPLACE with CrewAI |
| LangChain | LLM framework | KEEP (CrewAI uses it) |

### C. External API Dependencies

- Semantic Scholar API (S2_API_KEY)
- OpenAI API (OPENAI_API_KEY)
- Google/Gemini API (GOOGLE_API_KEY)
- Cohere API (COHERE_API_KEY)

### D. Glossary

- **Operative**: Custom agent pattern in mabool
- **DocumentCollection**: ai2i.dcollection data structure for papers
- **CorpusId**: Semantic Scholar paper ID
- **Dense Retrieval**: Vector-based semantic search
- **Bifroest**: Internal AI2 dense search service
- **Vespa**: Public dense search platform
- **Snowball**: Citation network expansion technique

---

**Document Status**: Living document, update as we learn and progress
**Next Review**: After Phase 1 completion
**Feedback**: Document learnings and decisions in SESSION.md
