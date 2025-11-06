"""
Simple Context Engineering Demo
Direct OpenAI implementation - easier to understand and explain!
"""

import json
import sys
import os
from openai import OpenAI
from utils import (
    print_header,
    print_section,
    visualize_tokens,
    print_comparison,
    estimate_tokens_for_messages,
    get_context_window_size,
    count_tokens,
    print_success,
    print_info,
    print_warning
)
from colorama import Fore, Style


def load_config():
    """Load configuration."""
    config_path = "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def demo_1_write():
    """Demo 1: Context WRITE - See how context grows"""
    print_header("DEMO 1: Context WRITE - Context Growth")

    config = load_config()
    client = OpenAI(api_key=config['api_key'])
    model = config['model']
    context_window = get_context_window_size(model)

    print_section("Starting Conversation with Token Tracking")

    # Conversation history
    messages = [
        {"role": "system", "content": "You are a helpful Python programming assistant. Keep responses concise (2-3 sentences)."}
    ]

    questions = [
        "What is a Python list?",
        "How do I append items to a list?",
        "What's the difference between append() and extend()?",
        "Can you show me a list comprehension example?",
        "How do I reverse a list?",
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n{Fore.YELLOW}{'═' * 80}")
        print(f"Turn {i}: {question}")
        print(f"{'═' * 80}{Style.RESET_ALL}\n")

        # Add user message
        messages.append({"role": "user", "content": question})

        # Get AI response
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )

        # Add assistant response
        assistant_msg = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_msg})

        # Count tokens
        total_tokens = estimate_tokens_for_messages(messages, model)

        print(f"{Fore.BLUE}Assistant:{Style.RESET_ALL} {assistant_msg}\n")

        # Visualize
        visualize_tokens(total_tokens, context_window, f"Turn {i} - Context Usage")

        # Warning
        percentage = (total_tokens / context_window) * 100
        if percentage > 70:
            print_warning(f"Context at {percentage:.1f}% - Consider management!")

        print(f"{Fore.CYAN}Messages: {len(messages)} | Tokens: {total_tokens:,}{Style.RESET_ALL}")

    print_section("Key Insight")
    print_success("Context grows with each exchange - management is essential!")
    print(f"Final context: {len(messages)} messages, {estimate_tokens_for_messages(messages, model):,} tokens\n")


def demo_2_select():
    """Demo 2: Context SELECT - Filter relevant messages"""
    print_header("DEMO 2: Context SELECT - Selective Filtering")

    config = load_config()
    model = config['model']
    context_window = get_context_window_size(model)

    # Sample long conversation
    full_conversation = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "How do I read a file in Python?"},
        {"role": "assistant", "content": "Use open() with 'r' mode: with open('file.txt', 'r') as f: content = f.read()"},
        {"role": "user", "content": "What about writing files?"},
        {"role": "assistant", "content": "Use 'w' mode: with open('file.txt', 'w') as f: f.write('content')"},
        {"role": "user", "content": "How do I sort a list?"},
        {"role": "assistant", "content": "Use my_list.sort() to sort in-place or sorted(my_list) for a new sorted list."},
        {"role": "user", "content": "How do I reverse a list?"},
        {"role": "assistant", "content": "Use my_list.reverse() or my_list[::-1] for slicing."},
        {"role": "user", "content": "What are list comprehensions?"},
        {"role": "assistant", "content": "Concise syntax: [x*2 for x in range(10)] creates [0,2,4,6,8,10,12,14,16,18]"},
    ]

    original_tokens = estimate_tokens_for_messages(full_conversation, model)

    print_section("Original Full Conversation")
    print(f"Messages: {len(full_conversation)}")
    visualize_tokens(original_tokens, context_window, "Full Context")

    # Strategy 1: Keep recent only
    print_section("Strategy 1: Keep Recent Messages Only")
    recent_messages = [full_conversation[0]] + full_conversation[-4:]  # System + last 4
    recent_tokens = estimate_tokens_for_messages(recent_messages, model)

    print(f"Kept: {len(recent_messages)} messages (last 4 exchanges)")
    visualize_tokens(recent_tokens, context_window, "Recent Context")

    print_comparison(
        {"messages": len(full_conversation), "tokens": original_tokens},
        {"messages": len(recent_messages), "tokens": recent_tokens}
    )

    # Strategy 2: Keyword-based
    print_section("Strategy 2: Keyword-Based Selection")
    keyword_messages = [full_conversation[0]]  # System
    keyword_messages += [m for m in full_conversation[1:] if 'list' in m['content'].lower()]
    keyword_tokens = estimate_tokens_for_messages(keyword_messages, model)

    print("Kept only 'list'-related messages:")
    for msg in keyword_messages[1:]:
        print(f"  • {msg['content'][:60]}...")

    print()
    visualize_tokens(keyword_tokens, context_window, "Keyword-Filtered Context")

    print_comparison(
        {"messages": len(full_conversation), "tokens": original_tokens},
        {"messages": len(keyword_messages), "tokens": keyword_tokens}
    )

    print_section("Key Insight")
    print_success("Selective filtering can save 40-80% tokens!")
    print("✓ Use recent messages for flow")
    print("✓ Use keywords for topic-specific queries\n")


