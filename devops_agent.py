"""
DevOps AI Agent Chatbot
Helps with Docker, Kubernetes, Prometheus, Cloud, and more!

Run: python devops_agent.py
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

# DevOps System Prompt
DEVOPS_SYSTEM_PROMPT = """You are an expert DevOps Engineer AI Assistant. You help with:

1. **Docker**: Dockerfile creation, docker-compose, container troubleshooting, image optimization
2. **Kubernetes (K8s)**: Deployments, Services, ConfigMaps, Secrets, Helm charts, kubectl commands
3. **Prometheus & Grafana**: PromQL queries, alerting rules, metrics, dashboards
4. **CI/CD**: GitHub Actions, Jenkins, GitLab CI, ArgoCD, pipeline optimization
5. **Cloud**: AWS, Azure, GCP - infrastructure, IAM, networking, cost optimization
6. **Infrastructure as Code**: Terraform, Ansible, Pulumi
7. **Monitoring & Logging**: ELK stack, Loki, Jaeger, OpenTelemetry
8. **Security**: Container security, secrets management, RBAC, network policies

Guidelines:
- Provide practical, copy-paste ready commands and configs
- Explain what each command does
- Suggest best practices and optimizations
- Warn about common pitfalls
- Keep responses focused and actionable
"""

def print_banner():
    print("""
================================================================================
     ____  _____ __     __  ___   ____  ____       _    ___    _    ____ _____
    |  _ \\| ____|  \\ / / / _ \\ |  _ \\/ ___|     / \\  |_ _|  / \\  / ___| ____|
    | | | |  _| \\ \\  / / | | | || |_) \\___ \\    / _ \\  | |  / _ \\| |  _|  _|
    | |_| | |___ \\ V /  | |_| ||  __/ ___) |  / ___ \\ | | / ___ \\ |_| | |___
    |____/|_____|  \\_/    \\___/ |_|   |____/  /_/   \\_\\___/_/   \\_\\____|_____|

================================================================================
    Docker | Kubernetes | Prometheus | Cloud | CI/CD | Terraform
================================================================================
    """)

def show_help():
    print("""
QUICK COMMANDS:
---------------
  help     - Show this help
  clear    - Reset conversation context
  quit     - Exit the chatbot

EXAMPLE QUESTIONS:
------------------
  "Create a Dockerfile for a Python Flask app"
  "Write a K8s deployment for nginx with 3 replicas"
  "PromQL query for high CPU usage alerts"
  "Terraform code for AWS EC2 instance"
  "Docker compose for Redis + PostgreSQL"
  "GitHub Actions workflow for Docker build"
  "How to debug CrashLoopBackOff in K8s?"
  "Optimize my Docker image size"
    """)

def main():
    print_banner()
    print("Type 'help' for commands, 'quit' to exit\n")

    # Load configuration
    config = load_config()
    model = config.get('model', 'gpt-3.5-turbo')
    max_context = 4096

    # Configure LLM
    llm_config = {
        "config_list": [{
            "model": model,
            "api_key": config['api_key'],
        }],
        "temperature": 0.7,
    }

    # Create DevOps Agent
    devops_agent = ConversableAgent(
        name="DevOpsAgent",
        system_message=DEVOPS_SYSTEM_PROMPT,
        llm_config=llm_config,
        human_input_mode="NEVER",
    )

    user = ConversableAgent(
        name="User",
        llm_config=False,
        human_input_mode="NEVER",
    )

    print(f"[i] Model: {model} | Context: {max_context:,} tokens\n")

    total_tokens = 0

    while True:
        try:
            user_input = input("DevOps> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[OK] Goodbye!")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.lower() == 'quit':
            print("[OK] Goodbye!")
            break

        if user_input.lower() == 'help':
            show_help()
            continue

        if user_input.lower() == 'clear':
            devops_agent.clear_history()
            total_tokens = 0
            print("[OK] Context cleared!\n")
            continue

        # Send to AI
        try:
            user.send(message=user_input, recipient=devops_agent, request_reply=True)

            # Get response
            response = devops_agent.chat_messages[user][-1]['content']

            # Calculate tokens
            total_tokens = sum(
                count_tokens(msg['content'], model)
                for msg in devops_agent.chat_messages[user]
            )

            # Display response
            print(f"\n{response}\n")

            # Token usage bar
            usage_percent = (total_tokens / max_context) * 100
            bar_len = 30
            filled = int(bar_len * total_tokens // max_context)
            bar = '#' * filled + '-' * (bar_len - filled)

            print(f"[{bar}] {usage_percent:.1f}% tokens used")

            if usage_percent > 70:
                print("[!] Context filling up. Type 'clear' to reset.")
            print()

        except Exception as e:
            print(f"[X] Error: {e}\n")
            print("[i] Check your API key in config.json\n")

if __name__ == "__main__":
    main()
