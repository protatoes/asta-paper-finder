from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from mabool.data_model.agent import DomainsIdentified, RelevanceCriteria
from mabool.agents.specific_paper_by_name.specific_paper_by_name_agent import get_specific_paper_by_name
from mabool.agents.broad_search_by_keyword.broad_search_by_keyword_agent import (
    BroadSearchByKeywordAgent,
)

class PaperFinderByNameInput(BaseModel):
    """Input schema for PaperFinderByNameTool."""
    paper_name: str = Field(..., description="The name of the paper to find.")
    user_input: str = Field(..., description="The user's original query.")
    domains: DomainsIdentified = Field(..., description="The domains identified in the query.")

class PaperFinderByNameTool(BaseTool):
    name: str = "Paper Finder by Name"
    description: str = "Finds a specific academic paper by its name."
    args_schema: Type[BaseModel] = PaperFinderByNameInput

    def _run(self, paper_name: str, user_input: str, domains: DomainsIdentified) -> str:
        papers = get_specific_paper_by_name(
            user_input=user_input,
            extracted_name=paper_name,
            domains=domains,
        )
        return str(papers)

class BroadPaperSearchInput(BaseModel):
    """Input schema for BroadPaperSearchTool."""
    content_query: str = Field(..., description="The content query to search for.")
    relevance_criteria: RelevanceCriteria = Field(..., description="The relevance criteria for the search.")
    domains: DomainsIdentified = Field(..., description="The domains identified in the query.")
    recent_first: bool = Field(default=False, description="Whether to sort by most recent first.")
    recent_last: bool = Field(default=False, description="Whether to sort by least recent first.")
    central_first: bool = Field(default=False, description="Whether to sort by most central first.")
    central_last: bool = Field(default=False, description="Whether to sort by least central first.")
    apply_relevance_judgement: bool = Field(default=True, description="Whether to apply relevance judgement.")

class BroadPaperSearchTool(BaseTool):
    name: str = "Broad Paper Search"
    description: str = "Performs a broad search for academic papers based on a content query."
    args_schema: Type[BaseModel] = BroadPaperSearchInput

    def _run(
        self,
        content_query: str,
        relevance_criteria: RelevanceCriteria,
        domains: DomainsIdentified,
        recent_first: bool = False,
        recent_last: bool = False,
        central_first: bool = False,
        central_last: bool = False,
        apply_relevance_judgement: bool = True,
    ) -> str:
        agent = BroadSearchByKeywordAgent()
        papers = agent.search(
            content_query=content_query,
            relevance_criteria=relevance_criteria,
            domains=domains,
            recent_first=recent_first,
            recent_last=recent_last,
            central_first=central_first,
            central_last=central_last,
            apply_relevance_judgement=apply_relevance_judgement,
        )
        return str(papers)
