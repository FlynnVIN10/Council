import os
import sys
from src.council import run_council_sync, run_curator_only

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 60)
    print("     THE COUNCIL — Bold & Deep Mode")
    print("     (phi3:mini @ 3700 tokens — visionary portfolios)")
    print("=" * 60)
    print("Type your message. 'exit' or 'quit' to end. Ctrl+C to interrupt.\n")

def interactive_mode():
    print_header()
    print("\033[1;36mCurator:\033[0m Hello and welcome to The Council!\n")
    print("I'm the Curator — your fast assistant to help craft great queries for the full council's bold deliberation.\n")
    print("The council takes ~12 minutes for deep reasoning, so let's refine your idea first.\n")
    print("How can I help today?\n")

    curator_history = []  # Conversation history with Curator only
    last_proposal = None  # Store last self-improvement proposal
    waiting_for_confirmation = False  # Track if we're waiting for yes/no
    refined_query = None  # Store refined query when Curator asks for confirmation

    while True:
        try:
            # Standard input() handles multi-line paste correctly:
            # User can paste multi-line text, press Enter once, and input() returns the full text
            # Processing only happens after Enter is pressed - no auto-trigger on paste
            user_input = input("\033[1;34mYou:\033[0m ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in {"exit", "quit"}:
                print("\n\033[1;32mCouncil session ended. Goodbye!\033[0m")
                break

            # Check for Self-Improvement Mode trigger (only after Enter is pressed)
            is_self_improve_trigger = (
                "self-improvement mode" in user_input.lower() or 
                "self-improve" in user_input.lower()
            )
            
            # Handle Self-Improvement Mode - bypass Curator
            if is_self_improve_trigger:
                print("\n\033[1;36mCurator:\033[0m Entering Self-Improvement Mode — the full council will now deliberate on a self-evolution proposal (~12 minutes).\n")
                try:
                    result = run_council_sync(user_input, skip_curator=True, stream=True)
                except KeyboardInterrupt:
                    print("\n\n\033[1;31mDeliberation interrupted by user.\033[0m")
                    print("Returning to Curator...\n")
                    print_header()
                    continue
                
                if "error" in result:
                    print(f"\n\033[1;31mError: {result['error']}\033[0m")
                    continue
                
                # Display final answer (streaming already printed agent outputs)
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

                curator_history = []  # Reset after full council run
                waiting_for_confirmation = False
                refined_query = None

                # Clean return to prompt - user can scroll up for history
                continue

            # Handle approval for self-improvement
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
                curator_history = []  # Reset curator conversation
                waiting_for_confirmation = False
                # Clean return to prompt
                continue

            # Handle confirmation response
            if waiting_for_confirmation:
                if user_input.lower() in {"yes", "y"}:
                    # Run full council with refined query
                    query_to_use = refined_query if refined_query else user_input
                    print("\n\033[1;33mThe Council is deliberating...\033[0m\n")
                    try:
                        result = run_council_sync(query_to_use, skip_curator=True, stream=True)
                    except KeyboardInterrupt:
                        print("\n\n\033[1;31mDeliberation interrupted by user.\033[0m")
                        print("Returning to Curator...\n")
                        waiting_for_confirmation = False
                        refined_query = None
                        print_header()
                        continue
                    waiting_for_confirmation = False
                    refined_query = None
                    curator_history = []  # Reset after full council run
                    
                    # Display final answer (streaming already printed agent outputs)
                    if "error" in result:
                        print(f"\n\033[1;31mError: {result['error']}\033[0m")
                        continue

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

                    # Clean return to prompt - user can scroll up for history
                    continue
                else:
                    # Continue conversation with Curator
                    curator_history.append({"role": "user", "content": user_input})
                    try:
                        curator_result = run_curator_only(user_input, curator_history, stream=True)
                    except KeyboardInterrupt:
                        print("\n\n\033[1;31mCurator interrupted by user.\033[0m")
                        print("Returning to input...\n")
                        waiting_for_confirmation = False
                        print_header()
                        continue
                    if "error" in curator_result:
                        print(f"\n\033[1;31mError: {curator_result['error']}\033[0m")
                        continue
                    
                    # Output already streamed, no need to print again
                    print()  # Single blank line for separation
                    
                    curator_history.append({"role": "assistant", "content": curator_result['output']})
                    
                    if curator_result.get("asking_confirmation"):
                        waiting_for_confirmation = True
                        # Try to extract refined query from Curator output
                        output = curator_result['output']
                        if "refined query ready:" in output.lower():
                            parts = output.split("refined query ready:", 1)
                            if len(parts) > 1:
                                refined_query = parts[1].split("\n")[0].strip().strip('"').strip("'")
                        if not refined_query:
                            refined_query = user_input  # Fallback to original
                    else:
                        waiting_for_confirmation = False
                    
                    # Clean return to prompt - continue conversation
                    continue
            else:
                # Normal flow: Run Curator first
                curator_history.append({"role": "user", "content": user_input})
                try:
                    curator_result = run_curator_only(user_input, curator_history, stream=True)
                except KeyboardInterrupt:
                    print("\n\n\033[1;31mCurator interrupted by user.\033[0m")
                    print("Returning to input...\n")
                    print_header()
                    continue
                
                if "error" in curator_result:
                    print(f"\n\033[1;31mError: {curator_result['error']}\033[0m")
                    continue
                
                # Output already streamed, no need to print again
                
                curator_history.append({"role": "assistant", "content": curator_result['output']})
                
                # Check if Curator is asking for confirmation
                if curator_result.get("asking_confirmation"):
                    waiting_for_confirmation = True
                    # Try to extract refined query from Curator output
                    output = curator_result['output']
                    if "refined query ready:" in output.lower():
                        parts = output.split("refined query ready:", 1)
                        if len(parts) > 1:
                            refined_query = parts[1].split("\n")[0].strip().strip('"').strip("'")
                    if not refined_query:
                        refined_query = user_input  # Fallback to original
                    
                    print("\n" + "-"*60)
                    continue  # Wait for user's yes/no response
                else:
                    # Curator is still refining, continue conversation
                    # Clean return to prompt
                    continue

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
