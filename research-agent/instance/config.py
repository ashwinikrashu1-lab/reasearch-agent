"""
instance/config.py — Instance-level Flask configuration.
Place secrets and environment-specific overrides here.
This file is NOT committed to version control (.gitignore).
"""
import os

# ── Core Flask ────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")
DEBUG      = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# ── Database ──────────────────────────────────────────────────────────────────
# SQLite stored inside this instance/ folder by default
SQLALCHEMY_DATABASE_URI    = os.getenv("DATABASE_URL", "sqlite:///research_agent.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ── Uploads ───────────────────────────────────────────────────────────────────
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB

# ── IBM watsonx.ai ────────────────────────────────────────────────────────────
IBM_API_KEY        = os.getenv("IBM_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
GRANITE_MODEL_ID   = os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-8b-instruct")

# ── Research Agent Settings ────────────────────────────────────────────────────
DEFAULT_CITATION_STYLE = os.getenv("DEFAULT_CITATION_STYLE", "APA")
RESEARCH_DEPTH         = os.getenv("RESEARCH_DEPTH", "standard")
RESEARCH_DOMAIN        = os.getenv("RESEARCH_DOMAIN", "general")
ENABLE_ARXIV_SEARCH    = os.getenv("ENABLE_ARXIV_SEARCH", "true").lower() == "true"
