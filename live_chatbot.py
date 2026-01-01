"""
Simple Live Chatbot with Token Tracking
Run: python live_chatbot.py
"""

import json
import os
from autogen import ConversableAgent
import tiktoken

def load_config():
    """Load config from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def count_tokens(text, model="gpt-3.5-turbo"):
    """Count tokens in text"""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def main():
    print("=" * 50)
    print("  LIVE CHATBOT with Token Tracking")
    print("=" * 50)
    print("Type 'quit' to exit, 'clear' to reset context\n")

    # Load configuration
    config = load_config()
    model = config.get('model', 'gpt-3.5-turbo')
    # Get context window from config, fallback to 4096
    context_windows = config.get('context_window', {})
    max_context = context_windows.get(model, config.get('max_tokens', 4096))

    # Configure LLM
    llm_config = {
        "config_list": [{
            "model": model,
            "api_key": config['api_key'],
        }],
        "temperature": config.get('temperature', 0.7),
    }

    # Create agents
    assistant = ConversableAgent(
        name="Assistant",
        system_message="You are a helpful AI assistant. Keep responses concise.",
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    user = ConversableAgent(
        name="User",
        llm_config=False,
        human_input_mode="NEVER",
    )

    print(f"[i] Model: {model}")
    print(f"[i] Max context: {max_context:,} tokens\n")

    total_tokens = 0

    while True:
        # Get user input
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[OK] Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == 'quit':
            print("[OK] Goodbye!")
            break

        if user_input.lower() == 'clear':
            # Clear conversation history
            assistant.clear_history()
            total_tokens = 0
            print("[OK] Context cleared!\n")
            continue

        # Count input tokens
        input_tokens = count_tokens(user_input, model)

        # Send message
        try:
            user.send(message=user_input, recipient=assistant, request_reply=True)

            # Get response
            response = assistant.chat_messages[user][-1]['content']
            response_tokens = count_tokens(response, model)

            # Update total
            total_tokens = sum(
                count_tokens(msg['content'], model)
                for msg in assistant.chat_messages[user]
            )

            # Display response
            print(f"\nAssistant: {response}\n")

            # Show token usage
            usage_percent = (total_tokens / max_context) * 100
            bar_len = 20
            filled = int(bar_len * total_tokens // max_context)
            bar = '#' * filled + '-' * (bar_len - filled)

            print(f"[{bar}] {usage_percent:.1f}% ({total_tokens:,}/{max_context:,} tokens)")

            # Warning if approaching limit
            if usage_percent > 70:
                print("[!] WARNING: Context getting full. Type 'clear' to reset.")
            print()

        except Exception as e:
            print(f"[X] Error: {e}\n")

if __name__ == "__main__":
    main()
