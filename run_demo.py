"""
Auto-run Context Engineering Demo
Non-interactive version for easy demonstration
"""

import json
import sys
import io
from openai import OpenAI
from utils import *
from colorama import Fore, Style
import time

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def load_config():
    with open("config.json", 'r', encoding='utf-8') as f:
        return json.load(f)


print_header("CONTEXT ENGINEERING DEMO")
print(f"{Fore.CYAN}Demonstrating 4 key context management techniques{Style.RESET_ALL}\n")

config = load_config()
client = OpenAI(api_key=config['api_key'])
model = config['model']
context_window = get_context_window_size(model)

print_success(f"Using model: {model} (Context: {context_window:,} tokens)\n")
time.sleep(1)

# ============================================================================
# DEMO 1: CONTEXT WRITE - Growth Tracking
# ============================================================================
print_header("DEMO 1: WRITE - Context Growth Tracking")
print_info("Showing how context accumulates with each message...\n")

messages = [{"role": "system", "content": "You are a concise Python tutor."}]

questions = [
    "What is a Python list in one sentence?",
    "How do I append to a list?",
    "Show me a quick list comprehension example.",
]

for i, q in enumerate(questions, 1):
    print(f"{Fore.YELLOW}Turn {i}: {q}{Style.RESET_ALL}")

    messages.append({"role": "user", "content": q})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=100
    )

    answer = response.choices[0].message.content
    messages.append({"role": "assistant", "content": answer})

    print(f"{Fore.BLUE}AI:{Style.RESET_ALL} {answer}\n")

    tokens = estimate_tokens_for_messages(messages, model)
    visualize_tokens(tokens, context_window, f"After Turn {i}")

print_success(f"Context grew from 0 to {estimate_tokens_for_messages(messages, model):,} tokens!")
print_info("Key insight: Context accumulates - monitoring is essential\n")
time.sleep(2)

# ============================================================================
# DEMO 2: CONTEXT SELECT - Filtering
# ============================================================================
print_header("DEMO 2: SELECT - Selective Filtering")
print_info("Reducing context by selecting only relevant messages...\n")

full_conv = [
    {"role": "system", "content": "Assistant"},
    {"role": "user", "content": "How do I read a file in Python?"},
    {"role": "assistant", "content": "Use open() with 'r' mode"},
    {"role": "user", "content": "How do I sort a Python list?"},
    {"role": "assistant", "content": "Use my_list.sort() or sorted(my_list)"},
    {"role": "user", "content": "How do I reverse a list?"},
    {"role": "assistant", "content": "Use my_list.reverse() or [::-1]"},
    {"role": "user", "content": "What are list comprehensions?"},
    {"role": "assistant", "content": "[x*2 for x in range(10)] syntax"},
]

original_tokens = estimate_tokens_for_messages(full_conv, model)
print(f"Original: {len(full_conv)} messages")
visualize_tokens(original_tokens, context_window, "Full Conversation")

# Select only list-related messages
selected = [full_conv[0]]  # System
selected += [m for m in full_conv[1:] if 'list' in m['content'].lower()]
selected_tokens = estimate_tokens_for_messages(selected, model)

print(f"\n{Fore.GREEN}Selected: {len(selected)} list-related messages{Style.RESET_ALL}")
visualize_tokens(selected_tokens, context_window, "Filtered (Lists only)")

print_comparison(
    {"messages": len(full_conv), "tokens": original_tokens},
    {"messages": len(selected), "tokens": selected_tokens}
)

print_success("Selective filtering saved tokens while keeping relevance!")
print_info("Key insight: Filter by keywords or recency to reduce size\n")
time.sleep(2)

# ============================================================================
# DEMO 3: CONTEXT COMPRESS - Summarization
# ============================================================================
print_header("DEMO 3: COMPRESS - Summarization")
print_info("Compressing long conversations via summarization...\n")

long_text = """User: How do I read files in Python?
Assistant: Use open() with 'r' mode. Example: with open('file.txt', 'r') as f: content = f.read()
User: What about writing?
Assistant: Use 'w' mode for writing, 'a' for appending: with open('file.txt', 'w') as f: f.write('text')
User: How do I handle paths?
Assistant: Use pathlib: from pathlib import Path; p = Path('folder') / 'file.txt'"""

