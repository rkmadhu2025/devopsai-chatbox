"""
================================================================================
MULTI-AGENT DEVOPS PLATFORM
================================================================================
A comprehensive AI-powered DevOps assistant with specialized agents for:
- Git/GitHub          - CI/CD (Jenkins, ArgoCD)
- Docker/Kubernetes   - Monitoring (Prometheus, Grafana, Loki)
- Databases           - Cloud (AWS, Azure, GCP)
- Infrastructure      - Network (Nginx, Firewall, Routers)
- SRE/Incidents       - Communication (Email, Chatbots)
- Python Development

Run: python multi_agent_devops.py
================================================================================
"""

import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tiktoken
from colorama import init, Fore, Style

# Try to import autogen, fall back to anthropic client if needed
try:
    from autogen import ConversableAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False

# Import anthropic for direct API calls
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Initialize colorama
init(autoreset=True)

# Import agent configurations
from agents.agent_prompts import AGENT_CONFIGS, get_agent_for_query, get_all_agent_names


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


def print_banner():
    """Print the application banner"""
    banner = f"""
{Fore.CYAN}================================================================================
{Fore.GREEN}    __  __       _ _   _          _                    _
{Fore.GREEN}   |  \\/  |_   _| | |_(_)        / \\   __ _  ___ _ __ | |_
{Fore.GREEN}   | |\\/| | | | | | __| |_____  / _ \\ / _` |/ _ \\ '_ \\| __|
{Fore.GREEN}   | |  | | |_| | | |_| |_____/ ___ \\ (_| |  __/ | | | |_
{Fore.GREEN}   |_|  |_|\\__,_|_|\\__|_|    /_/   \\_\\__, |\\___|_| |_|\\__|
{Fore.GREEN}                                     |___/
{Fore.YELLOW}                    DEVOPS PLATFORM
{Fore.CYAN}================================================================================
{Style.RESET_ALL}"""
    print(banner)


def print_agents_table():
    """Print available agents in a table format"""
    agents_info = [
        ("git", "Git, GitHub, GitLab, Branching, PRs"),
        ("cicd", "Jenkins, ArgoCD, Maven, Gradle, GitHub Actions"),
        ("container", "Docker, Kubernetes, Helm, kubectl"),
        ("monitoring", "Prometheus, Grafana, Loki, OpenTelemetry"),
        ("database", "MySQL, Neo4j, Redis, RabbitMQ, Kafka"),
        ("cloud", "AWS, Azure, GCP, Terraform, Ansible"),
        ("infrastructure", "VMware, Windows Server, Linux, VMs"),
        ("network", "Nginx, Firewall, Router, Switch, API Gateway"),
        ("sre", "Incidents, Problems, SLO/SLI, Runbooks"),
        ("communication", "Email, Slack, Webhooks, Chatbots"),
        ("python", "Python scripting, Flask, FastAPI"),
    ]

    print(f"\n{Fore.YELLOW}AVAILABLE AGENTS:{Style.RESET_ALL}")
    print("-" * 70)
    print(f"{'Agent':<15} {'Specialization':<55}")
    print("-" * 70)
    for agent_id, desc in agents_info:
        print(f"{Fore.CYAN}{agent_id:<15}{Style.RESET_ALL} {desc:<55}")
    print("-" * 70)


def print_help():
    """Print help information"""
    print(f"""
{Fore.YELLOW}COMMANDS:{Style.RESET_ALL}
---------
  help          Show this help message
  agents        List all available agents
  @<agent>      Force use specific agent (e.g., @docker, @k8s, @aws)
  clear         Clear all agent contexts
  clear <agent> Clear specific agent context
  tokens        Show token usage for all agents
  quit/exit     Exit the application

{Fore.YELLOW}EXAMPLE QUERIES:{Style.RESET_ALL}
----------------
  "Create a Dockerfile for Python Flask"
  "K8s deployment with 3 replicas"
  "PromQL for high CPU pods"
  "Jenkins pipeline for Docker build"
  "@aws Create an S3 bucket with Terraform"
  "GitHub Actions workflow for CI"
  "Nginx reverse proxy config"
  "MySQL backup script"
  "Incident response for database outage"
  "vmware clone vm script"

{Fore.YELLOW}AUTO-ROUTING:{Style.RESET_ALL}
-------------
  Questions are automatically routed to the best agent based on keywords.
  Use @<agent> prefix to force a specific agent.
""")


