#!/usr/bin/env python3
"""
================================================================================
DEVOPS GENAI MULTI-AGENT CHATBOT
================================================================================

A comprehensive AI-powered DevOps assistant with 30+ specialized agents for:

MONITORING & OBSERVABILITY:
  - Prometheus, Grafana, AlertManager, Loki, Jaeger, Tempo, Thanos

LOGGING & SEARCH:
  - Elasticsearch, Kibana

CI/CD & GITOPS:
  - Jenkins, ArgoCD, SonarQube

CONTAINER & REGISTRY:
  - Docker, Kubernetes, Harbor

SECURITY & AUTH:
  - Keycloak, Vault, Trivy, Falco, Kyverno, Cert-Manager

AUTOMATION:
  - StackStorm, n8n

DATABASES & MESSAGING:
  - Neo4j, Redis, RabbitMQ, MySQL, PostgreSQL

PROJECT & INCIDENT:
  - Redmine, PagerDuty, Statuspage

BACKUP & KUBERNETES TOOLS:
  - Velero, External-DNS, Goldilocks/VPA, Chaos Mesh

COMMUNICATION:
  - Email, Slack, Teams, Chatbot

CODEBASE:
  - Code Analysis, Git

================================================================================
USAGE:
    # Run Web UI (recommended)
    python run_chatbot.py --web

    # Run CLI mode
    python run_chatbot.py --cli

    # Run with custom port
    python run_chatbot.py --web --port 3000

================================================================================
"""

import argparse
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_web(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the FastAPI web server"""
    print(f"""
================================================================================
       DEVOPS GENAI MULTI-AGENT CHATBOT - WEB MODE
================================================================================
       Starting web server at: http://{host}:{port}

       Open your browser and navigate to:

       Local:   http://localhost:{port}
       Network: http://{host}:{port}

       Press Ctrl+C to stop the server
================================================================================
    """)

    import uvicorn
    uvicorn.run(
        "chatbot.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


def run_cli():
    """Run the CLI chatbot"""
    from multi_agent_devops import main
    main()


def check_config():
    """Check if configuration exists"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    example_path = os.path.join(os.path.dirname(__file__), "config.example.json")

    if not os.path.exists(config_path):
        print("""
================================================================================
       CONFIGURATION REQUIRED
================================================================================

       Please create a config.json file from the example:

       1. Copy config.example.json to config.json
       2. Add your OpenAI API key
       3. Configure any tool integrations you want to use

       Example:
           cp config.example.json config.json
           # Edit config.json with your API key

================================================================================
        """)

        if os.path.exists(example_path):
            response = input("Would you like to create config.json now? (y/n): ")
            if response.lower() == 'y':
                import shutil
                shutil.copy(example_path, config_path)
                print(f"Created {config_path}")
                print("Please edit config.json and add your OpenAI API key.")
                return False
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="DevOps GenAI Multi-Agent Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_chatbot.py --web              # Start web server on port 8000
    python run_chatbot.py --web --port 3000  # Start on custom port
    python run_chatbot.py --cli              # Start CLI mode
    python run_chatbot.py --web --reload     # Start with auto-reload (dev)
        """
    )

    parser.add_argument(
        "--web", "-w",
        action="store_true",
        help="Run web UI mode (default)"
    )

    parser.add_argument(
        "--cli", "-c",
        action="store_true",
        help="Run CLI mode"
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to run on (default: 8000)"
    )

    parser.add_argument(
        "--reload", "-r",
        action="store_true",
        help="Enable auto-reload (development)"
    )

    args = parser.parse_args()

    # Check configuration
    if not check_config():
        sys.exit(1)

    # Determine mode
    if args.cli:
        run_cli()
    else:
        # Default to web mode
        run_web(args.host, args.port, args.reload)


if __name__ == "__main__":
    main()
