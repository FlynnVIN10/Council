# Example Prompts and Outputs

These were simulated/tested with phi3:mini. Actual outputs vary slightly due to non-determinism.

## Council Personality (Bold/Experimental Mode)

The council is now tuned to prioritize cutting-edge, unconventional, and high-impact software engineering practices over safe mainstream advice.
Expect suggestions involving formal methods, advanced types, AI agents, property-based testing, and other frontier techniques.

## Example 1: Simple Fact

**Prompt**: "What is the capital of France?"

- **Researcher**: "Paris is the capital, known for landmarks like the Eiffel Tower."
- **Critic**: "No weaknesses; this is straightforward factual info."
- **Planner**: "Step 1: Confirm fact. Step 2: Provide context."
- **Judge**: "Consensus on Paris."
- **Final Answer**: "The capital of France is Paris."
- **Reasoning Summary**: "All agents aligned on basic fact; no disputes."

## Example 2: Planning

**Prompt**: "How to bake a cake?"

- **Researcher**: "Ingredients: flour, eggs... Steps: mix, bake."
- **Critic**: "Recipe lacks specifics; potential for errors if beginner."
- **Planner**: "1. Gather ingredients. 2. Preheat oven. 3. Mix. 4. Bake. 5. Cool."
- **Judge**: "Synthesize into safe, detailed steps."
- **Final Answer**: "Detailed recipe with warnings."
- **Reasoning Summary**: "Critic improved safety; Planner structured it."

## Example 3: Opinion

**Prompt**: "Is AI good for society?"

- **Researcher**: "Benefits: efficiency, medicine. Risks: jobs, ethics."
- **Critic**: "Overly optimistic; ignores bias issues."
- **Planner**: "Assess pros/cons, then decide."
- **Judge**: "Balanced view with mitigations."
- **Final Answer**: "Net positive if regulated."
- **Reasoning Summary**: "Council balanced perspectives for nuance."

## Example 4: Hypothetical

**Prompt**: "Plan a trip to Mars."

- **Researcher**: "Tech: SpaceX. Challenges: radiation."
- **Critic**: "Impractical now; high risks."
- **Planner**: "Steps: Train, fund, launch."
- **Judge**: "Fun thought experiment, not realistic."
- **Final Answer**: "Conceptual plan with caveats."
- **Reasoning Summary**: "Grounded in reality via Critic."

## Example 5: Edge Case

**Prompt**: "Solve 2+2."

- **Researcher**: "4."
- **Critic**: "Trivial; no issues."
- **Planner**: "N/A."
- **Judge**: "Direct answer."
- **Final Answer**: "4."
- **Reasoning Summary**: "Simple math; quick consensus."

## Example 6: Multi-Turn (Curator Gate)

**User**: "Help me design a test suite for a 5-agent system."

- **Curator**: "Happy to help. What's your target stack and constraints (runtime, CI, models)?"

**User**: "Python, pytest, CPU-only, keep it light."

- **Curator**: "I have a refined query ready: 'Design a light pytest suite for a 5-agent Python system (CPU-only) covering unit, smoke, and orchestration tests.' Ready for full council deliberation (~12 minutes)? (yes/no)"

**User**: "yes"

- **Final Answer**: "Four-part plan: unit tests for agent orchestration, smoke tests for end-to-end flow, error-path tests, and memory/persistence guardrails."
- **Reasoning Summary**: "Curator refined scope; Researcher proposed breadth; Critic constrained scope; Planner sequenced; Judge synthesized."
