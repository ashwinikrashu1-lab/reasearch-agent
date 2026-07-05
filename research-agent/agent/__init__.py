"""
agent package — exposes research tools and watsonx client.
Import submodules lazily to avoid circular imports at package load time.
"""
from agent.instructions import (
    AGENT_INSTRUCTIONS,
    get_system_prompt,
    get_citation_style,
    get_depth_config,
    is_arxiv_enabled,
)

__all__ = [
    "AGENT_INSTRUCTIONS",
    "get_system_prompt",
    "get_citation_style",
    "get_depth_config",
    "is_arxiv_enabled",
]
