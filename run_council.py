import sys
from src.council import run_council_sync

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    else:
        prompt = input("Enter your prompt: ")
    
    print(f"Running council with prompt: {prompt}")
    print("This may take 30-60 seconds on CPU...\n")
    
    result = run_council_sync(prompt)
    
    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
        sys.exit(1)
    
    print("\n=== Council Results ===")
    print(f"Prompt: {result.get('prompt', prompt)}")
    for agent in result.get('agents', []):
        print(f"\n{agent['name']}:")
        print(agent['output'])
    print("\nFinal Answer:")
    print(result.get('final_answer', 'N/A'))
    print("\nReasoning Summary:")
    print(result.get('reasoning_summary', 'N/A'))