original_size = count_tokens(long_text, model)
print(f"Original conversation:\n{long_text[:200]}...\n")
print(f"Original size: {original_size:,} tokens\n")

# Create summary
summary_response = client.chat.completions.create(
    model=model,
    messages=[{
        "role": "user",
        "content": f"Summarize in 1 sentence:\n{long_text}"
    }],
    temperature=0.5
)

summary = summary_response.choices[0].message.content
summary_size = count_tokens(summary, model)

print(f"{Fore.GREEN}Summary:{Style.RESET_ALL} {summary}\n")
print(f"Compressed size: {summary_size:,} tokens\n")

print_comparison(
    {"messages": 6, "tokens": original_size},
    {"messages": 1, "tokens": summary_size}
)

print_success("Summarization preserved key info with fewer tokens!")
print_info("Key insight: Compress old messages, keep recent ones detailed\n")
time.sleep(2)

# ============================================================================
# DEMO 4: CONTEXT ISOLATE - Separation
# ============================================================================
print_header("DEMO 4: ISOLATE - Context Separation")
print_info("Preventing context contamination through isolation...\n")

# Problem: Mixed context
print(f"{Fore.RED}PROBLEM: Mixed Context{Style.RESET_ALL}")
mixed = [
    "User: How do I sort a Python list?",
    "AI: Use my_list.sort()",
    "User: How do I make cookies?",
    "AI: Mix butter, sugar, flour, bake at 350F",
    "User: Show me an example.",  # AMBIGUOUS!
]
for msg in mixed:
    print(f"  {msg}")

print(f"\n{Fore.RED}[!] 'Show me an example' is AMBIGUOUS - sorting or cookies?{Style.RESET_ALL}\n")

# Solution: Isolated contexts
print(f"{Fore.GREEN}SOLUTION: Separate Contexts{Style.RESET_ALL}")

python_ctx = [
    "[Python Context]",
    "User: How do I sort a Python list?",
    "AI: Use my_list.sort()",
    "User: Show me an example.",  # NOW CLEAR!
]

cooking_ctx = [
    "[Cooking Context]",
    "User: How do I make cookies?",
    "AI: Mix butter, sugar, flour, bake at 350F",
]

print(f"\n{Fore.CYAN}Python Context (Isolated):{Style.RESET_ALL}")
for msg in python_ctx:
    print(f"  {msg}")

print(f"\n{Fore.CYAN}Cooking Context (Isolated):{Style.RESET_ALL}")
for msg in cooking_ctx:
    print(f"  {msg}")

print(f"\n{Fore.GREEN}[OK] 'Show me an example' is now CLEAR in Python context!{Style.RESET_ALL}\n")

print_success("Isolation prevents confusion between different topics!")
print_info("Key insight: Separate contexts for users/sessions/domains\n")
time.sleep(2)

# ============================================================================
# SUMMARY
# ============================================================================
print_header("ALL DEMOS COMPLETE!")
print(f"{Fore.GREEN}You now understand the 4 context engineering techniques!{Style.RESET_ALL}\n")

print("Summary of Techniques:\n")
print(f"{Fore.CYAN}1. WRITE{Style.RESET_ALL}    - Monitor context growth constantly")
print(f"              Track tokens to avoid hitting limits\n")

print(f"{Fore.CYAN}2. SELECT{Style.RESET_ALL}   - Filter messages intelligently")
print(f"              Savings: 40-80% by selecting relevant context\n")

print(f"{Fore.CYAN}3. COMPRESS{Style.RESET_ALL} - Summarize long conversations")
print(f"              Savings: 60-80% while preserving key information\n")

print(f"{Fore.CYAN}4. ISOLATE{Style.RESET_ALL}  - Separate different contexts")
print(f"              Prevents contamination, improves clarity\n")

print(f"\n{Fore.YELLOW}Production Tip: Combine all 4 techniques for optimal results!{Style.RESET_ALL}\n")

print_success("Demo complete! Check the code to see implementation details.")
print_info(f"Approximate API cost for this demo: $0.01-0.03 ({model})\n")
