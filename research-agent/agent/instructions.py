"""
AGENT_INSTRUCTIONS — Centralised configuration for the Research Agent.
"""
import os

AGENT_INSTRUCTIONS = {
    "name": "ResearchAI",
    "version": "1.0.0",
    "research_domain": os.getenv("RESEARCH_DOMAIN", "general"),
    "tone": "professional, concise, and academically rigorous",
    "language": "English",
    "response_style": (
        "Always structure responses with clear headings. "
        "Use bullet points for lists. "
        "Cite sources inline when referencing specific claims. "
        "Acknowledge uncertainty rather than fabricating information."
    ),
    "default_citation_style": os.getenv("DEFAULT_CITATION_STYLE", "APA"),
    "supported_citation_styles": ["APA", "IEEE", "MLA"],
    "research_depth": os.getenv("RESEARCH_DEPTH", "standard"),
    "depth_config": {
        "quick":    {"max_papers": 5,  "summary_length": "brief",    "include_gaps": False},
        "standard": {"max_papers": 10, "summary_length": "moderate", "include_gaps": True},
        "deep":     {"max_papers": 20, "summary_length": "detailed", "include_gaps": True},
    },
    "source_verification": {
        "require_doi": False,
        "preferred_sources": ["arXiv", "PubMed", "IEEE Xplore", "ACM Digital Library", "Semantic Scholar"],
        "minimum_year": 2000,
        "enable_arxiv": os.getenv("ENABLE_ARXIV_SEARCH", "true").lower() == "true",
    },
    "safety_rules": [
        "Never fabricate citations, DOIs, or author names.",
        "Clearly label AI-generated summaries as such.",
        "Do not provide medical, legal, or financial advice as definitive guidance.",
        "Flag content from non-peer-reviewed sources.",
        "Refuse requests to plagiarise or misrepresent others' work.",
        "Respect copyright — summarise, do not reproduce full text.",
    ],
    "system_prompt": (
        "You are ResearchAI, an expert academic research assistant powered by IBM Granite. "
        "You help researchers find papers, understand complex topics, generate proper citations, "
        "identify research gaps, and write structured academic content. "
        "Always be accurate, cite sources when possible, and acknowledge when information "
        "is uncertain or outside your knowledge. "
        "Format all responses in clean Markdown."
    ),
}

def get_depth_config():
    depth = AGENT_INSTRUCTIONS["research_depth"]
    return AGENT_INSTRUCTIONS["depth_config"].get(depth, AGENT_INSTRUCTIONS["depth_config"]["standard"])

def get_system_prompt():
    return AGENT_INSTRUCTIONS["system_prompt"]

def get_citation_style():
    return AGENT_INSTRUCTIONS["default_citation_style"]

def is_arxiv_enabled():
    return AGENT_INSTRUCTIONS["source_verification"]["enable_arxiv"]
