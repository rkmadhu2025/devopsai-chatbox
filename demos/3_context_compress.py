"""
Demo 3: Context COMPRESS - Context Compression Through Summarization

This demo shows:
- How to compress long conversations using summarization
- Maintaining key information while reducing tokens
- Using LLM to create conversation summaries
- Extending effective conversation length
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
    print_success,
    count_tokens
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


def create_conversation_summary(messages, llm_config, model):
    """
    Create a summary of conversation messages using an LLM.

    Args:
        messages: List of message dictionaries to summarize
        llm_config: LLM configuration
        model: Model name

    Returns:
        Summary message dictionary
    """
    # Create a summarizer agent
    summarizer = ConversableAgent(
        name="Summarizer",
        system_message="You are a summarization expert. Create concise summaries that preserve key information.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    # Format messages for summarization
    conversation_text = "\n".join([
        f"{msg['role']}: {msg['content']}"
        for msg in messages
        if msg['role'] != 'system'
    ])

    # Request summary
    summary_request = f"""Summarize the following conversation, preserving key facts, decisions, and context.
Be concise but include all important information:

{conversation_text}

Provide a summary in 2-3 sentences."""

    # Create a temporary user agent for the request
    temp_user = ConversableAgent(
        name="TempUser",
        llm_config=False,
        human_input_mode="NEVER",
    )

    # Get summary
    temp_user.send(message=summary_request, recipient=summarizer, request_reply=True)
    chat_history = summarizer.chat_messages[temp_user]
    summary = chat_history[-1]['content']

    return {
        "role": "system",
        "content": f"Previous conversation summary: {summary}"
    }


def demo_context_compress():
    """Demonstrate context compression through summarization."""
    print_header("DEMO 3: Context COMPRESS - Summarization Strategy")

    # Load configuration
    config = load_config()
    model = config.get('model', 'gpt-3.5-turbo')
    context_window = get_context_window_size(model)

    print_section("Scenario: Long Conversation Needing Compression")

    # Configure LLM
    llm_config = {
        "config_list": [{
            "model": model,
            "api_key": config['api_key'],
        }],
        "temperature": config.get('temperature', 0.7),
    }

    # Create a long conversation history
    conversation_history = [
        {"role": "system", "content": "You are a helpful Python programming tutor."},
        {"role": "user", "content": "I'm learning Python. Can you help me understand data structures?"},
        {"role": "assistant", "content": "Of course! Python has several built-in data structures: lists (ordered, mutable), tuples (ordered, immutable), dictionaries (key-value pairs), and sets (unordered, unique elements). Which would you like to explore first?"},
        {"role": "user", "content": "Let's start with lists. How do I create one?"},
        {"role": "assistant", "content": "You can create a list using square brackets: my_list = [1, 2, 3, 4, 5] or my_list = ['apple', 'banana', 'cherry']. Lists can contain any type of objects and can be nested."},
        {"role": "user", "content": "How do I add items to a list?"},
        {"role": "assistant", "content": "There are several methods: append() adds one item to the end, extend() adds multiple items, and insert() adds an item at a specific position. For example: my_list.append(6) or my_list.extend([7, 8, 9]) or my_list.insert(0, 'first')."},
        {"role": "user", "content": "What about removing items?"},
        {"role": "assistant", "content": "You can use: remove() to delete by value, pop() to remove by index (and return it), del to delete by index, or clear() to empty the list. Example: my_list.remove('apple') or item = my_list.pop(0) or del my_list[1]."},
        {"role": "user", "content": "How do I find items in a list?"},
        {"role": "assistant", "content": "Use the 'in' operator to check existence: 'apple' in my_list returns True/False. Use index() to find position: my_list.index('apple') returns the index. Use count() to count occurrences: my_list.count('apple')."},
        {"role": "user", "content": "Can you show me list comprehensions?"},
        {"role": "assistant", "content": "List comprehensions provide a concise way to create lists. Syntax: [expression for item in iterable if condition]. Examples: squares = [x**2 for x in range(10)], evens = [x for x in range(20) if x % 2 == 0], upper = [s.upper() for s in ['a', 'b', 'c']]."},
    ]

    # Calculate original token count
    original_tokens = estimate_tokens_for_messages(conversation_history, model)
    original_message_count = len(conversation_history)

    print_info(f"Original conversation: {original_message_count} messages")
    print_info(f"Total tokens: {original_tokens:,}")
    print("\n")
    visualize_tokens(original_tokens, context_window, "Original Context")

    # Show original messages
    print_section("Original Conversation (Sample)")
    for i, msg in enumerate(conversation_history[:5], 1):
        role = msg['role']
        content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
        tokens = count_tokens(msg['content'], model)
        print(f"{i}. [{role.upper()}] ({tokens} tokens)")
        print(f"   {content}\n")

    # Strategy 1: Compress old messages
    print_section("Strategy 1: Compress Old Messages, Keep Recent Ones")

    print_info("Compressing first 6 messages, keeping last 5 as-is...")

    # Messages to compress (exclude system message, compress first few exchanges)
    messages_to_compress = conversation_history[1:7]  # Skip system, take first 6
    recent_messages = conversation_history[7:]  # Keep last 4

    print(f"\nCreating summary of {len(messages_to_compress)} messages...")

    # Create summary
    summary_message = create_conversation_summary(messages_to_compress, llm_config, model)

    print_success("Summary created!")
    print(f"\nSummary ({count_tokens(summary_message['content'], model)} tokens):")
    print(f"{summary_message['content']}\n")

    # Build compressed context
    compressed_history_1 = [conversation_history[0], summary_message] + recent_messages

    compressed_tokens_1 = estimate_tokens_for_messages(compressed_history_1, model)

    visualize_tokens(compressed_tokens_1, context_window, "Compressed Context (Strategy 1)")

    print_comparison(
        {"messages": original_message_count, "tokens": original_tokens},
        {"messages": len(compressed_history_1), "tokens": compressed_tokens_1}
    )

    # Strategy 2: Aggressive compression - summarize everything except system and last message
    print_section("Strategy 2: Aggressive Compression")

    print_info("Summarizing entire conversation except system and last exchange...")

    # Compress all but system and last 2 messages
    messages_to_compress_2 = conversation_history[1:-2]
    last_messages = conversation_history[-2:]

    print(f"\nCreating summary of {len(messages_to_compress_2)} messages...")

    # Create summary
    summary_message_2 = create_conversation_summary(messages_to_compress_2, llm_config, model)

    print_success("Aggressive summary created!")
    print(f"\nSummary ({count_tokens(summary_message_2['content'], model)} tokens):")
    print(f"{summary_message_2['content']}\n")

    # Build aggressively compressed context
    compressed_history_2 = [conversation_history[0], summary_message_2] + last_messages

    compressed_tokens_2 = estimate_tokens_for_messages(compressed_history_2, model)

    visualize_tokens(compressed_tokens_2, context_window, "Compressed Context (Strategy 2)")

    print_comparison(
        {"messages": original_message_count, "tokens": original_tokens},
        {"messages": len(compressed_history_2), "tokens": compressed_tokens_2}
    )

    # Strategy comparison
    print_section("Compression Strategy Comparison")

    print(f"{'Strategy':<35} {'Messages':<12} {'Tokens':<12} {'Savings':<12}")
    print('─' * 80)

    strategies = [
        ("Original (No Compression)", original_message_count, original_tokens, "0%"),
        ("Partial Compression", len(compressed_history_1), compressed_tokens_1,
         f"{((original_tokens - compressed_tokens_1) / original_tokens * 100):.1f}%"),
        ("Aggressive Compression", len(compressed_history_2), compressed_tokens_2,
         f"{((original_tokens - compressed_tokens_2) / original_tokens * 100):.1f}%"),
    ]

    for strategy, msgs, tokens, savings in strategies:
        print(f"{strategy:<35} {msgs:<12} {tokens:<12,} {savings:<12}")

    # Key insights
    print_section("Key Insights")
    print_success("Compression can reduce token usage by 30-60%")
    print("✓ Summarization preserves key information in fewer tokens")
    print("✓ Keep recent messages for conversation flow")
    print("✓ Compress older messages that are still relevant")
    print("✓ Use LLM-based summarization for quality")
    print("✓ Balance between compression and information loss")

    # Best practices
    print_section("Best Practices for Context Compression")
    print("1. Compress old messages, keep recent ones verbatim")
    print("2. Use clear summarization prompts")
    print("3. Preserve key facts, decisions, and entities")
    print("4. Consider sliding window: summarize, add new, repeat")
    print("5. Test summary quality with follow-up questions")
    print("6. Store original messages if recovery needed")
    print("7. Combine with selection for maximum efficiency")

    # When to use compression
    print_section("When to Use Compression")
    print("✓ Long conversations approaching token limits")
    print("✓ Multi-session conversations needing history")
    print("✓ Complex projects with extensive context")
    print("✓ Cost-sensitive applications")
    print("✗ Don't compress if details are critical")
    print("✗ Don't compress very recent messages")


if __name__ == "__main__":
    demo_context_compress()
