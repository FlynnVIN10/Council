import os
import sys
from src.council import run_council_sync

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 60)
    print("     LOCAL AI COUNCIL — Bold & Deep Mode")
    print("     (phi3:mini @ 5000 tokens — visionary portfolios)")
    print("=" * 60)
    print("Type your message. 'exit' or 'quit' to end. Ctrl+C to interrupt.\n")

def interactive_mode():
    print_header()
    print("Council is ready. Ask away!\n")

    history = []  # List of {"role": "user"/"assistant", "content": "..."} for context
    last_proposal = None  # Store last self-improvement proposal

    while True:
        try:
            user_input = input("\033[1;34mYou:\033[0m ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in {"exit", "quit"}:
                print("\n\033[1;32mCouncil session ended. Goodbye!\033[0m")
                break

            # Handle approval
            if user_input.lower() == "approved. proceed" and last_proposal:
                print("\n\033[1;33mExecuting approved proposal...\033[0m\n")
                result = run_council_sync("Approved. Proceed", previous_proposal=last_proposal)
                if "error" in result:
                    print(f"\n\033[1;31mError: {result['error']}\033[0m")
                elif result.get("executed"):
                    print(f"\n\033[1;32m✓ {result.get('message', 'Proposal executed')}\033[0m")
                    if "branch" in result:
                        print(f"Branch: {result['branch']}\n")
                last_proposal = None  # Clear after execution
                print("\n" + "-"*60)
                input("\033[1;34mPress Enter for next message...\033[0m")
                print_header()
                continue

            # Build contextual prompt
            context = "\n".join([
                f"{'You' if msg['role']=='user' else 'Council Final Answer'}: {msg['content']}"
                for msg in history[-8:]  # Last 4 exchanges
            ])
            full_prompt = f"""Previous conversation summary:
{context}

New message: {user_input}

Respond as the full council deliberation."""

            print("\n\033[1;33mCouncil deliberating... (Researcher → Critic → Planner → Judge)\033[0m\n")

            result = run_council_sync(full_prompt)

            if "error" in result:
                print(f"\n\033[1;31mError: {result['error']}\033[0m")
                continue

            # Display full chain of thought
            print("\033[1;35mResearcher (bold exploration):\033[0m")
            print(result['agents'][0]['output'])
            print("\n\033[1;31mCritic (contrarian challenge):\033[0m")
            print(result['agents'][1]['output'])
            print("\n\033[1;36mPlanner (multi-track strategy):\033[0m")
            print(result['agents'][2]['output'])
            print("\n\033[1;32mJudge (visionary synthesis):\033[0m")
            print(result['agents'][3]['output'])

            print("\n" + "="*60)
            print("\033[1;37mFINAL COUNCIL ANSWER\033[0m")
            print("="*60)
            print(result['final_answer'])
            print("\n\033[1;37mREASONING SUMMARY\033[0m")
            print(result['reasoning_summary'])

            # Handle self-improvement proposal
            if result.get("is_self_improve") and "proposal" in result:
                last_proposal = result["proposal"]
                print("\n" + "="*60)
                print("\033[1;33m🔧 SELF-IMPROVEMENT PROPOSAL GENERATED\033[0m")
                print("="*60)
                if "description" in last_proposal:
                    print(f"\n\033[1;36mProposal:\033[0m {last_proposal['description']}")
                if "file_changes" in last_proposal:
                    print(f"\n\033[1;36mFiles to modify:\033[0m {', '.join(last_proposal['file_changes'].keys())}")
                if "impact" in last_proposal:
                    print(f"\n\033[1;36mExpected Impact:\033[0m {last_proposal['impact']}")
                print("\n\033[1;33mTo approve and execute, type: 'Approved. Proceed'\033[0m")
            else:
                last_proposal = None

            # Update history
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": result['final_answer']})

            print("\n" + "-"*60)
            input("\033[1;34mPress Enter for next message...\033[0m")  # Pause for readability
            print_header()

        except KeyboardInterrupt:
            print("\n\n\033[1;32mSession interrupted. Goodbye!\033[0m")
            break
        except Exception as e:
            print(f"\n\033[1;31mError: {e}\033[0m")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Single-shot fallback
        prompt = " ".join(sys.argv[1:])
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
    else:
        interactive_mode()
