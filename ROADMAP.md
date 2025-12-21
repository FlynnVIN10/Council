# The Council Roadmap

## Overview

This roadmap defines release criteria and priorities for The Council project, focusing on core functionality and stability for the v0.1 release.

---

## v0.1 Release Criteria (Sprint 1 P0)

The v0.1 release must meet all of the following criteria before release:

### 1. 5-Agent Sequential Execution Success
- ✅ All 5 agents execute in correct sequence: Curator → Researcher → Critic → Planner → Judge
- ✅ Each agent completes its task before the next agent begins
- ✅ Agent outputs are properly passed between stages
- ✅ Error handling prevents cascading failures
- ✅ All agents produce valid, structured outputs

### 2. Local Ollama Inference Only
- ✅ No external API calls or cloud dependencies
- ✅ All inference runs through local Ollama instance
- ✅ Model loading and inference works on CPU-only hardware
- ✅ No internet connectivity required for core functionality
- ✅ Graceful handling when Ollama is unavailable

### 3. CLI/API Execution Success
- ✅ CLI interface (`python run_council.py`) functions correctly
- ✅ Interactive mode works with proper input/output handling
- ✅ Single-shot mode accepts command-line arguments
- ✅ API endpoints (if implemented) return valid responses
- ✅ Both interfaces produce identical results for same inputs

### 4. Memory Ceiling Respected (<12GB RAM)
- ✅ Peak memory usage stays under 12GB during full council runs
- ✅ Model loading doesn't exceed available memory
- ✅ No memory leaks across multiple executions
- ✅ Memory profiling confirms constraint adherence
- ✅ Graceful degradation if memory limits are approached

### 5. Smoke Test Passing
- ✅ Complete end-to-end test: user prompt → full council deliberation → final answer
- ✅ All 5 agents execute without errors
- ✅ Output format matches expected structure
- ✅ Test completes within reasonable time (<20 minutes on target hardware)
- ✅ No crashes or unhandled exceptions

---

## Explicit Non-Goals for v0.1

The following features are **explicitly out of scope** for v0.1:

### Persistence
- ❌ No persistent storage of conversation history across sessions
- ❌ No database or file-based session management
- ❌ Each run starts fresh with no memory of previous interactions
- *Rationale: Focus on core execution logic first, persistence is a future enhancement*

### Long-Term Memory
- ❌ No learning from previous sessions
- ❌ No accumulation of knowledge across runs
- ❌ No memory system for storing insights or patterns
- *Rationale: Keep v0.1 stateless and simple; memory systems add complexity*

### Plugins
- ❌ No plugin architecture or extensibility system
- ❌ No third-party integrations
- ❌ No modular component system
- *Rationale: Establish solid core before adding extension points*

### Other Excluded Features
- ❌ No web UI (CLI/API only)
- ❌ No distributed execution or multi-machine support
- ❌ No advanced monitoring or observability
- ❌ No self-improvement mode execution (proposal-only)
- ❌ No Docker requirements (optional, not default)

---

## Success Metrics

v0.1 is considered successful when:
- All 5 release criteria pass consistently
- Smoke test passes 100% of the time
- Memory usage verified on target hardware (2018 MacBook Pro)
- No critical bugs blocking core functionality
- Documentation enables new users to run the system

---

## Post-v0.1 Considerations

Future versions may include (not committed for v0.1):
- Persistent conversation history
- Long-term memory and learning systems
- Plugin architecture
- Web UI improvements
- Performance optimizations
- Additional model support
- Enhanced error recovery

---

## Notes

- Target hardware: 2018 MacBook Pro (6-core i7, 16GB RAM, CPU-only)
- Recommended model: phi3
- Expected runtime: ~12 minutes for full council deliberation (with recommended settings)
- This roadmap is a living document and may be updated as priorities evolve

