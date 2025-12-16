import sys
from src.council import run_council_sync

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        prompt = input("Enter your prompt: ")
    
    result = run_council_sync(prompt)
    
    print("\n=== Council Results ===")
    print(f"Prompt: {result['prompt']}")
    for agent in result['agents']:
        print(f"\n{agent['name']}:")
        print(agent['output'])
    print("\nFinal Answer:")
    print(result['final_answer'])
    print("\nReasoning Summary:")
    print(result['reasoning_summary'])