class MultiAgentDevOps:
    """Multi-Agent DevOps Platform"""

    def __init__(self, config):
        self.config = config
        self.use_anthropic = 'anthropic' in config and ANTHROPIC_AVAILABLE
        self.use_autogen = not self.use_anthropic and AUTOGEN_AVAILABLE

        # Support both flat config (OpenAI) and nested config (Anthropic)
        if self.use_anthropic:
            anthropic_config = config['anthropic']
            self.model = anthropic_config.get('model', 'claude-3-haiku-20240307')
            # Check env var first, then config file
            self.api_key = os.environ.get('ANTHROPIC_API_KEY') or anthropic_config.get('api_key', '')
            self.anthropic_client = anthropic.Anthropic(api_key=self.api_key)
            self.llm_config = None  # Not used for direct Anthropic calls
        elif self.use_autogen:
            # OpenAI config (original behavior)
            self.model = config.get('model', 'gpt-3.5-turbo')
            self.llm_config = {
                "config_list": [{
                    "model": self.model,
                    "api_key": config.get('api_key', ''),
                }],
                "temperature": config.get('temperature', 0.7),
            }
        else:
            raise RuntimeError("No LLM backend available. Install 'anthropic' or 'pyautogen'.")

        self.max_context = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.7)
        self.agents = {}
        self.users = {}
        self.agent_histories = {}  # Store conversation history for Anthropic
        self._create_agents()

    def _create_agents(self):
        """Create all specialized agents"""
        for agent_id, agent_config in AGENT_CONFIGS.items():
            if self.use_autogen:
                # Create the AI agent using autogen
                self.agents[agent_id] = ConversableAgent(
                    name=agent_config["name"],
                    system_message=agent_config["prompt"],
                    llm_config=self.llm_config,
                    human_input_mode="NEVER",
                )
                # Create corresponding user agent
                self.users[agent_id] = ConversableAgent(
                    name=f"User_{agent_id}",
                    llm_config=False,
                    human_input_mode="NEVER",
                )
            else:
                # For Anthropic, store agent configs and create history
                self.agents[agent_id] = {
                    "name": agent_config["name"],
                    "system_message": agent_config["prompt"],
                }
                self.agent_histories[agent_id] = []

    def get_token_usage(self, agent_id):
        """Get token usage for a specific agent"""
        if self.use_autogen:
            agent = self.agents.get(agent_id)
            user = self.users.get(agent_id)
            if not agent or not user:
                return 0
            messages = agent.chat_messages.get(user, [])
            return sum(count_tokens(msg.get('content', ''), self.model) for msg in messages)
        else:
            # For Anthropic, calculate from history
            history = self.agent_histories.get(agent_id, [])
            return sum(count_tokens(msg.get('content', ''), self.model) for msg in history)

    def get_all_token_usage(self):
        """Get token usage for all agents"""
        usage = {}
        for agent_id in self.agents:
            usage[agent_id] = self.get_token_usage(agent_id)
        return usage

    def clear_agent(self, agent_id):
        """Clear context for a specific agent"""
        if agent_id in self.agents:
            if self.use_autogen:
                self.agents[agent_id].clear_history()
            else:
                self.agent_histories[agent_id] = []
            return True
        return False

    def clear_all_agents(self):
        """Clear context for all agents"""
        for agent_id in self.agents:
            if self.use_autogen:
                self.agents[agent_id].clear_history()
            else:
                self.agent_histories[agent_id] = []

    def query(self, user_input, force_agent=None):
        """Send query to appropriate agent"""
        # Determine which agent to use
        if force_agent and force_agent in self.agents:
            agent_id = force_agent
        else:
            agent_id = get_agent_for_query(user_input)

        agent_name = AGENT_CONFIGS[agent_id]["name"]

        if self.use_autogen:
            agent = self.agents[agent_id]
            user = self.users[agent_id]

            # Send message
            user.send(message=user_input, recipient=agent, request_reply=True)

            # Get response
            response = agent.chat_messages[user][-1]['content']
        else:
            # Use Anthropic API directly
            agent = self.agents[agent_id]
            history = self.agent_histories[agent_id]

            # Add user message to history
            history.append({"role": "user", "content": user_input})

            try:
                # Call Anthropic API
                message = self.anthropic_client.messages.create(
                    model=self.model,
                    max_tokens=self.max_context,
                    system=agent["system_message"],
                    messages=history
                )
                response = message.content[0].text

                # Add assistant response to history
                history.append({"role": "assistant", "content": response})
            except anthropic.AuthenticationError as e:
                raise Exception(f"Authentication failed: {e}. Check your Anthropic API key.")
            except Exception as e:
                raise Exception(f"API call failed: {e}")

        tokens_used = self.get_token_usage(agent_id)

        return {
            "agent_id": agent_id,
            "agent_name": agent_name,
            "response": response,
            "tokens_used": tokens_used,
        }


