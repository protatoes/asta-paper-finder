# CrewAI Agents

This directory contains the implementation of a multi-agent system using CrewAI. The system is designed to analyze user queries and route them to the appropriate tools for finding academic papers.

## Architecture

The system is composed of the following components:

- **Agents**: A set of CrewAI agents, each with a specific role and set of tools.
- **Tasks**: A series of tasks that are assigned to the agents to process a user's query.
- **Crew**: A CrewAI crew that orchestrates the agents and tasks to achieve a common goal.
- **Tools**: A collection of tools that the agents can use to perform their tasks, such as searching for papers by title or author.
