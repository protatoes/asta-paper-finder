# Paper Finder - CrewAI Implementation

This directory contains the CrewAI-based implementation of the Paper Finder agent system.

## Status

**Current Phase**: Phase 1 - Foundation
**Progress**: Directory structure created

## Overview

This implementation runs **side-by-side** with the existing mabool implementation, allowing for:
- Learning CrewAI patterns through practical application
- A/B testing and comparison of results
- Gradual migration and feature parity validation
- Fallback option if needed

## Structure

```
agents/crewai/api/paperfinder_crew/
├── agents/       # CrewAI Agent definitions (12 agents)
├── tasks/        # Task templates and factories
├── tools/        # Tool implementations (13+ tools)
├── crews/        # Crew compositions and orchestration
├── state/        # State management utilities
├── config/       # Configuration files
└── tests/        # Test suite
```

## Implementation Progress

See `/PROGRESS.md` for detailed tracking.

### Phase 1: Foundation (In Progress)
- [x] Directory structure created
- [ ] Dependencies installed
- [ ] Core tools implemented
- [ ] Tool tests written

### Remaining Phases
- Phase 2: Simple Agents
- Phase 3: Query Analyzer
- Phase 4: Complex Agents
- Phase 5: Crew Orchestration
- Phase 6: API Integration
- Phase 7: Testing & Refinement
- Phase 8: Documentation

## Documentation

- **`/DESIGN.md`**: Complete technical design and architecture
- **`/PROGRESS.md`**: Detailed progress tracking
- **`/SESSION.md`**: Current session state and notes

## Key Design Decisions

1. **Side-by-side**: Both mabool and crewai implementations coexist
2. **Fine-grained tools**: Multiple specific tools rather than multipurpose ones
3. **Preserved libraries**: ai2i.dcollection, ai2i.chain, ai2i.di, ai2i.config
4. **Replaced pattern**: Custom Operative → CrewAI Agents/Crews/Tasks
5. **Hybrid state**: CrewAI memory + custom state store

## Quick Start

*(To be completed when implementation begins)*

## Testing

*(To be completed when tests are implemented)*

## Comparison with Mabool

For comparison of the two implementations, see `DESIGN.md` Section: "Architecture Comparison"

## Contributing

This is a learning project. See `SESSION.md` for current work and `PROGRESS.md` for what needs to be done next.

## License

Same as parent project (see `/LICENSE`)
