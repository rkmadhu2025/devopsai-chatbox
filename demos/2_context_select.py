"""
Demo 2: Context SELECT - Selective Message Passing

This demo shows:
- How to filter relevant messages from conversation history
- Reducing unnecessary context
- Maintaining conversation coherence with less context
- Token savings from selective context
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
    print_comparison,
    estimate_tokens_for_messages,
    get_context_window_size,
    print_info,
    print_success
)


def load_config():
    """Load configuration from config.json."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found.")
        sys.exit(1)


def select_relevant_messages(messages, keywords=None, max_messages=5, keep_system=True):
    """
    Select relevant messages from conversation history.

    Args:
        messages: List of message dictionaries
        keywords: List of keywords to match (if None, use recency)
        max_messages: Maximum number of messages to keep
        keep_system: Whether to always keep system messages

    Returns:
        Filtered list of messages
    """
    selected = []

    # Always keep system message if requested
    if keep_system:
        system_msgs = [m for m in messages if m.get('role') == 'system']
        selected.extend(system_msgs)

    # Get non-system messages
    other_msgs = [m for m in messages if m.get('role') != 'system']

    if keywords:
        # Select messages containing keywords
        relevant = []
        for msg in other_msgs:
            content = msg.get('content', '').lower()
            if any(keyword.lower() in content for keyword in keywords):
                relevant.append(msg)

        # If we found relevant messages, use them; otherwise fall back to recent
        if relevant:
            selected.extend(relevant[-max_messages:])
        else:
            selected.extend(other_msgs[-max_messages:])
    else:
        # Just take the most recent messages
        selected.extend(other_msgs[-max_messages:])

    return selected