def main():
    """Main function"""
    print_banner()
    print_agents_table()
    print(f"\n{Fore.GREEN}Type 'help' for commands, 'quit' to exit{Style.RESET_ALL}\n")

    # Load configuration
    try:
        config = load_config()
    except FileNotFoundError:
        print(f"{Fore.RED}[X] config.json not found. Please create it from config.example.json{Style.RESET_ALL}")
        return

    # Initialize multi-agent system
    print(f"{Fore.CYAN}[i] Initializing agents...{Style.RESET_ALL}")
    try:
        platform = MultiAgentDevOps(config)
    except Exception as e:
        print(f"{Fore.RED}[X] Failed to initialize: {e}{Style.RESET_ALL}")
        return

    backend = "Anthropic" if platform.use_anthropic else "OpenAI (AutoGen)"
    print(f"{Fore.GREEN}[OK] {len(platform.agents)} agents ready!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[i] Backend: {backend}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[i] Model: {platform.model}{Style.RESET_ALL}\n")

    while True:
        try:
            user_input = input(f"{Fore.GREEN}DevOps>{Style.RESET_ALL} ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{Fore.YELLOW}[OK] Goodbye!{Style.RESET_ALL}")
            break

        if not user_input:
            continue

        # Handle commands
        cmd = user_input.lower()

        if cmd in ['quit', 'exit']:
            print(f"{Fore.YELLOW}[OK] Goodbye!{Style.RESET_ALL}")
            break

        if cmd == 'help':
            print_help()
            continue

        if cmd == 'agents':
            print_agents_table()
            continue

        if cmd == 'tokens':
            usage = platform.get_all_token_usage()
            print(f"\n{Fore.YELLOW}TOKEN USAGE:{Style.RESET_ALL}")
            print("-" * 40)
            total = 0
            for agent_id, tokens in usage.items():
                if tokens > 0:
                    pct = (tokens / platform.max_context) * 100
                    bar_len = 15
                    filled = int(bar_len * tokens // platform.max_context)
                    bar = '#' * filled + '-' * (bar_len - filled)
                    print(f"{agent_id:<15} [{bar}] {tokens:>5} ({pct:.1f}%)")
                    total += tokens
            print("-" * 40)
            print(f"{'TOTAL':<15} {' ' * 17} {total:>5}")
            print()
            continue

        if cmd == 'clear':
            platform.clear_all_agents()
            print(f"{Fore.GREEN}[OK] All agent contexts cleared!{Style.RESET_ALL}\n")
            continue

        if cmd.startswith('clear '):
            agent_id = cmd.split(' ')[1]
            if platform.clear_agent(agent_id):
                print(f"{Fore.GREEN}[OK] {agent_id} context cleared!{Style.RESET_ALL}\n")
            else:
                print(f"{Fore.RED}[X] Unknown agent: {agent_id}{Style.RESET_ALL}\n")
            continue

        # Check for forced agent (@agent prefix)
        force_agent = None
        if user_input.startswith('@'):
            parts = user_input.split(' ', 1)
            force_agent = parts[0][1:].lower()
            if len(parts) > 1:
                user_input = parts[1]
            else:
                print(f"{Fore.RED}[X] Please provide a query after @{force_agent}{Style.RESET_ALL}\n")
                continue

            if force_agent not in platform.agents:
                print(f"{Fore.RED}[X] Unknown agent: {force_agent}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}[i] Available: {', '.join(platform.agents.keys())}{Style.RESET_ALL}\n")
                continue

        # Query the agent
        try:
            result = platform.query(user_input, force_agent)

            # Display which agent responded
            print(f"\n{Fore.MAGENTA}[{result['agent_name']}]{Style.RESET_ALL}")
            print("-" * 70)

            # Display response
            print(f"{result['response']}")

            # Token usage bar
            print("-" * 70)
            tokens = result['tokens_used']
            pct = (tokens / platform.max_context) * 100
            bar_len = 30
            filled = int(bar_len * tokens // platform.max_context)
            bar = '#' * filled + '-' * (bar_len - filled)

            color = Fore.GREEN if pct < 50 else (Fore.YELLOW if pct < 80 else Fore.RED)
            print(f"{color}[{bar}] {pct:.1f}% ({tokens:,} tokens){Style.RESET_ALL}")

            if pct > 70:
                print(f"{Fore.YELLOW}[!] Context filling up. Use 'clear {result['agent_id']}' to reset.{Style.RESET_ALL}")
            print()

        except Exception as e:
            print(f"{Fore.RED}[X] Error: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[i] Check your API key in config.json{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
