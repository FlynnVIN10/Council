# The Council - Project Roadmap

## v0.1 Release Criteria (Sprint 1)

### Objective
Create a fully local 4-agent AI council system running on 2018 MacBook Pro with no external API dependencies.

### Hardware Constraints
- **Target System**: 2018 15" MacBook Pro
- **CPU**: 6-core Intel i7 (CPU-only, no CUDA)
- **RAM**: 16GB total, <12GB usage target to avoid macOS swapping
- **Storage**: Local models only

### Core Requirements

#### 1. Four-Agent Architecture
**Agent Roster**:
1. **Analyst** - Data analysis and pattern recognition
2. **Critic** - Critical evaluation and quality assurance
3. **Innovator** - Creative problem-solving and ideation
4. **Synthesizer** - Integration and final recommendation generation

**Agent Flow** (Sequential, NO parallelization):
```
Curator → Researcher → Critic → Planner → Judge
```

#### 2. Local Model Requirements
- **No Cloud APIs**: No OpenAI, Anthropic, or other external services
- **Dummy Keys**: Use placeholder keys if framework requires, but never send traffic
- **Model Size**: Small quantized models (3B-7B parameters)
- **Model Runner**: Ollama (preferred) or LM Studio
- **RAM Budget**: Each agent <3GB, total system <12GB

#### 3. Orchestration Framework
- **Options**: CrewAI or LangGraph
- **Configuration**: Local model endpoints only
- **Error Handling**: Graceful degradation, no external fallbacks

#### 4. API Interface
- **Technology**: FastAPI
- **Endpoint**: `/api/council`
- **Input**: User query/task
- **Output**: Multi-agent deliberation results
- **Response Format**: JSON with agent contributions

#### 5. RAM Optimization Strategies

**Model Management**:
- Load models on-demand, unload after use
- Share base model weights where possible
- Use quantized models (Q4_0, Q5_0, or similar)
- Implement model caching with LRU eviction

**Memory Profiling**:
- Monitor RSS (Resident Set Size) continuously
- Set hard limits per agent process
- Implement memory pressure detection
- Automatic agent throttling if approaching 12GB threshold

**Process Architecture**:
- Sequential agent execution (one at a time)
- Clean process termination between agents
- Garbage collection between agent runs
- Swap usage monitoring and alerts

### Acceptance Criteria for v0.1

- [ ] All 4 agents implemented with distinct roles
- [ ] Sequential orchestration working (no parallelization)
- [ ] Local Ollama/LM Studio integration complete
- [ ] No external API calls detected (verified via network monitoring)
- [ ] FastAPI server running on localhost
- [ ] `/api/council` endpoint functional
- [ ] Peak RAM usage stays <12GB under typical queries
- [ ] Response time <2 minutes for standard queries
- [ ] Error handling for model failures
- [ ] Basic logging and debugging output

### Technical Stack

**Core**:
- Python 3.9+
- FastAPI
- Ollama or LM Studio
- CrewAI or LangGraph

**Models** (Examples):
- Llama 2 7B quantized
- Mistral 7B quantized
- Phi-2 3B
- TinyLlama 1.1B (fallback)

**Dependencies**:
- No OpenAI SDK (or use with dummy keys)
- No Anthropic SDK
- Local model inference only
- psutil for memory monitoring

### Development Phases

**Phase 1: Foundation** (Current)
- [x] Repository setup
- [x] Development environment configured
- [x] Terminal infrastructure operational
- [ ] ROADMAP.md created (this file)

**Phase 2: Model Setup**
- [ ] Ollama/LM Studio installed
- [ ] Local models downloaded and tested
- [ ] Model performance benchmarked
- [ ] RAM usage profiled

**Phase 3: Agent Implementation**
- [ ] Agent base class/interface defined
- [ ] Analyst agent implemented
- [ ] Critic agent implemented
- [ ] Innovator agent implemented
- [ ] Synthesizer agent implemented

**Phase 4: Orchestration**
- [ ] Sequential flow implemented
- [ ] Agent communication protocol defined
- [ ] Context passing between agents
- [ ] Error handling and retries

**Phase 5: API Layer**
- [ ] FastAPI server setup
- [ ] `/api/council` endpoint implemented
- [ ] Request validation
- [ ] Response formatting
- [ ] Basic authentication (optional)

**Phase 6: Optimization & Testing**
- [ ] RAM optimization implemented
- [ ] Performance profiling
- [ ] Load testing
- [ ] Documentation
- [ ] v0.1 release

### Success Metrics

**Performance**:
- Response time: <2 minutes (target), <5 minutes (acceptable)
- RAM usage: <12GB peak, <8GB average
- CPU utilization: <80% during inference
- Model load time: <30 seconds per agent

**Quality**:
- Agent responses relevant to assigned role
- Synthesizer successfully integrates perspectives
- No external API calls (100% local)
- Graceful handling of model errors

**Reliability**:
- No crashes from memory exhaustion
- Consistent results across multiple runs
- Error recovery within 30 seconds
- System stable for 1-hour continuous operation

### Known Constraints & Tradeoffs

**Limitations**:
- Slower inference than cloud APIs (expected 10-100x)
- Smaller models = less capable reasoning
- Sequential execution = longer total time
- RAM constraints limit context window

**Design Decisions**:
- Prioritize reliability over speed
- Prioritize local execution over capability
- Simple before complex
- Measure before optimize

### Future Considerations (Post-v0.1)

- [ ] Web UI for council interactions
- [ ] Agent specialization with fine-tuned models
- [ ] Conversation history/memory
- [ ] Multi-turn deliberations
- [ ] Configurable agent personalities
- [ ] Performance dashboard
- [ ] Docker containerization
- [ ] Larger models on better hardware

---

**Document Version**: 1.0  
**Last Updated**: December 21, 2025  
**Status**: Sprint 1 P0 - Foundation  
**Next Review**: After Phase 2 completion