def demo_context_select():
    """Demonstrate selective context passing."""
    print_header("DEMO 2: Context SELECT - Selective Message Passing")

    # Load configuration
    config = load_config()
    model = config.get('model', 'gpt-3.5-turbo')
    context_window = get_context_window_size(model)

    print_section("Scenario: Long Conversation with Topic Changes")

    # Configure LLM
    llm_config = {
        "config_list": [{
            "model": model,
            "api_key": config['api_key'],
        }],
        "temperature": config.get('temperature', 0.7),
    }

    # Create a conversation history manually to demonstrate selection
    conversation_history = [
        {"role": "system", "content": "You are a helpful programming assistant."},
        {"role": "user", "content": "How do I read a file in Python?"},
        {"role": "assistant", "content": "You can read a file using open() function: with open('file.txt', 'r') as f: content = f.read()"},
        {"role": "user", "content": "What about writing to a file?"},
        {"role": "assistant", "content": "Use 'w' mode: with open('file.txt', 'w') as f: f.write('content')"},
        {"role": "user", "content": "How do I sort a Python list?"},
        {"role": "assistant", "content": "Use the sort() method or sorted() function: my_list.sort() or sorted_list = sorted(my_list)"},
        {"role": "user", "content": "What's the difference between sort() and sorted()?"},
        {"role": "assistant", "content": "sort() modifies the list in-place, sorted() returns a new sorted list without modifying the original."},
        {"role": "user", "content": "How do I reverse a list?"},
        {"role": "assistant", "content": "Use reverse() method or slicing: my_list.reverse() or reversed_list = my_list[::-1]"},
        {"role": "user", "content": "Can you explain list comprehensions?"},
        {"role": "assistant", "content": "List comprehensions provide a concise way to create lists: [x*2 for x in range(10)] creates [0,2,4,6,8,10,12,14,16,18]"},
    ]

    # Calculate original token count
    original_tokens = estimate_tokens_for_messages(conversation_history, model)

    print_info(f"Original conversation: {len(conversation_history)} messages")
    visualize_tokens(original_tokens, context_window, "Original Context")

    # Scenario 1: Recent messages only
    print_section("Strategy 1: Keep Only Recent Messages")

    recent_messages = select_relevant_messages(
        conversation_history,
        max_messages=4,  # Keep last 4 non-system messages
        keep_system=True
    )

    recent_tokens = estimate_tokens_for_messages(recent_messages, model)

    print(f"Selected messages: {len(recent_messages)}")
    print("\nSelected conversation:")
    for msg in recent_messages:
        role = msg['role']
        content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
        print(f"  [{role}] {content}")

    print("\n")
    visualize_tokens(recent_tokens, context_window, "Reduced Context (Recent)")

    print_comparison(
        {"messages": len(conversation_history), "tokens": original_tokens},
        {"messages": len(recent_messages), "tokens": recent_tokens}
    )

    # Scenario 2: Keyword-based selection
    print_section("Strategy 2: Keyword-Based Selection")

    # User wants to ask about lists, so select list-related messages
    print_info("User's next question will be about 'lists', selecting relevant messages...")

    keyword_messages = select_relevant_messages(
        conversation_history,
        keywords=["list", "sort", "reverse"],
        max_messages=6,
        keep_system=True
    )

    keyword_tokens = estimate_tokens_for_messages(keyword_messages, model)

    print(f"\nSelected messages: {len(keyword_messages)}")
    print("\nSelected conversation (list-related):")
    for msg in keyword_messages:
        role = msg['role']
        content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
        print(f"  [{role}] {content}")

    print("\n")
    visualize_tokens(keyword_tokens, context_window, "Reduced Context (Keyword)")

    print_comparison(
        {"messages": len(conversation_history), "tokens": original_tokens},
        {"messages": len(keyword_messages), "tokens": keyword_tokens}
    )

    # Scenario 3: Minimal context (system + last exchange only)
    print_section("Strategy 3: Minimal Context (System + Last Exchange)")

    minimal_messages = [conversation_history[0]]  # System message
    minimal_messages.extend(conversation_history[-2:])  # Last user-assistant exchange

    minimal_tokens = estimate_tokens_for_messages(minimal_messages, model)

    print(f"Selected messages: {len(minimal_messages)}")
    print("\nMinimal conversation:")
    for msg in minimal_messages:
        role = msg['role']
        content = msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content']
        print(f"  [{role}] {content}")

    print("\n")
    visualize_tokens(minimal_tokens, context_window, "Minimal Context")

    print_comparison(
        {"messages": len(conversation_history), "tokens": original_tokens},
        {"messages": len(minimal_messages), "tokens": minimal_tokens}
    )

    # Strategy comparison
    print_section("Strategy Comparison")

    print(f"{'Strategy':<30} {'Messages':<15} {'Tokens':<15} {'Savings':<15}")
    print('─' * 80)

    strategies = [
        ("Original (No Selection)", len(conversation_history), original_tokens, "0%"),
        ("Recent Messages", len(recent_messages), recent_tokens, f"{((original_tokens - recent_tokens) / original_tokens * 100):.1f}%"),
        ("Keyword-Based", len(keyword_messages), keyword_tokens, f"{((original_tokens - keyword_tokens) / original_tokens * 100):.1f}%"),
        ("Minimal Context", len(minimal_messages), minimal_tokens, f"{((original_tokens - minimal_tokens) / original_tokens * 100):.1f}%"),
    ]

    for strategy, msgs, tokens, savings in strategies:
        print(f"{strategy:<30} {msgs:<15} {tokens:<15,} {savings:<15}")

    # Key insights
    print_section("Key Insights")
    print_success("Selective context can reduce token usage by 40-80%")
    print("✓ Recent messages: Good for maintaining conversation flow")
    print("✓ Keyword-based: Best for topic-specific questions")
    print("✓ Minimal context: Maximum savings, but may lose context")
    print("✓ Always consider: relevance vs. coherence trade-off")
    print("✓ Keep system messages to maintain agent behavior")

    # Best practices
    print_section("Best Practices")
    print("1. Analyze the user's query to determine what context is needed")
    print("2. Use keyword matching for topic-specific questions")
    print("3. Keep recent messages for general conversation flow")
    print("4. Always preserve system messages")
    print("5. Monitor response quality when reducing context")
    print("6. Combine strategies: recent + keyword-matching")


if __name__ == "__main__":
    demo_context_select()
