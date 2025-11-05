"""
State Management

This module handles state management for the Paper Finder CrewAI implementation.

Components:
- StateManager: Manages complex state across crew executions
- Session management utilities
- Document collection persistence
- State serialization/deserialization

Implements hybrid approach:
1. Task context for immediate task-to-task data passing
2. CrewAI memory for agent learning
3. Custom state store for document collections and complex state
"""