def demo_3_compress():
    """Demo 3: Context COMPRESS - Summarize conversations"""
    print_header("DEMO 3: Context COMPRESS - Summarization")

    config = load_config()
    client = OpenAI(api_key=config['api_key'])
    model = config['model']
    context_window = get_context_window_size(model)

    # Long conversation
    long_conversation = [
        {"role": "user", "content": "How do I read a file in Python?"},
        {"role": "assistant", "content": "You can read a file using the open() function with 'r' mode. Use a with statement for automatic file closing: with open('file.txt', 'r') as f: content = f.read(). This reads the entire file into a string."},
        {"role": "user", "content": "What about writing to files?"},
        {"role": "assistant", "content": "For writing, use 'w' mode which creates a new file or overwrites existing: with open('file.txt', 'w') as f: f.write('your content'). Use 'a' mode to append instead of overwriting."},
        {"role": "user", "content": "How do I handle file paths?"},
        {"role": "assistant", "content": "Use the os.path or pathlib modules. pathlib is more modern: from pathlib import Path; file_path = Path('folder') / 'file.txt'. This handles different OS path separators automatically."},
        {"role": "user", "content": "What about reading line by line?"},
        {"role": "assistant", "content": "Use a for loop: with open('file.txt', 'r') as f: for line in f: print(line.strip()). Or use f.readlines() to get a list of all lines."},
    ]

    original_tokens = count_tokens(str(long_conversation), model)

    print_section("Original Detailed Conversation")
    print(f"Messages: {len(long_conversation)}")
    print(f"Sample:\n  User: {long_conversation[0]['content']}")
    print(f"  AI: {long_conversation[1]['content'][:100]}...\n")
    visualize_tokens(original_tokens, context_window, "Detailed Conversation")

    # Create summary
    print_section("Creating Summary...")
    conversation_text = "\n".join([f"{m['role']}: {m['content']}" for m in long_conversation])

    summary_response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": f"Summarize this conversation in 1-2 sentences, preserving key facts:\n\n{conversation_text}"
        }],
        temperature=0.5
    )

    summary = summary_response.choices[0].message.content
    summary_tokens = count_tokens(summary, model)

    print_success("Summary Created!")
    print(f"\n{Fore.GREEN}Summary:{Style.RESET_ALL} {summary}\n")
    visualize_tokens(summary_tokens, context_window, "Compressed Summary")

    print_comparison(
        {"messages": len(long_conversation), "tokens": original_tokens},
        {"messages": 1, "tokens": summary_tokens}
    )

    print_section("Key Insight")
    print_success("Compression can save 60-80% tokens!")
    print("✓ Summarize old messages")
    print("✓ Keep recent messages detailed\n")


