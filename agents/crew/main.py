from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel
from agents.crew.tools.paper_finder_tools import PaperFinderByNameTool, BroadPaperSearchTool
from mabool.data_model.agent import AnalyzedQuery

class QueryAnalysis(BaseModel):
    """The structured analysis of the user's query."""
    analyzed_query: AnalyzedQuery

def create_crew_with_llm(llm):
    """
    Creates a crew with a query analyzer agent.

    Args:
        llm: The language model to use for the crew.

    Returns:
        A crew that can analyze a user's query.
    """

    # Instantiate the tools
    paper_finder_by_name_tool = PaperFinderByNameTool()
    broad_paper_search_tool = BroadPaperSearchTool()

    # Define your agents with roles and goals
    query_analyzer_agent = Agent(
        role='Query Analyzer',
        goal='Analyze the user query and extract a structured representation of it.',
        backstory="""You are an expert in analyzing user queries and extracting a structured representation of them.
        You are able to identify the user's intent, the main keywords, and any other relevant information.""",
        verbose=True,
        allow_delegation=False,
        tools=[paper_finder_by_name_tool, broad_paper_search_tool],
        llm=llm
    )

    # Create tasks for your agents
    analyze_query_task = Task(
        description="Analyze the user query: '{query}'",
        expected_output="A structured analysis of the user's query.",
        agent=query_analyzer_agent,
        output_pydantic=QueryAnalysis
    )

    # Instantiate your crew with a sequential process
    crew = Crew(
        agents=[query_analyzer_agent],
        tasks=[analyze_query_task],
        process=Process.sequential
    )

    return crew
