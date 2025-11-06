"""
Demo 1: Context WRITE - Understanding Context Growth and Token Tracking

This demo shows:
- How context grows with each message
- Real-time token counting
- Context window usage visualization
- Impact of conversation length on token consumption
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
    print_messages,
    count_tokens,
    estimate_tokens_for_messages,
    get_context_window_size
)


def load_config():
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found. Please copy config.example.json to config.json and add your API key.")
        sys.exit(1)


def demo_context_write():
    """Demonstrate context writing and token tracking."""
    print_header("DEMO 1: Context WRITE - Understanding Context Growth")

    # Load configuration
    config = load_config()
    model = config.get('model', 'gpt-3.5-turbo')
    context_window = get_context_window_size(model)

    print_section("Configuration")
    print(f"Model: {model}")
    print(f"Context Window: {context_window:,} tokens")
    print(f"Max response tokens: {config.get('max_tokens', 1000)}")

    # Configure LLM
    llm_config = {
        "config_list": [{
            "model": model,
            "api_key": config['api_key'],
        }],
        "temperature": config.get('temperature', 0.7),
    }

    # Create agents
    print_section("Creating Agents")

    user = ConversableAgent(
        name="User",
        system_message="You are a user asking questions about Python programming.",
        llm_config=False,
        human_input_mode="NEVER",
    )

    assistant = ConversableAgent(
        name="Assistant",
        system_message="You are a helpful AI assistant that answers programming questions concisely.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    print("✓ User agent created")
    print("✓ Assistant agent created")

    # Simulate a growing conversation
    print_section("Simulating Conversation with Token Tracking")

    questions = [
        "What is a Python list?",
        "How do I append items to a list?",
        "What's the difference between append() and extend()?",
        "Can you show me an example of list comprehension?",
        "How do I sort a list in reverse order?",
        "What are some common list methods I should know?",
    ]

    # Track token growth
    token_history = []

    for i, question in enumerate(questions, 1):
        print(f"\n{'━' * 80}")
        print(f"Turn {i}: {question}")
        print('━' * 80)

        # User asks question
        user.send(message=question, recipient=assistant, request_reply=True)

        # Get chat history
        chat_history = assistant.chat_messages[user]

        # Count tokens
        total_tokens = estimate_tokens_for_messages(chat_history, model)
        token_history.append({
            'turn': i,
            'tokens': total_tokens,
            'messages': len(chat_history)
        })

        # Visualize token usage
        visualize_tokens(total_tokens, context_window, f"Turn {i} - Token Usage")

        # Show last exchange
        if len(chat_history) >= 2:
            last_msg = chat_history[-1]
            print(f"Assistant's response ({count_tokens(last_msg['content'], model)} tokens):")
            print(f"{last_msg['content']}\n")

        # Warning if approaching limit
        percentage = (total_tokens / context_window) * 100
        if percentage > 70:
            print(f"⚠️  WARNING: Context usage at {percentage:.1f}% - Consider context management!")
        elif percentage > 50:
            print(f"ℹ️  INFO: Context usage at {percentage:.1f}% - Monitoring recommended")

    # Show final statistics
    print_section("Context Growth Analysis")

    print("Token Growth Over Conversation:")
    print(f"{'Turn':<10} {'Messages':<15} {'Tokens':<15} {'Growth':<15}")
    print('─' * 60)

    for i, entry in enumerate(token_history):
        growth = ""
        if i > 0:
            token_diff = entry['tokens'] - token_history[i-1]['tokens']
            growth = f"+{token_diff}"

        print(f"{entry['turn']:<10} {entry['messages']:<15} {entry['tokens']:<15,} {growth:<15}")

    # Final visualization
    print("\n")
    visualize_tokens(token_history[-1]['tokens'], context_window, "Final Context Usage")

    # Key insights
    print_section("Key Insights")
    print("✓ Context grows linearly with each user-assistant exchange")
    print("✓ Each message adds ~3-4 tokens for formatting overhead")
    print("✓ Longer responses consume more tokens")
    print("✓ Context accumulates - old messages remain unless managed")
    print(f"✓ After {len(questions)} turns: {token_history[-1]['tokens']:,} tokens used")
    print(f"✓ Remaining capacity: {context_window - token_history[-1]['tokens']:,} tokens")

    # Show complete conversation
    print_section("Complete Conversation History")
    print_messages(assistant.chat_messages[user], "All Messages", model)


if __name__ == "__main__":
    demo_context_write()
