from agents.crew.main import create_crew_with_llm
from langchain_openai import ChatOpenAI
from mabool.data_model.agent import (
    AnalyzedQuery,
    QueryAnalysisFailure,
    QueryAnalysisPartialSuccess,
    QueryAnalysisRefusal,
    QueryAnalysisResult,
    QueryAnalysisSuccess,
    NoActionableDataError,
    PartiallyAnalyzedQuery,
)
from mabool.data_model.specifications import Specifications
from ai2i.config import ConfigValue, configurable
from typing import cast
import logging
from . import analyze

logger = logging.getLogger(__name__)

@configurable
async def extract_specifications(
    user_input: str,
    specification_extraction_model_name: str = ConfigValue(cfg_schema.metadata_planner_agent.llm_model_name),
) -> Specifications:
    try:
        spec_extract_llm_model = LLMModel.from_name(specification_extraction_model_name)
        spec_extract_endpoint = define_llm_endpoint(
            default_timeout=Timeouts.medium,
            default_model=spec_extract_llm_model,
            logger=logger,
            api_key=get_api_key_for_model(spec_extract_llm_model),
        ).model_params(temperature=0.1)
        return await spec_extract_endpoint.execute(specification_extraction).once(user_input)
    except Exception as e:
        logger.exception(f"Failed to extract specifications: {user_input}. Continue with best effort. Error: {e}")
        return Specifications(union=[])

@configurable
async def decompose_and_analyze_query_restricted(
    user_input: str,
    model_name: str = ConfigValue(cfg_schema.query_analyzer_agent.llm_abstraction_model_name),
) -> QueryAnalysisResult:
    """
    This function has been refactored to use the new crewai-based system.
    """
    llm = ChatOpenAI(model_name=model_name)
    crew = create_crew_with_llm(llm=llm)
    result = crew.kickoff(inputs={'query': user_input})
    specifications = await extract_specifications(user_input)

    analyzed_query = result.analyzed_query
    errors = [] # No error handling in crew yet

    match analyzed_query:
        case AnalyzedQuery():
            logger.info(f"{analyzed_query = }")
        case PartiallyAnalyzedQuery():
            logger.warning(f"{analyzed_query = } with {errors = }")

    if any(isinstance(error, NoActionableDataError) for error in errors):
        return QueryAnalysisFailure(
            partially_analyzed_query=cast(PartiallyAnalyzedQuery, analyzed_query),
            error=[e for e in errors if isinstance(e, NoActionableDataError)][0],
        )

    if analyzed_query.possible_refusal and analyzed_query.possible_refusal.type:
        return QueryAnalysisRefusal(analysis=analyzed_query, errors=errors)

    if len(errors) == 0:
        return QueryAnalysisSuccess(
            analyzed_query=analyzed_query, specifications=specifications
        )

    return QueryAnalysisPartialSuccess(
        partially_analyzed_query=cast(PartiallyAnalyzedQuery, analyzed_query), errors=errors
    )
