"""
Multi-Agent DevOps System
Specialized agents for comprehensive DevOps operations
"""

from .devops_agents import (
    DEVOPS_AGENT_CONFIGS,
    get_agent_for_query,
    get_agent_config,
    get_all_agent_names,
    get_agents_by_category
)

# Legacy support for existing code
from .agent_prompts import AGENT_CONFIGS

__all__ = [
    'DEVOPS_AGENT_CONFIGS',
    'AGENT_CONFIGS',
    'get_agent_for_query',
    'get_agent_config',
    'get_all_agent_names',
    'get_agents_by_category'
]
