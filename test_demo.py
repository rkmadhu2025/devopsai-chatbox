"""Quick test of Demo 1 imports and basic functionality."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("Testing Demo 1 imports...")

try:
    from autogen import ConversableAgent
    print("[OK] ConversableAgent imported")
except Exception as e:
    print(f"[ERROR] ConversableAgent import failed: {e}")
    sys.exit(1)

try:
    from utils import (
        print_header,
        print_section,
        visualize_tokens,
        print_messages,
        count_tokens,
        estimate_tokens_for_messages,
        get_context_window_size
    )
    print("[OK] Utils imported")
except Exception as e:
    print(f"[ERROR] Utils import failed: {e}")
    sys.exit(1)

try:
    import json
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    print(f"[OK] Config loaded - Model: {config.get('model', 'unknown')}")
except Exception as e:
    print(f"[ERROR] Config loading failed: {e}")
    sys.exit(1)

try:
    # Test creating an agent (without API call)
    test_agent = ConversableAgent(
        name="TestAgent",
        system_message="Test",
        llm_config=False,
        human_input_mode="NEVER",
    )
    print(f"[OK] Agent created successfully: {test_agent.name}")
except Exception as e:
    print(f"[ERROR] Agent creation failed: {e}")
    sys.exit(1)

try:
    # Test token counting
    test_text = "Hello, this is a test message."
    token_count = count_tokens(test_text, "gpt-3.5-turbo")
    print(f"[OK] Token counting works: '{test_text}' = {token_count} tokens")
except Exception as e:
    print(f"[ERROR] Token counting failed: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)
print("\nDemo 1 is ready to run!")
