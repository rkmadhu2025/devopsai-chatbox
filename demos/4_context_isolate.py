"""
Demo 4: Context ISOLATE - Context Isolation and Separation

This demo shows:
- How to maintain separate conversation contexts
- Preventing context leakage between different tasks
- Managing multiple independent conversations
- When and why to isolate contexts
"""

import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from autogen import ConversableAgent
from utils import (
    print_header,
    print_section,
    visualize_tokens,
    estimate_tokens_for_messages,
    get_context_window_size,
    print_info,
    print_success,
    print_warning,
    count_tokens
)
from colorama import Fore, Style


def load_config():
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found.")
        sys.exit(1)


def demo_context_isolate():
    """Demonstrate context isolation."""
    print_header("DEMO 4: Context ISOLATE - Maintaining Separate Contexts")

    # Load configuration
    config = load_config()
    model = config.get('model', 'gpt-3.5-turbo')
    context_window = get_context_window_size(model)

    print_section("Scenario: Multiple Independent Tasks")

    # Configure LLM
    llm_config = {
        "config_list": [{
            "model": model,
            "api_key": config['api_key'],
        }],
        "temperature": config.get('temperature', 0.7),
    }

    # === Scenario 1: WITHOUT Isolation (Context Leakage) ===
    print_section("WITHOUT Isolation: Context Leakage Problem")

    print_info("Creating a single assistant for multiple unrelated tasks...")

    # Single assistant handling multiple topics
    shared_assistant = ConversableAgent(
        name="SharedAssistant",
        system_message="You are a helpful assistant.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    shared_user = ConversableAgent(
        name="SharedUser",
        llm_config=False,
        human_input_mode="NEVER",
    )

    # Task 1: Python question
    print(f"\n{Fore.CYAN}Task 1: Python Programming{Style.RESET_ALL}")
    print("─" * 40)
    question1 = "Explain Python list comprehensions briefly."
    print(f"User: {question1}")

    shared_user.send(message=question1, recipient=shared_assistant, request_reply=True)
    response1 = shared_assistant.chat_messages[shared_user][-1]['content']
    print(f"Assistant: {response1[:150]}...\n")

    # Task 2: Recipe question (completely different topic)
    print(f"\n{Fore.CYAN}Task 2: Cooking Recipe{Style.RESET_ALL}")
    print("─" * 40)
    question2 = "How do I make chocolate chip cookies?"
    print(f"User: {question2}")

    shared_user.send(message=question2, recipient=shared_assistant, request_reply=True)
    response2 = shared_assistant.chat_messages[shared_user][-1]['content']
    print(f"Assistant: {response2[:150]}...\n")

    # Task 3: Back to Python (but context is polluted)
    print(f"\n{Fore.CYAN}Task 3: Back to Python{Style.RESET_ALL}")
    print("─" * 40)
    question3 = "Show me an example."
    print(f"User: {question3}")

    shared_user.send(message=question3, recipient=shared_assistant, request_reply=True)
    response3 = shared_assistant.chat_messages[shared_user][-1]['content']
    print(f"Assistant: {response3[:150]}...\n")

    # Analyze the problem
    shared_history = shared_assistant.chat_messages[shared_user]
    shared_tokens = estimate_tokens_for_messages(shared_history, model)

    print_warning("PROBLEM: 'Show me an example' is ambiguous!")
    print_warning("Context includes BOTH Python AND cooking topics")
    print(f"\n{Fore.RED}All messages in one context: {len(shared_history)} messages, {shared_tokens:,} tokens{Style.RESET_ALL}")

    visualize_tokens(shared_tokens, context_window, "Shared Context (No Isolation)")

    # === Scenario 2: WITH Isolation (Separate Contexts) ===
    print_section("WITH Isolation: Separate Contexts Solution")

    print_success("Creating separate assistants for each task domain...")

    # Separate assistant for Python
    python_assistant = ConversableAgent(
        name="PythonAssistant",
        system_message="You are a Python programming expert. Only discuss Python topics.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    python_user = ConversableAgent(
        name="PythonUser",
        llm_config=False,
        human_input_mode="NEVER",
    )

    # Separate assistant for Cooking
    cooking_assistant = ConversableAgent(
        name="CookingAssistant",
        system_message="You are a cooking expert. Only discuss cooking and recipes.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    cooking_user = ConversableAgent(
        name="CookingUser",
        llm_config=False,
        human_input_mode="NEVER",
    )

    # Task 1: Python (isolated context)
    print(f"\n{Fore.GREEN}Isolated Context 1: Python Programming{Style.RESET_ALL}")
    print("─" * 40)
    print(f"User: {question1}")

    python_user.send(message=question1, recipient=python_assistant, request_reply=True)
    iso_response1 = python_assistant.chat_messages[python_user][-1]['content']
    print(f"Python Assistant: {iso_response1[:150]}...\n")

    python_tokens = estimate_tokens_for_messages(python_assistant.chat_messages[python_user], model)

    # Task 2: Cooking (separate isolated context)
    print(f"\n{Fore.GREEN}Isolated Context 2: Cooking{Style.RESET_ALL}")
    print("─" * 40)
    print(f"User: {question2}")

    cooking_user.send(message=question2, recipient=cooking_assistant, request_reply=True)
    iso_response2 = cooking_assistant.chat_messages[cooking_user][-1]['content']
    print(f"Cooking Assistant: {iso_response2[:150]}...\n")

    cooking_tokens = estimate_tokens_for_messages(cooking_assistant.chat_messages[cooking_user], model)

    # Task 3: Back to Python (clean context)
    print(f"\n{Fore.GREEN}Back to Isolated Context 1: Python{Style.RESET_ALL}")
    print("─" * 40)
    print(f"User: {question3}")

    python_user.send(message=question3, recipient=python_assistant, request_reply=True)
    iso_response3 = python_assistant.chat_messages[python_user][-1]['content']
    print(f"Python Assistant: {iso_response3[:150]}...\n")

    python_tokens_final = estimate_tokens_for_messages(python_assistant.chat_messages[python_user], model)

    print_success("SOLUTION: 'Show me an example' is clear in Python context!")
    print_success("Each context maintains only relevant information")

    # Visualize isolated contexts
    print("\n")
    visualize_tokens(python_tokens_final, context_window, "Python Context (Isolated)")
    visualize_tokens(cooking_tokens, context_window, "Cooking Context (Isolated)")

    # Comparison
    print_section("Isolation Benefits Comparison")

    print(f"{'Approach':<25} {'Total Tokens':<15} {'Contexts':<15} {'Clarity':<15}")
    print('─' * 80)
    print(f"{'Without Isolation':<25} {shared_tokens:<15,} {'1 (mixed)':<15} {'Ambiguous':<15}")
    print(f"{'With Isolation':<25} {python_tokens_final + cooking_tokens:<15,} {'2 (separate)':<15} {'Clear':<15}")

    # Use cases for isolation
    print_section("When to Use Context Isolation")

    use_cases = [
        ("Multi-tenant applications", "Each user/tenant needs isolated context"),
        ("Different task domains", "Prevent cross-contamination of unrelated topics"),
        ("Security/Privacy", "Keep sensitive information separate"),
        ("Parallel processing", "Handle multiple requests independently"),
        ("A/B testing", "Compare responses with different contexts"),
        ("Role-based agents", "Specialized agents with domain expertise"),
    ]

    for use_case, description in use_cases:
        print(f"✓ {Fore.CYAN}{use_case}{Style.RESET_ALL}")
        print(f"  → {description}\n")

    # Implementation strategies
    print_section("Implementation Strategies")

    print(f"{Fore.YELLOW}1. Separate Agent Instances{Style.RESET_ALL}")
    print("   - Create distinct agent objects for each context")
    print("   - Each agent maintains its own conversation history")
    print("   - Best for: Different domains or users\n")

    print(f"{Fore.YELLOW}2. Session-Based Isolation{Style.RESET_ALL}")
    print("   - Use session IDs to separate conversations")
    print("   - Same agent, different conversation threads")
    print("   - Best for: Same user, multiple sessions\n")

    print(f"{Fore.YELLOW}3. Clear History Method{Style.RESET_ALL}")
    print("   - Explicitly clear chat history between tasks")
    print("   - Start fresh for each new context")
    print("   - Best for: Sequential independent tasks\n")

    print(f"{Fore.YELLOW}4. Context Managers{Style.RESET_ALL}")
    print("   - Use context manager pattern to scope conversations")
    print("   - Automatic cleanup after context exit")
    print("   - Best for: Temporary isolated operations\n")

    # Trade-offs
    print_section("Isolation Trade-offs")

    print(f"{Fore.GREEN}Advantages:{Style.RESET_ALL}")
    print("✓ Prevents context contamination")
    print("✓ Clearer, more focused responses")
    print("✓ Better token efficiency per context")
    print("✓ Improved security and privacy")
    print("✓ Easier debugging and testing")

    print(f"\n{Fore.RED}Disadvantages:{Style.RESET_ALL}")
    print("✗ Cannot share information between contexts")
    print("✗ More memory usage (multiple contexts)")
    print("✗ Increased complexity in architecture")
    print("✗ Requires explicit context switching")

    # Best practices
    print_section("Best Practices")

    print("1. Identify natural boundaries for isolation")
    print("   → User sessions, task types, security levels")
    print("\n2. Use system messages to reinforce isolation")
    print("   → Set clear agent roles and domains")
    print("\n3. Implement context switching explicitly")
    print("   → Make it clear when changing contexts")
    print("\n4. Monitor token usage per context")
    print("   → Prevent any single context from growing too large")
    print("\n5. Consider hybrid approaches")
    print("   → Isolate by default, share when needed")
    print("\n6. Document context boundaries")
    print("   → Help developers understand the isolation strategy")

    # Code example
    print_section("Code Pattern Example")

    code_example = """
# Pattern 1: Separate Agents
python_agent = ConversableAgent(name="Python", system_message="Python expert")
cooking_agent = ConversableAgent(name="Cooking", system_message="Cooking expert")

# Pattern 2: Clear History
agent.clear_history()  # Start fresh context

# Pattern 3: Session-based
def get_agent_for_session(session_id):
    if session_id not in agents:
        agents[session_id] = create_new_agent()
    return agents[session_id]
"""

    print(code_example)


if __name__ == "__main__":
    demo_context_isolate()
