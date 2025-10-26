import pytest
from types import SimpleNamespace
from agents.crew.main import create_crew_with_llm, QueryAnalysis
from mabool.data_model.agent import AnalyzedQuery, QueryType

# Example: your factory should allow injecting an LLM or response function
def fake_llm_returning(structured_obj):
    class FakeLLM:
        def invoke(self, *_args, **_kwargs):
            return structured_obj
    return FakeLLM()

def test_crew_kickoff():
    """
    Test that the crew can correctly parse a user's query into a structured output.
    """
    fake_output = QueryAnalysis(
        analyzed_query=AnalyzedQuery(
            original_query="Find the paper 'Attention Is All You Need'",
            content="Attention Is All You Need",
            authors=[],
            venues=[],
            time_range=None,
            extracted_properties=None,
            query_type=QueryType(type="SPECIFIC_BY_NAME", broad_or_specific="specific"),
            relevance_criteria=None,
            domains=None,
            possible_refusal=None,
            matched_title=None,
        )
    )
    llm = fake_llm_returning(fake_output)
    crew = create_crew_with_llm(llm=llm)
    result = crew.kickoff(inputs={'query': "Find the paper 'Attention Is All You Need'"})
    assert result is not None
    assert isinstance(result, QueryAnalysis)
    assert result.analyzed_query.query_type.type == "SPECIFIC_BY_NAME"
    assert result.analyzed_query.content == "Attention Is All You Need"
