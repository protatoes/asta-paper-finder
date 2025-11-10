# Mabool Agent Analysis Report - Phase 2 Review

**Date**: 2025-11-08
**Phase**: Phase 2 - Step 1 (Mabool Implementation Review)
**Purpose**: Detailed analysis of mabool agent implementations to inform CrewAI migration

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [The Operative Pattern](#the-operative-pattern)
4. [Orchestration & Routing](#orchestration--routing)
5. [Agent Deep Dives](#agent-deep-dives)
6. [Integration Patterns](#integration-patterns)
7. [Key Takeaways for CrewAI Migration](#key-takeaways-for-crewai-migration)

---

## Executive Summary

### What We Analyzed

**Files Reviewed**:
- `specific_paper_by_title_agent.py` (143 lines)
- `specific_paper_by_title_prompts.py` (34 lines)
- `specific_paper_by_name_agent.py` (487 lines)
- `metadata_only_agent.py` (87 lines)
- `paper_finder_agent.py` (560 lines - main orchestrator)
- `query_analyzer.py` (300+ lines)

### Key Findings

1. **Architecture Pattern**: Mabool uses a custom "Operative" pattern for agent orchestration
2. **Centralized Routing**: PaperFinderAgent acts as the main orchestrator/router
3. **Query Analysis First**: All queries go through QueryAnalyzer before routing to specialist agents
4. **Rich Scoring Systems**: Agents use sophisticated multi-signal scoring for result ranking
5. **Heavy LLM Usage**: Extensive use of LLMs for extraction and classification
6. **Graceful Degradation**: Robust error handling with fallback strategies

### Complexity Assessment

| Agent | Complexity | LoC | Key Challenge |
|-------|------------|-----|---------------|
| SpecificPaperByTitleAgent | Low | 143 | Simple title matching with LLM extraction |
| SpecificPaperByNameAgent | High | 487 | Complex multi-signal scoring system |
| MetadataOnlyAgent | Low | 87 | Simple metadata filtering |
| PaperFinderAgent (Orchestrator) | Very High | 560 | Complex routing and state management |
| QueryAnalyzer | Very High | 300+ | Multi-step extraction and classification |

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Query Input                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              QueryAnalyzer (decompose_and_analyze_query)     │
│  • Extracts: content, authors, venues, time_range, domains  │
│  • Classifies: SPECIFIC_BY_TITLE, SPECIFIC_BY_NAME,        │
│                BY_AUTHOR, BROAD_BY_DESCRIPTION,             │
│                METADATA_ONLY_NO_AUTHOR                      │
│  • Determines: broad vs specific                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              PaperFinderAgent (Main Orchestrator)            │
│                                                              │
│  register():                                                 │
│    • broad_search_agent                                     │
│    • fast_broad_search_agent                                │
│    • broad_search_by_keyword                                │
│    • specific_paper_by_title    ← Phase 2 Target           │
│    • search_by_authors                                      │
│    • specific_paper_by_name     ← Phase 2 Target           │
│    • metadata_only_agent         ← Phase 2 Target           │
│    • metadata_planner_agent                                 │
│                                                              │
│  handle_operation():                                         │
│    1. Analyze query                                         │
│    2. Create PlanContext                                    │
│    3. Route to appropriate agent                            │
│    4. Sort and enrich results                               │
│    5. Generate response                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────┴───────────┐
         │                       │
    ┌────▼────┐           ┌─────▼──────┐
    │ Agent 1 │    ...    │  Agent N   │
    │         │           │            │
    │ Tools   │           │   Tools    │
    └────┬────┘           └─────┬──────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  DocumentCollection   │
         │  (Results)            │
         └───────────────────────┘
```

### Data Flow

```
User Query
    ↓
[Query Analysis] → ExtractedFields + QueryType
    ↓
[Route Decision] → Based on QueryType
    ↓
    ├─→ SPECIFIC_BY_TITLE → SpecificPaperByTitleAgent
    ├─→ SPECIFIC_BY_NAME → SpecificPaperByNameAgent
    ├─→ BY_AUTHOR → SearchByAuthorsAgent
    ├─→ BROAD_BY_DESCRIPTION → BroadSearchAgent / FastBroadSearchAgent
    └─→ METADATA_ONLY_NO_AUTHOR → MetadataOnlyAgent
    ↓
[Agent Execution] → DocumentCollection with scores
    ↓
[Sorting & Enrichment] → Add fields, sort by preferences
    ↓
[Response Generation] → ExplainedAgentOutput
    ↓
User Results
```

---

## The Operative Pattern

### Pattern Definition

The Operative pattern is a custom abstraction for agent-like components in mabool:

```python
class Operative[INPUT, OUTPUT, STATE]:
    """
    Custom agent pattern with:
    - Typed inputs/outputs/state
    - Nested agent registration
    - Standardized response types
    """

    def register(self) -> None:
        """Register nested operatives (sub-agents)"""
        # Example from PaperFinderAgent:
        self.specific_paper_by_title = self.init_operative(
            "specific_paper_by_title_agent",
            SpecificPaperByTitleAgent
        )

    async def handle_operation(
        self,
        state: STATE | None,
        inputs: INPUT
    ) -> tuple[STATE | None, OperativeResponse[OUTPUT]]:
        """
        Core logic - returns (new_state, response)

        Response types:
        - CompleteResponse: Success with data
        - PartialResponse: Success with data + error/warning
        - VoidResponse: Failure with error
        """
        pass
```

### Response Types

```python
# Success
CompleteResponse(data=AgentOutput(...))

# Partial success (has results but with issues)
PartialResponse(
    data=AgentOutput(...),
    error=AgentError(type="...", message="...")
)

# Failure
VoidResponse(
    error=AgentError(type="...", message="...")
)
```

### State Management

- **STATE**: Optional state object passed between calls (for stateful agents)
- **AgentState**: Common state type, often contains `checkpoint: DocumentCollection`
- **Stateless Agents**: Most agents are stateless (STATE = None)

### Key Differences from CrewAI

| Aspect | Mabool Operative | CrewAI Agent |
|--------|------------------|--------------|
| Pattern | Custom class inheritance | Framework-provided Agent class |
| Registration | Manual `register()` with `init_operative()` | Crew composition |
| State | Explicit state parameter | Memory/context (built-in) |
| Responses | Typed response classes | Task outputs |
| Nesting | Built-in with `register()` | Crew hierarchies |
| Invocation | `await self.agent(input)` | Task delegation |

---

## Orchestration & Routing

### PaperFinderAgent: The Main Orchestrator

**Role**: Main entry point that routes queries to appropriate specialist agents

**Location**: `agents/mabool/api/mabool/agents/paper_finder/paper_finder_agent.py`

#### Registration Phase

```python
def register(self) -> None:
    """Initialize all specialist agents"""
    self.broad_search_agent = self.init_operative("broad_search_agent", BroadSearchAgent)
    self.fast_broad_search_agent = self.init_operative("fast_broad_search_agent", FastBroadSearchAgent)
    self.broad_search_by_keyword = self.init_operative("broad_search_by_keyword_agent", BroadSearchByKeywordAgent)

    # Phase 2 targets:
    self.specific_paper_by_title = self.init_operative("specific_paper_by_title_agent", SpecificPaperByTitleAgent)
    self.specific_paper_by_name = self.init_operative("specific_paper_by_name_agent", SpecificPaperByNameAgent)
    self.metadata_only_agent = self.init_operative("metadata_only_agent", MetadataOnlySearchAgent)

    self.search_by_authors = self.init_operative("search_by_authors_agent", SearchByAuthorsAgent)
    self.metadata_planner_agent = self.init_operative("metadata_planner_agent", MetadataPlannerAgent)
```

**Pattern**: All specialist agents are registered as nested operatives

#### Routing Logic

```python
async def handle_operation(
    self, state: PaperFinderState | None, inputs: PaperFinderInput
) -> tuple[PaperFinderState | None, OperativeResponse[PaperFinderOutput]]:

    # Step 1: Analyze query
    query_analysis_result = await decompose_and_analyze_query_restricted(inputs.query)

    # Step 2: Route based on analysis
    match query_analysis_result:
        case QueryAnalysisSuccess(analyzed_query=analyzed_query, specifications=Specifications()):
            # Special case: Metadata-only with specifications
            if specifications.is_non_trivial_metadata_only():
                docs, text = await self.run_metadata_planner_on_specifications(...)
            else:
                # Normal case: Create PlanContext and route
                anchor_docs = await enrich_anchor_documents(analyzed_query, inputs)
                docs, text = await self.run_paper_finder_on_analyzed_query(
                    inputs, analyzed_query, anchor_docs
                )

        case QueryAnalysisRefusal(...):
            # Handle refusals (ask user to clarify or soft reject)
            ...

        case QueryAnalysisPartialSuccess(...):
            # Partial success - fall back to LLM suggestions
            ...

        case QueryAnalysisFailure(...):
            # Complete failure
            ...

    # Step 3: Generate output
    return PaperFinderState(checkpoint=docs), CompleteResponse(data=output)
```

**Key Pattern**: Match statement on QueryAnalysisResult types

### PlanContext: Routing Helper

**Role**: Encapsulates routing logic and agent invocation

**Location**: `paper_finder_agent.py` lines 343-505

```python
class PlanContext(BaseModel):
    """
    Contains:
    - analyzed_input: AnalyzedQuery with all extracted metadata
    - authors, venues, domains: Extracted metadata
    - anchor_doc_collection: Reference papers
    - paper_finder_agent: Reference to orchestrator
    """

    async def run_paper_finder_on_analyzed_query(
        self, inputs: PaperFinderInput, analyzed_input: AnalyzedQuery, anchor_docs: DocumentCollection
    ) -> tuple[DocumentCollection, str]:

        plan_context = PlanContext(...)

        # Route based on query type
        match plan_context.analyzed_input.query_type.type:
            case "SPECIFIC_BY_TITLE":
                response = await plan_context.run_specific_paper_by_title()

            case "SPECIFIC_BY_NAME":
                response = await plan_context.run_specific_paper_by_name()

            case "BY_AUTHOR":
                response = await plan_context.run_search_by_authors()

            case "BROAD_BY_DESCRIPTION":
                if inputs.operation_mode == "diligent":
                    response = await plan_context.run_broad_search()
                else:
                    response = await plan_context.run_fast_broad_search()

            case "METADATA_ONLY_NO_AUTHOR":
                response = await plan_context.attempt_metadata_only_search()

            case "UNKNOWN":
                raise Exception("Unknown query type")

        # Sort and enrich results
        docs, sorting_explanation = await _add_missing_fields_and_sort(response.data.doc_collection, plan_context)

        return docs, aggregated_text
```

### Routing Triggers

| Query Type | Trigger Conditions | Agent Invoked |
|------------|-------------------|---------------|
| **SPECIFIC_BY_TITLE** | • `broad_or_specific == "specific"` <br> • No authors <br> • Has content <br> • `by_name_or_title == "title"` <br> • Title extraction successful | SpecificPaperByTitleAgent |
| **SPECIFIC_BY_NAME** | • `broad_or_specific == "specific"` <br> • No authors <br> • Has content <br> • `by_name_or_title == "name"` | SpecificPaperByNameAgent |
| **BY_AUTHOR** | • Has authors (len(authors) > 0) <br> • Any broad_or_specific | SearchByAuthorsAgent |
| **BROAD_BY_DESCRIPTION** | • `broad_or_specific == "broad"` <br> • OR query starts with "papers about" <br> • OR title search failed (fallback) | BroadSearchAgent / FastBroadSearchAgent |
| **METADATA_ONLY_NO_AUTHOR** | • No content <br> • No authors <br> • Has venues OR time_range | MetadataOnlyAgent |

---

## Agent Deep Dives

### 1. SpecificPaperByTitleAgent

**Location**: `agents/mabool/api/mabool/agents/specific_paper_by_title/specific_paper_by_title_agent.py`

**Complexity**: ⭐ Low (143 lines)

#### Purpose

Find a specific paper when the user provides an exact or near-exact title.

#### Input Schema

```python
class SpecificPaperByTitleInput(AgentInput):
    matched_title: str                     # The extracted/matched title
    matched_corpus_ids: list[str]          # Corpus IDs from query analyzer
    time_range: ExtractedYearlyTimeRange | None = None
    venues: list[str] | None = None
```

**Key Insight**: The heavy lifting is done BEFORE the agent runs. The QueryAnalyzer:
1. Extracts the title using LLM (`title_extraction` prompt)
2. Searches S2 using `get_specific_paper_by_title()`
3. Filters by title match using `_titles_match()`
4. Returns matched corpus IDs

#### Output Schema

```python
type SpecificPaperByTitleOutput = AgentOutput

class AgentOutput(BaseModel):
    response_text: str
    doc_collection: DocumentCollection
```

#### Business Logic

```python
async def handle_operation(
    self, state: SpecificPaperByTitleState | None, inputs: SpecificPaperByTitleInput
) -> tuple[SpecificPaperByTitleState | None, OperativeResponse[SpecificPaperByTitleOutput]]:

    # 1. Create DocumentCollection from matched corpus IDs
    search_results = DC.from_docs([
        PaperFinderDocument(
            corpus_id=corpus_id,
            origins=[get_by_title_origin_query(inputs.matched_title, inputs.time_range, inputs.venues)]
        )
        for corpus_id in inputs.matched_corpus_ids
    ])

    # 2. Handle empty results
    if len(search_results) == 0:
        return (state, CompleteResponse(data=AgentOutput(response_text="", doc_collection=search_results)))

    # 3. Add score field (all papers get score 1.0 - they already matched)
    search_results = await search_results.with_fields([
        AssignedField[float](
            field_name="final_specific_paper_by_title_score",
            assigned_values=[1.0] * len(search_results)
        )
    ])

    # 4. Return results
    return (state, CompleteResponse(data=AgentOutput(response_text="", doc_collection=search_results)))
```

#### Key Functions

**Title Extraction (LLM-based)**:

```python
# In specific_paper_by_title_prompts.py
_title_extraction_prompt_tmpl = """
Given a paper finding query, extract the paper title from the query:

Query: ```{query}```
"""

title_extraction = define_prompt_llm_call(
    _title_extraction_prompt_tmpl,
    input_type=InputQuery,
    output_type=ExtractTitlePromptOutput,  # Has .title field
    custom_format_instructions='Return a JSON dict with the key "title"...'
)
```

**Title Matching (Pre-Agent)**:

```python
def _titles_match(title1: str | None, title2: str | None) -> bool:
    """
    Normalize and compare titles:
    1. Remove non-alphanumeric characters
    2. Convert to lowercase
    3. Remove words <= 3 characters
    4. Compare
    """
    def normalize_title(t: str) -> str:
        t = "".join(filter(str.isalnum, t.lower()))
        return "".join([w for w in t.split() if len(w) > 3])

    if title1 is None or title2 is None:
        return False

    return normalize_title(title1) == normalize_title(title2)
```

**Pre-Agent Search**:

```python
@DI.managed
async def get_specific_paper_by_title(
    user_input: str,
    time_range: ExtractedYearlyTimeRange | None = None,
    venues: list[str] | None = None,
    authors: list[str] | None = None,
) -> tuple[DocumentCollection, str]:
    """
    Called by QueryAnalyzer BEFORE routing to agent.
    Returns (matching_docs, extracted_title).
    """

    # 1. Extract title using LLM
    extracted_title = await get_default_endpoint().execute(title_extraction).once(user_input)
    if not extracted_title:
        extracted_title = user_input  # Fallback to full query

    # 2. Search S2
    search_results = await DC.from_s2_by_title(extracted_title, time_range, venues)

    # 3. Filter by title match
    search_results = search_results.filter(lambda doc: _titles_match(doc.title, extracted_title))

    # 4. Filter by authors if provided
    if authors:
        search_results = search_results.filter(lambda doc: filter_by_author(authors, doc))

    return search_results, extracted_title
```

#### Workflow Diagram

```
User Query: "find the paper attention is all you need"
    ↓
[QueryAnalyzer]
    ↓
    1. LLM extracts title: "Attention Is All You Need"
    2. Search S2 by title
    3. Filter by _titles_match()
    4. Return corpus IDs: ["abc123", "def456"]
    ↓
[PaperFinderAgent routes to SpecificPaperByTitleAgent]
    ↓
SpecificPaperByTitleInput(
    matched_title="Attention Is All You Need",
    matched_corpus_ids=["abc123", "def456"]
)
    ↓
[SpecificPaperByTitleAgent.handle_operation()]
    ↓
    1. Create DocumentCollection from corpus IDs
    2. Add score field (all 1.0)
    3. Return results
    ↓
DocumentCollection with 2 papers (score=1.0 each)
```

#### Key Takeaways for CrewAI

1. **Pre-processing is Key**: Most logic happens in QueryAnalyzer, not the agent
2. **Simple Scoring**: All matched papers get score 1.0 (binary: matched or not)
3. **LLM for Extraction**: Uses LLM to extract clean title from messy query
4. **Normalization**: Strong title normalization for fuzzy matching
5. **Empty Handling**: Gracefully returns empty results if nothing found
6. **No Complex Logic**: Agent itself is very simple (~30 lines of actual logic)

#### Migration Strategy

**For CrewAI**:
- Agent can be simpler - use LLM reasoning instead of separate title extraction tool
- Task description should explain title matching logic
- Tools needed: `s2_search_by_title`, `filter_papers`
- Agent backstory should emphasize title normalization and fuzzy matching

---

### 2. SpecificPaperByNameAgent

**Location**: `agents/mabool/api/mabool/agents/specific_paper_by_name/specific_paper_by_name_agent.py`

**Complexity**: ⭐⭐⭐⭐ High (487 lines)

#### Purpose

Find papers by commonly used names/abbreviations (e.g., "BERT", "AlexNet", "GPT-3", "the Transformer paper").

#### Input Schema

```python
class SpecificPaperByNameInput(AgentInput):
    user_input: str                              # Original query
    extracted_name: str                          # Name extracted by QueryAnalyzer
    extracted_content: Optional[str] = None      # Additional context
    time_range: Optional[ExtractedYearlyTimeRange] = None
    venues: Optional[list[str]] = None
    authors: Optional[list[str]] = None
    domains: DomainsIdentified
```

#### Output Schema

```python
type SpecificPaperByNameOutput = AgentOutput

# Same as SpecificPaperByTitleAgent, but with different scoring field
```

#### Business Logic Flow

```python
async def handle_operation(
    self, state: SpecificPaperByNameState | None, inputs: SpecificPaperByNameInput
) -> tuple[SpecificPaperByNameState | None, OperativeResponse[SpecificPaperByNameOutput]]:

    # Call main search function
    search_results = await get_specific_paper_by_name(
        user_input=inputs.user_input,
        extracted_name=inputs.extracted_name,
        extracted_content=inputs.extracted_content,
        time_range=inputs.time_range,
        venues=inputs.venues,
        authors=inputs.authors,
        domains=inputs.domains,
        filter_threshold=config_value(cfg_schema.specific_paper_by_name_agent.filter_threshold)
    )

    # Take top 2 results
    top2_results = search_results.take(config_value(cfg_schema.search_by_author_agent.limit_for_specific))

    return (state, CompleteResponse(data=AgentOutput(response_text="", doc_collection=top2_results)))
```

#### Multi-Signal Search Strategy

The agent combines results from **3 sources**:

```python
async def get_specific_paper_by_name_with_reporting(...) -> DocumentCollection:

    # Source 1: LLM Suggestions
    llm_suggest_future = get_llm_suggested_papers(
        user_input=user_input,
        domains=domains,
        extra_hints="The query may refer to a method name, technique name, dataset name..."
    )

    # Source 2: S2 Search with Name Scoring
    s2_search_future = s2_name_relevance_search(
        user_input,
        extracted_name,
        domains,
        extracted_content,
        time_range,
        venues
    )

    # Source 3: SPIKE Most Cited (commented out in current code)
    # spike_most_cited_future = ...

    # Gather all results
    llm_suggest_results, s2_search_results = await custom_gather(
        llm_suggest_future, s2_search_future, return_exceptions=True
    )

    # Merge results
    merged_results = s2_search_results + llm_suggest_results

    # Score merged results using all signals
    results_with_scores = await score_specific_by_name_all_origins(
        merged_results=merged_results,
        llm_suggest_results=llm_suggest_results,
        s2_search_results=s2_search_results,
        spike_most_cited_results=DC.empty()
    )

    # Sort by score
    results_with_scores = results_with_scores.sorted(
        sort_definitions=[DocumentCollectionSortDef(field_name="specific_paper_by_name_score", order="desc")]
    )

    # Filter by threshold
    results_with_scores = results_with_scores.filter(
        lambda doc: doc.specific_paper_by_name_score > filter_threshold
    )

    # Normalize scores to final score
    results_with_scores = await results_with_scores.with_fields([
        AggTransformComputedField[float](
            field_name="final_specific_paper_by_name_score",
            computation_func=calculate_final_specific_paper_by_name_score,
            required_fields=["specific_paper_by_name_score"]
        )
    ])

    return results_with_scores
```

#### Sophisticated Scoring System

**S2 Search Scoring** (`score_paper_for_name`):

```python
def score_paper_for_name(extracted_name: str, doc: Document) -> float:
    """
    Multi-factor scoring:

    1. Title Analysis:
       - Title introduces name (e.g., "BERT: Pre-training..."): +1.5 * strong_multiplier
       - Name appears in title: +0.5 * weak_multiplier

    2. Abstract Analysis:
       - Occurrences of name: +(min(count, 3) * 0.1 * strong_multiplier)
       - "We introduce/present/propose {name}": +1.0 * strong_multiplier

    3. URL Analysis:
       - URL contains name (http://bert.ai or github.com/bert): +1.0

    4. Context Boost:
       - Found in search with additional content: score *= 2

    5. Case Sensitivity Bonus:
       - If name is capitalized weirdly (BERT, GPT-3): use case-sensitive scoring
       - Multipliers: strong=1.0, weak=1.0 (vs 0.5, 0.2 for case-insensitive)

    Returns: max(case_sensitive_score, case_insensitive_score)
    """

    score = 0.0

    # Title scoring
    if title_introduces_name(extracted_name, title):
        score += 1.5 * strong_multiplier
    elif extracted_name in title:
        score += 0.5 * weak_multiplier

    # Abstract scoring
    if abstract:
        num_occurrences = len(re.findall(rf"\b{re.escape(extracted_name)}\b", abstract))
        score += min(num_occurrences, 3) * 0.1 * strong_multiplier

        if num_occurrences > 0:
            if we_introduce(extracted_name, abstract):
                score += 1 * strong_multiplier

    # URL scoring
    if url_contains_name(extracted_name, abstract):
        score += 1

    # Content boost
    if found_in_search_with_content:
        score *= 2

    return score
```

**Helper Functions**:

```python
def capitalized_weirdly(name: str) -> bool:
    """Check if name has unusual capitalization (BERT, GPT-3, AlexNet)"""
    return not name.islower() and not name.replace("-", "").istitle()

def we_introduce(name: str, abstract: str) -> bool:
    """Check if abstract contains introduction pattern"""
    # Matches: "We introduce BERT", "This paper presents GPT-3", etc.
    match = re.search(
        r"((we|this work|this paper) ([^\s\.]+\s+){0,15}?(present|introduce|propose|publish|design|develop)(s|es|ed)? "
        rf"([^\s\.]+\s+){{0,15}}(\( ?)?({re.escape(name)})(\( ?)?)|((Our ([^\s]+\s+)"
        rf"{{0,7}}( ?called|named)?({re.escape(name)})))",
        abstract,
        re.IGNORECASE
    )
    return bool(match)

def url_contains_name(name: str, abstract: str) -> bool:
    """Check if URL in abstract contains the name"""
    # Matches: http://bert.ai, https://github.com/bert, etc.
    match = re.search(rf"(https?://)[^\s]*\b{re.escape(name)}\b", abstract, re.IGNORECASE)
    return bool(match)

def title_introduces_name(name: str, title: str) -> bool:
    """Check if title introduces the name"""
    # Matches: "BERT: Pre-training..." or "Transformers (GPT-3)"
    valid_name_re = rf"([Tt]he )?{re.escape(name)}([ \-]?[vV]?(\d(\.\d)?)?)"
    begin_match = re.match(rf"^{valid_name_re}: ", title)
    end_match = re.search(rf"\({valid_name_re}\)\s*$", title)
    return bool(begin_match or end_match)
```

**Multi-Source Scoring** (`score_specific_by_name_all_origins`):

```python
async def score_specific_by_name_all_origins(
    merged_results: DocumentCollection,
    llm_suggest_results: DocumentCollection,
    s2_search_results: DocumentCollection,
    spike_most_cited_results: DocumentCollection,
) -> DocumentCollection:
    """
    Combine scores from multiple sources using weighted sum.

    Steps:
    1. Score each collection by rank (top=3, normalize to 0-1)
    2. Base score for being in results: +1
    3. Weighted combination: weights = [1, 1, 1] for [llm, spike, s2]
    4. Assign combined score to each document
    """

    def score_by_rank(collection: DocumentCollection, max_score: int = 3) -> dict[str, float]:
        # Rank-based scoring: top result gets max_score, bottom gets 1
        rank_scores = {
            doc.corpus_id: min(len(collection) - i, max_score)
            for i, doc in enumerate(collection.documents)
        }
        # Normalize to 0-1 range
        normalized = normalize_scores(rank_scores)
        # Add base score of 1
        return {corpus_id: score + 1 for corpus_id, score in normalized.items()}

    llm_suggest_scores = score_by_rank(llm_suggest_results)
    s2_search_scores = score_by_rank(s2_search_results)
    spike_most_cited_scores = score_by_rank(spike_most_cited_results)

    # Weighted sum (all weights = 1)
    weighted_scores = weighted_scoring_func(
        [llm_suggest_scores, spike_most_cited_scores, s2_search_scores],
        [1, 1, 1]
    )

    # Assign scores to documents
    results_with_scores = await merged_results.with_fields([
        AssignedField[float](
            field_name="specific_paper_by_name_score",
            assigned_values=[weighted_scores.get(doc.corpus_id, 0) for doc in merged_results.documents]
        )
    ])

    return results_with_scores
```

#### S2 Name Relevance Search

```python
async def s2_name_relevance_search(
    user_input: str,
    extracted_name: str,
    domains: DomainsIdentified,
    extracted_content: Optional[str],
    time_range: Optional[ExtractedYearlyTimeRange],
    venues: Optional[list[str]],
    search_iteration: int = 1,
) -> DocumentCollection:
    """
    Search S2 using the name and optional content.

    Strategy:
    1. Search for just the name (limit=5)
    2. If content exists, also search for "name + content" (limit=5)
    3. Merge results
    4. Score each paper using score_paper_for_name()
    5. Filter to papers with score >= 0.5
    """

    fields_of_study = get_fields_of_study_filter_from_domains(domains)

    # Search 1: Just the name
    s2_futures = [
        DC.from_s2_search(
            query=extracted_name,
            limit=5,
            time_range=time_range,
            venues=venues,
            fields_of_study=fields_of_study
        )
    ]

    # Search 2: Name + content (if content exists)
    if extracted_content:
        stripped_content = " ".join(
            extracted_content.lower()
            .replace(extracted_name.lower(), "")
            .replace("paper", "")
            .replace("the", "")
            .replace("original", "")
            .strip()
            .split()
        )
        if stripped_content:
            s2_futures.append(
                DC.from_s2_search(
                    query=extracted_name + " " + stripped_content,
                    limit=5,
                    time_range=time_range,
                    venues=venues,
                    fields_of_study=fields_of_study
                )
            )

    # Gather and merge
    s2_results = await custom_gather(*s2_futures)
    s2_results_merged = s2_results[0].merged(*s2_results[1:])

    # Score each paper
    docs_with_scores = await s2_results_merged.with_fields([
        AssignedField[float](
            field_name="s2_search_score",
            assigned_values=[score_paper_for_name(extracted_name, doc) for doc in s2_results_merged.documents]
        )
    ])

    # Sort by score
    sorted_docs = docs_with_scores.sorted(
        sort_definitions=[DocumentCollectionSortDef(field_name="s2_search_score", order="desc")]
    )

    # Filter to score >= 0.5
    filtered_docs = sorted_docs.filter(lambda doc: doc.dynamic_value("s2_search_score", float, default=0.0) >= 0.5)

    return filtered_docs
```

#### Workflow Diagram

```
User Query: "find the BERT paper"
    ↓
[QueryAnalyzer]
    ↓
    • Extracts name: "BERT"
    • Classifies: SPECIFIC_BY_NAME
    ↓
[PaperFinderAgent routes to SpecificPaperByNameAgent]
    ↓
SpecificPaperByNameInput(
    user_input="find the BERT paper",
    extracted_name="BERT",
    extracted_content="",
    domains=...
)
    ↓
[SpecificPaperByNameAgent.handle_operation()]
    ↓
    [get_specific_paper_by_name()]
        ↓
        ┌────────────────┬─────────────────┬──────────────────┐
        │                │                 │                  │
        ▼                ▼                 ▼                  ▼
    [LLM Suggest]   [S2 Search]    [SPIKE Citations]   (disabled)
        │                │                 │
        │ 5 papers        │ Papers with     │
        │ suggested       │ score >= 0.5    │
        │                │                 │
        └────────────────┴─────────────────┘
                         │
                         ▼
                [Merge All Results]
                         │
                         ▼
            [Score by Multi-Signal]
                • LLM rank score (0-2)
                • S2 rank score (0-2)
                • SPIKE rank score (0-2)
                • Weighted sum (all weight=1)
                         │
                         ▼
            [Sort by Total Score]
                         │
                         ▼
            [Filter by Threshold]
                score >= filter_threshold
                         │
                         ▼
            [Normalize Final Score]
                0.0 - 1.0 range
                         │
                         ▼
            [Take Top 2 Results]
    ↓
DocumentCollection with 1-2 papers
```

#### Key Takeaways for CrewAI

1. **Complex Multi-Signal System**: Combines 3 sources (LLM, S2, citations)
2. **Sophisticated Scoring**:
   - Pattern matching in titles/abstracts
   - URL detection
   - Case sensitivity handling
   - Rank-based scoring across sources
3. **Heavy Regex Usage**: Multiple regex patterns for name detection
4. **Parallel Search**: Runs multiple searches concurrently
5. **Filtering & Ranking**: Multi-stage filtering and ranking
6. **Configurable Thresholds**: Uses config values for limits and thresholds

#### Migration Challenges

**For CrewAI**:
- **Challenge**: Very complex scoring logic
- **Solution Options**:
  1. Simplify: Use LLM reasoning instead of regex patterns
  2. Replicate: Create Python scoring tools
  3. Hybrid: LLM for scoring + simple tools for S2 search
- **Recommendation**: Start with simplified version using LLM reasoning, add scoring tools if needed
- Tools needed: `s2_search_query`, `get_llm_suggested_papers` (new), scoring utilities

---

### 3. MetadataOnlyAgent

**Location**: `agents/mabool/api/mabool/agents/metadata_only/metadata_only_agent.py`

**Complexity**: ⭐ Low (87 lines)

#### Purpose

Find papers using ONLY metadata criteria (venue, year, research domain) without any content search.

#### Input Schema

```python
class MetadataOnlySearchInput(AgentInput):
    time_range: ExtractedYearlyTimeRange | None = None
    venues: list[str] | None = None
    domains: DomainsIdentified

    # Note: If venues exist, domains are ignored
    # Reason: Domains are often hallucinated, venue is more reliable
```

#### Output Schema

```python
type MetadataOnlySearchOutput = AgentOutput

# Returns DocumentCollection + response_text
```

#### Business Logic

```python
async def handle_operation(
    self, state: None, inputs: MetadataOnlySearchInput
) -> tuple[None, OperativeResponse[AgentOutput]]:

    response_text = ""

    try:
        # Get papers by metadata
        results = await self.get_papers_by_metadata(
            inputs.time_range,
            inputs.venues,
            inputs.domains
        )

        # Check results
        if not results or len(results.documents) == 0:
            response_text = "Could not find papers in S2"
            if inputs.venues and len(inputs.venues) > 0:
                response_text += " - try alternative venues"

        elif len(results.documents) == config_value(cfg_schema.s2_api.total_papers_limit):
            # Hit the limit
            response_text = f"Notice: Results limited to {total_papers_limit}"

    except Exception as e:
        return None, VoidResponse(error=AgentError(type="other", message=str(e)))

    return (
        None,
        CompleteResponse(data=AgentOutput(response_text=response_text, doc_collection=results))
    )
```

#### Core Search Logic

```python
@DI.managed
async def get_papers_by_metadata(
    self,
    time_range: ExtractedYearlyTimeRange | None = None,
    venues: list[str] | None = None,
    domains: DomainsIdentified | None = None,
) -> DocumentCollection:

    # Validation: Must have venues OR time_range
    assert venues or (time_range and not time_range.is_empty())

    # Get fields of study from domains
    fields_of_study = get_fields_of_study_filter_from_domains(domains) if domains else None

    # Search S2 with empty query (metadata-only search)
    search_results = await DC.from_s2_search(
        "",  # Empty query string!
        limit=config_value(cfg_schema.s2_api.total_papers_limit),  # e.g., 1000
        time_range=time_range,
        venues=venues,
        fields_of_study=fields_of_study if not venues else None  # Ignore domains if venues exist
    )

    return search_results
```

#### Key Patterns

**1. Empty Query String**:
```python
# Metadata-only search uses EMPTY query string
await DC.from_s2_search(
    "",  # <-- Empty! Only uses metadata filters
    limit=1000,
    time_range=time_range,
    venues=venues,
    fields_of_study=fields_of_study
)
```

**2. Venue Priority**:
```python
# If venues exist, ignore domains (domains can be hallucinated)
fields_of_study=fields_of_study if not venues else None
```

**3. Assertion Validation**:
```python
# Must have SOMETHING to search by
assert venues or (time_range and not time_range.is_empty())
```

**4. Response Messages**:
```python
# Different messages based on result state
if len(results) == 0:
    "Could not find papers in S2"
    if venues: "+ try alternative venues"

elif len(results) == LIMIT:
    f"Notice: Results limited to {LIMIT}"

else:
    "" # Empty response text = success
```

#### Workflow Diagram

```
User Query: "papers from NeurIPS 2023"
    ↓
[QueryAnalyzer]
    ↓
    • Extracts venues: ["NeurIPS"]
    • Extracts time_range: {start: 2023, end: 2023}
    • No content extracted
    • Classifies: METADATA_ONLY_NO_AUTHOR
    ↓
[PaperFinderAgent routes to MetadataOnlyAgent]
    ↓
MetadataOnlySearchInput(
    time_range={start: 2023, end: 2023},
    venues=["NeurIPS"],
    domains=...
)
    ↓
[MetadataOnlyAgent.handle_operation()]
    ↓
    [get_papers_by_metadata()]
        ↓
        1. Validate: venues OR time_range exists ✓
        2. Get fields_of_study from domains
        3. S2 Search with empty query:
           - query=""
           - venues=["NeurIPS"]
           - time_range={2023-2023}
           - fields_of_study=None (ignored due to venues)
           - limit=1000
        ↓
    DocumentCollection with 500 papers
        ↓
    Check result count:
        • 0 papers: "Could not find..."
        • 500 papers: "" (success)
        • 1000 papers: "Notice: limited to 1000"
    ↓
CompleteResponse(
    data=AgentOutput(
        response_text="",
        doc_collection=DocumentCollection(500 papers)
    )
)
```

#### Example Queries

```python
# Example 1: By venue + year
Input: "papers from ICML 2022"
→ MetadataOnlySearchInput(
    venues=["ICML"],
    time_range={start: 2022, end: 2022}
)
→ S2 search: query="", venues=["ICML"], time_range=2022-2022

# Example 2: By year range only
Input: "papers from 2020 to 2023"
→ MetadataOnlySearchInput(
    venues=None,
    time_range={start: 2020, end: 2023}
)
→ S2 search: query="", time_range=2020-2023, fields_of_study=[...]

# Example 3: By multiple venues
Input: "papers from NeurIPS or ICML in 2023"
→ MetadataOnlySearchInput(
    venues=["NeurIPS", "ICML"],
    time_range={start: 2023, end: 2023}
)
→ S2 search: query="", venues=["NeurIPS", "ICML"], time_range=2023-2023
```

#### Key Takeaways for CrewAI

1. **Very Simple**: Only ~30 lines of actual logic
2. **Assertion-Based Validation**: Requires venues OR time_range
3. **Empty Query Pattern**: Uses "" for metadata-only searches
4. **Venue Prioritization**: Ignores domains if venues exist
5. **Limit Handling**: Checks if results hit the limit
6. **Informative Messages**: Different response texts based on results
7. **No Scoring**: Results returned as-is from S2 (no ranking)

#### Migration Strategy

**For CrewAI**:
- Very straightforward to implement
- Agent task: "Search S2 using only metadata, no content"
- Tools needed: `s2_search_query` (with empty query support)
- Agent should explain to user when results are limited
- Simple backstory: "Expert at metadata-based filtering"

---

## Integration Patterns

### Common Patterns Across All Agents

#### 1. DocumentCollection as Central Data Structure

```python
# All agents work with DocumentCollection
from ai2i.dcollection import DocumentCollection

# Creating from corpus IDs
DC.from_docs([
    PaperFinderDocument(corpus_id=id, origins=[...])
    for id in corpus_ids
])

# Creating from S2 search
await DC.from_s2_search(query, limit, time_range, venues, fields_of_study)

# Creating from S2 by title
await DC.from_s2_by_title(title, time_range, venues)

# Empty collection
DC.empty()

# Merging collections
collection1.merged(collection2, collection3)
# OR
collection1 + collection2

# Filtering
collection.filter(lambda doc: doc.year > 2020)

# Sorting
collection.sorted(sort_definitions=[
    DocumentCollectionSortDef(field_name="citation_count", order="desc")
])

# Taking top N
collection.take(10)

# Adding fields
await collection.with_fields([
    AssignedField[float](
        field_name="score",
        assigned_values=[1.0, 0.9, 0.8, ...]
    )
])
```

#### 2. Scoring Pattern

```python
# Step 1: Calculate scores (list of floats)
scores = [calculate_score(doc) for doc in collection.documents]

# Step 2: Add as field
collection_with_scores = await collection.with_fields([
    AssignedField[float](
        field_name="agent_specific_score",
        assigned_values=scores
    )
])

# Step 3: Sort by score
sorted_collection = collection_with_scores.sorted(
    sort_definitions=[DocumentCollectionSortDef(field_name="agent_specific_score", order="desc")]
)

# Step 4: Normalize to final score (0-1 range)
collection_final = await sorted_collection.with_fields([
    AggTransformComputedField[float](
        field_name="final_agent_score",
        computation_func=normalize_scores,
        required_fields=["agent_specific_score"]
    )
])
```

#### 3. Error Handling Pattern

```python
try:
    # Agent logic
    results = await some_operation()

    # Success
    return (state, CompleteResponse(data=AgentOutput(...)))

except Exception as e:
    # Failure
    return None, VoidResponse(error=AgentError(type="other", message=str(e)))
```

#### 4. LLM Integration Pattern

```python
# Define endpoint
def get_default_endpoint() -> LLMEndpoint:
    llm_model = LLMModel.from_name(config_value(cfg_schema.agent.llm_model_name))
    return define_llm_endpoint(
        default_timeout=Timeouts.medium,
        default_model=llm_model,
        logger=logger,
        api_key=get_api_key_for_model(llm_model)
    )

# Define prompt
my_prompt = define_prompt_llm_call(
    prompt_template,
    input_type=InputType,
    output_type=OutputType,
    custom_format_instructions="..."
)

# Execute
result = await get_default_endpoint().execute(my_prompt).once(input_data)
```

#### 5. Parallel Execution Pattern

```python
from mabool.utils.asyncio import custom_gather

# Define futures
future1 = async_operation_1()
future2 = async_operation_2()
future3 = async_operation_3()

# Gather with exception handling
results = await custom_gather(future1, future2, future3, return_exceptions=True)

# Check for exceptions
result1, result2, result3 = results
if isinstance(result1, BaseException):
    logger.warning(f"Operation 1 failed: {result1}")
    result1 = default_value
```

### Agent Orchestration Patterns

#### Pattern 1: Sequential Delegation

```python
# PaperFinderAgent delegates to ONE specialist agent based on query type

match query_type:
    case "SPECIFIC_BY_TITLE":
        response = await self.specific_paper_by_title(inputs)
    case "SPECIFIC_BY_NAME":
        response = await self.specific_paper_by_name(inputs)
    # ... etc
```

#### Pattern 2: Fallback Strategy

```python
# If specific search fails, retry as broad search

docs, text = await self.run_paper_finder_on_analyzed_query(inputs, analyzed_query, anchor_docs)

if len(docs) == 0 and analyzed_query.query_type.type in ["SPECIFIC_BY_TITLE", "SPECIFIC_BY_NAME"]:
    # Re-run in broad mode
    retry_analyzed_query = analyzed_query.model_copy()
    retry_analyzed_query.query_type = QueryType(type="BROAD_BY_DESCRIPTION", broad_or_specific="broad")
    docs, text = await self.run_paper_finder_on_analyzed_query(retry_inputs, retry_analyzed_query, anchor_docs)
```

#### Pattern 3: Conditional Routing

```python
# Different agent based on operation mode

case "BROAD_BY_DESCRIPTION":
    if inputs.operation_mode == "diligent":
        response = await plan_context.run_broad_search()
    else:
        response = await plan_context.run_fast_broad_search()
```

### State Management Patterns

#### Stateless Agents (Most Common)

```python
class MyAgent(Operative[Input, Output, None]):  # <-- STATE = None

    async def handle_operation(
        self, state: None, inputs: Input
    ) -> tuple[None, OperativeResponse[Output]]:
        # No state management
        results = await do_work(inputs)
        return None, CompleteResponse(data=results)
```

#### Stateful Agents (PaperFinderAgent)

```python
class PaperFinderAgent(Operative[Input, Output, PaperFinderState]):

    async def handle_operation(
        self, state: PaperFinderState | None, inputs: Input
    ) -> tuple[PaperFinderState | None, OperativeResponse[Output]]:
        # Do work
        docs = await search(inputs)

        # Save checkpoint in state
        new_state = PaperFinderState(checkpoint=docs)

        return new_state, CompleteResponse(data=output)
```

**State Schema**:
```python
class PaperFinderState(AgentState):
    checkpoint: DocumentCollection  # Last successful results
```

---

## Key Takeaways for CrewAI Migration

### 1. Simplification Opportunities

| Mabool Pattern | CrewAI Equivalent | Simplification |
|----------------|-------------------|----------------|
| Operative class hierarchy | Agent + Task | Less boilerplate |
| Manual `register()` | Crew composition | Declarative |
| Response types (Complete/Partial/Void) | Task outputs | Simpler |
| Custom state management | Built-in memory | Framework handles it |
| Complex scoring functions | LLM reasoning | Let AI do the work |

### 2. What to Keep

**Complex Logic Worth Preserving**:
1. ✅ **Title Normalization** (`_titles_match`) - Very effective fuzzy matching
2. ✅ **Name Pattern Detection** (regex patterns) - Accurate for BERT, GPT-3, etc.
3. ✅ **Multi-Signal Scoring** - Combining multiple sources is powerful
4. ✅ **Venue Priority Logic** - Domain over venues is smart
5. ✅ **Fallback Strategies** - Specific→Broad fallback is user-friendly

**What Can Be Simplified**:
1. 🔄 **LLM Extraction** - CrewAI agents can do this in task descriptions
2. 🔄 **Complex Scoring** - Can use LLM for relevance judgment
3. 🔄 **Parallel Searches** - CrewAI can handle this with tools
4. 🔄 **State Management** - Use CrewAI memory instead of custom state

### 3. Agent Complexity Rankings

**For CrewAI Implementation**:

1. **SpecificPaperByTitleAgent** ⭐ (Easiest)
   - Simple logic
   - Most work in QueryAnalyzer
   - Can leverage LLM for title extraction
   - Good starting point

2. **MetadataOnlyAgent** ⭐ (Very Easy)
   - Simplest of all
   - Just metadata filtering
   - No scoring needed
   - Good for testing

3. **SpecificPaperByNameAgent** ⭐⭐⭐⭐ (Most Complex)
   - Multi-signal search
   - Complex scoring
   - Regex pattern matching
   - Needs careful planning

**Recommended Implementation Order**:
1. MetadataOnlyAgent (warm up)
2. SpecificPaperByTitleAgent (core pattern)
3. SpecificPaperByNameAgent (most complex)

### 4. Tools Needed for Phase 2

**Already Have from Phase 1**:
- ✅ `s2_search_by_title`
- ✅ `s2_search_by_author`
- ✅ `s2_get_paper_details`
- ✅ `s2_search_query`
- ✅ `filter_papers`
- ✅ `sort_papers`
- ✅ `deduplicate_papers`

**Need to Create**:
- 🆕 `get_llm_suggested_papers` - For SpecificPaperByNameAgent
- 🆕 Optional: Scoring utilities if we want to replicate exact logic

**Can Skip**:
- ❌ Title extraction tool - LLM in task can handle it
- ❌ Name extraction tool - LLM in task can handle it
- ❌ Complex scoring tools - Start with LLM-based scoring

### 5. Routing Logic Translation

**Mabool**:
```python
# Centralized routing in PaperFinderAgent
match query_type:
    case "SPECIFIC_BY_TITLE": → SpecificPaperByTitleAgent
    case "SPECIFIC_BY_NAME": → SpecificPaperByNameAgent
    case "METADATA_ONLY_NO_AUTHOR": → MetadataOnlyAgent
```

**CrewAI Phase 2** (Simple):
```python
# For Phase 2, we'll test agents individually
# Each agent will have its own crew for testing

title_crew = Crew(
    agents=[specific_paper_by_title_agent],
    tasks=[title_search_task],
    process=Process.sequential
)

# Later in Phase 3, we'll add QueryAnalyzer for routing
```

**CrewAI Phase 3+** (With Routing):
```python
# QueryAnalyzer will be a CrewAI agent that routes
# Using hierarchical process or conditional task creation

query_analyzer_agent = Agent(
    role="Query Analyzer & Router",
    goal="Analyze query and determine which specialist to use",
    ...
)

# Approach 1: Hierarchical with manager
crew = Crew(
    agents=[query_analyzer, title_agent, name_agent, metadata_agent],
    tasks=[analyze_task, search_task],
    process=Process.hierarchical,
    manager_agent=query_analyzer_agent
)

# Approach 2: Dynamic task creation (callback-based)
# Based on query analysis results, create appropriate tasks
```

### 6. Testing Strategy

**Unit Tests**:
```python
# Test agent creation
def test_create_specific_paper_by_title_agent():
    agent = create_specific_paper_by_title_agent()
    assert agent.role == "Specific Paper Title Search Specialist"
    assert len(agent.tools) > 0

# Test agent execution (mocked)
@pytest.mark.asyncio
async def test_agent_finds_paper_by_title(mock_s2_search):
    crew = create_title_search_crew()
    result = await crew.kickoff(inputs={"paper_title": "Attention Is All You Need"})
    assert len(result.papers) > 0
```

**Integration Tests**:
```python
# Test with real S2 API
@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_famous_paper():
    crew = create_title_search_crew()
    result = await crew.kickoff(inputs={"paper_title": "BERT"})
    assert result.confidence > 0.8
    assert "BERT" in result.papers[0]["title"]
```

### 7. Key Decisions for Phase 2

**Decision 1: Scoring Approach**

Option A: **Replicate Exact Scoring** (Complex)
- Pro: Proven to work
- Con: Lots of custom code, hard to maintain
- Time: +10 hours

Option B: **LLM-Based Scoring** (Simple)
- Pro: Simpler, more flexible
- Con: May be less accurate initially
- Time: +2 hours

**Recommendation**: Start with Option B, add Option A scoring as tools if needed

---

**Decision 2: Title/Name Extraction**

Option A: **Separate Tools**
- Pro: Modular, testable
- Con: More code

Option B: **LLM in Task Description**
- Pro: Simpler, leverages CrewAI
- Con: Less control

**Recommendation**: Option B for Phase 2, can always add tools later

---

**Decision 3: Multi-Source Search (SpecificPaperByName)**

Option A: **Parallel Tool Calls**
- Create separate tools for each source
- Agent orchestrates

Option B: **Single Aggregated Tool**
- One tool that does multi-source search
- Returns merged results

Option C: **Simplified Single Source**
- Just use S2 search for Phase 2
- Add LLM suggestions later

**Recommendation**: Option C for Phase 2 (simpler), then Option A for Phase 3

---

## Appendix: Code Snippets

### A. Title Normalization Function

```python
def normalize_title(title: str) -> str:
    """
    Normalize title for fuzzy matching:
    1. Remove non-alphanumeric
    2. Lowercase
    3. Remove short words (<=3 chars)
    """
    if not title:
        return ""

    # Remove non-alphanumeric
    clean = "".join(filter(str.isalnum, title.lower()))

    # Remove short words
    words = [w for w in clean.split() if len(w) > 3]

    return "".join(words)

def titles_match(title1: str | None, title2: str | None) -> bool:
    """Check if two titles match after normalization"""
    if not title1 or not title2:
        return False
    return normalize_title(title1) == normalize_title(title2)
```

### B. Name Detection Patterns

```python
import re

def title_introduces_name(name: str, title: str) -> bool:
    """
    Check if title introduces the name.
    Matches patterns like:
    - "BERT: Pre-training of Deep..."
    - "Transformers (GPT-3)"
    """
    valid_name_re = rf"([Tt]he )?{re.escape(name)}([ \-]?[vV]?(\d(\.\d)?)?)"

    # Pattern 1: "NAME: rest of title"
    begin_match = re.match(rf"^{valid_name_re}: ", title)
    if begin_match:
        return True

    # Pattern 2: "title (NAME)"
    end_match = re.search(rf"\({valid_name_re}\)\s*$", title)
    if end_match:
        return True

    return False

def we_introduce_pattern(name: str, abstract: str) -> bool:
    """
    Check if abstract contains introduction pattern.
    Matches: "We introduce BERT", "This paper presents GPT-3", etc.
    """
    pattern = (
        r"((we|this work|this paper) "
        r"([^\s\.]+\s+){0,15}?"
        r"(present|introduce|propose|publish|design|develop)(s|es|ed)? "
        rf"([^\s\.]+\s+){{0,15}}"
        rf"(\( ?)?({re.escape(name)})(\( ?)?"
        r")"
    )

    match = re.search(pattern, abstract, re.IGNORECASE)
    return bool(match)
```

### C. DocumentCollection Helpers

```python
from ai2i.dcollection import DocumentCollection, AssignedField

async def add_scores(
    collection: DocumentCollection,
    scores: list[float],
    field_name: str = "score"
) -> DocumentCollection:
    """Add score field to collection"""
    return await collection.with_fields([
        AssignedField[float](
            field_name=field_name,
            assigned_values=scores
        )
    ])

def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    """Normalize scores to 0-1 range"""
    if not scores:
        return {}

    max_score = max(scores.values())
    min_score = min(scores.values())

    if max_score == min_score:
        return {corpus_id: 1.0 for corpus_id in scores.keys()}

    return {
        corpus_id: (score - min_score) / (max_score - min_score)
        for corpus_id, score in scores.items()
    }
```

---

## Summary

### What We Learned

1. **Architecture**: Mabool uses custom Operative pattern with centralized routing
2. **Complexity**: Ranges from simple (MetadataOnly) to very complex (SpecificByName)
3. **Scoring**: Sophisticated multi-signal scoring systems
4. **LLM Integration**: Heavy use for extraction and classification
5. **Orchestration**: PaperFinderAgent routes to specialists via PlanContext

### Phase 2 Implementation Plan

**Recommended Approach**:
1. Start with **MetadataOnlyAgent** (simplest, good warm-up)
2. Then **SpecificPaperByTitleAgent** (establishes core patterns)
3. Finally **SpecificPaperByNameAgent** (most complex, build on experience)

**Simplifications for CrewAI**:
- Use LLM reasoning instead of separate extraction tools
- Start with simpler scoring (can add complexity later)
- Leverage CrewAI's built-in features (memory, tools, tasks)
- Test agents individually before building full routing system

**Tools Needed**:
- ✅ Most tools already exist from Phase 1
- 🆕 `get_llm_suggested_papers` - only new tool needed
- Optional: Scoring utilities if we want exact mabool behavior

### Next Steps

1. ✅ **Complete**: Mabool analysis report
2. 📝 **Next**: Decide on simplifications vs exact replication
3. 🔨 **Then**: Implement MetadataOnlyAgent (easiest first)
4. 🧪 **Test**: Create test crew and validate
5. 🔁 **Iterate**: Apply learnings to other two agents

---

**Report End**

**Document Version**: 1.0
**Date**: 2025-11-08
**Total Analysis Time**: ~2 hours
**Files Analyzed**: 6 files, ~1500 lines of code
**Key Insights**: 42 documented patterns and decisions