def demo_4_isolate():
    """Demo 4: Context ISOLATE - Separate contexts"""
    print_header("DEMO 4: Context ISOLATE - Separation")

    config = load_config()
    client = OpenAI(api_key=config['api_key'])
    model = config['model']

    print_section("Problem: Mixed Context (Without Isolation)")

    # Shared context (problematic)
    shared_context = [
        {"role": "user", "content": "How do I sort a Python list?"},
        {"role": "assistant", "content": "Use my_list.sort() or sorted(my_list)."},
        {"role": "user", "content": "How do I make chocolate chip cookies?"},
        {"role": "assistant", "content": "Mix butter, sugar, eggs, flour, and chocolate chips. Bake at 350°F for 10-12 minutes."},
        {"role": "user", "content": "Show me an example."},  # AMBIGUOUS!
    ]

    print("Conversation history:")
    for msg in shared_context:
        role_color = Fore.GREEN if msg['role'] == 'user' else Fore.BLUE
        print(f"{role_color}[{msg['role'].upper()}]{Style.RESET_ALL} {msg['content']}")

    print(f"\n{Fore.RED}PROBLEM:{Style.RESET_ALL} 'Show me an example' is ambiguous!")
    print("  → Example of sorting? Or cookie recipe?")
    print(f"  → Context contains BOTH topics - confusion!\n")

    shared_tokens = estimate_tokens_for_messages(shared_context, model)
    print(f"Shared context tokens: {shared_tokens:,}\n")

    print_section("Solution: Isolated Contexts")

    # Separate contexts
    python_context = [
        {"role": "system", "content": "You are a Python expert."},
        {"role": "user", "content": "How do I sort a Python list?"},
        {"role": "assistant", "content": "Use my_list.sort() or sorted(my_list)."},
        {"role": "user", "content": "Show me an example."},
    ]

    cooking_context = [
        {"role": "system", "content": "You are a cooking expert."},
        {"role": "user", "content": "How do I make chocolate chip cookies?"},
        {"role": "assistant", "content": "Mix butter, sugar, eggs, flour, and chocolate chips. Bake at 350°F for 10-12 minutes."},
    ]

    print(f"{Fore.GREEN}Python Context (Isolated):{Style.RESET_ALL}")
    for msg in python_context:
        print(f"  • [{msg['role']}] {msg['content']}")

    print(f"\n{Fore.GREEN}Cooking Context (Isolated):{Style.RESET_ALL}")
    for msg in cooking_context:
        print(f"  • [{msg['role']}] {msg['content']}")

    python_tokens = estimate_tokens_for_messages(python_context, model)
    cooking_tokens = estimate_tokens_for_messages(cooking_context, model)

    print(f"\n{Fore.CYAN}Python tokens: {python_tokens:,}")
    print(f"Cooking tokens: {cooking_tokens:,}")
    print(f"Total: {python_tokens + cooking_tokens:,}{Style.RESET_ALL}\n")

    print_success("'Show me an example' is now CLEAR in Python context!")

    print_section("Key Insight")
    print_success("Isolation prevents context contamination!")
    print("✓ Separate users/sessions")
    print("✓ Separate task domains")
    print("✓ Clearer, more focused responses\n")


def main():
    """Run all demos."""
    print_header("CONTEXT ENGINEERING - SIMPLE DEMO")
    print(f"{Fore.CYAN}Visual demonstrations of 4 key techniques:{Style.RESET_ALL}\n")
    print("  1. WRITE    - Context growth tracking")
    print("  2. SELECT   - Selective message filtering")
    print("  3. COMPRESS - Conversation summarization")
    print("  4. ISOLATE  - Context separation\n")

    try:
        # Check config
        config = load_config()
        print_success(f"Configuration loaded: {config['model']}\n")

        # Run demos
        input("Press Enter to start Demo 1 (Context WRITE)...")
        demo_1_write()

        input("\nPress Enter to start Demo 2 (Context SELECT)...")
        demo_2_select()

        input("\nPress Enter to start Demo 3 (Context COMPRESS)...")
        demo_3_compress()

        input("\nPress Enter to start Demo 4 (Context ISOLATE)...")
        demo_4_isolate()

        # Summary
        print_header("ALL DEMOS COMPLETE!")
        print(f"{Fore.GREEN}You now understand Context Engineering!{Style.RESET_ALL}\n")
        print("Key Takeaways:")
        print("  ✓ WRITE: Monitor context growth constantly")
        print("  ✓ SELECT: Filter messages to reduce tokens 40-80%")
        print("  ✓ COMPRESS: Summarize to save 60-80% tokens")
        print("  ✓ ISOLATE: Separate contexts for clarity\n")

        print(f"{Fore.YELLOW}Combine these techniques for production apps!{Style.RESET_ALL}\n")

    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
