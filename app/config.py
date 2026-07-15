"""Application configuration.

This module contains shared settings only. Other modules should import these
constants instead of defining their own paths, model names, limits, or tuning
values.
"""

from pathlib import Path


# Paths
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
DATABASE_PATH: Path = DATA_DIR / "products.db"


# AI
DEFAULT_PROVIDER: str = "ollama"
OLLAMA_MODEL: str = "qwen3-coder:30b"
GEMINI_MODEL: str = "gemini-2.5-flash"
GEMINI_MODELS: list[str] = [
    "gemini-3.5-flash",
    GEMINI_MODEL,
    "gemini-2.0-flash",
]


# Search
MAX_SEARCH_RESULTS: int = 8


# Conversation
MAX_HISTORY_EXCHANGES: int = 10
MAX_HISTORY_MESSAGES: int = MAX_HISTORY_EXCHANGES * 2


# Prompt
TARGET_PROMPT_MIN: int = 1500
TARGET_PROMPT_MAX: int = 2500
PROMPT_HARD_LIMIT: int = 3000


# Generation
TEMPERATURE: float = 0.2


# Backward-compatible aliases for earlier config names.
BASE_DIR: Path = PROJECT_ROOT
DEFAULT_AI_PROVIDER: str = DEFAULT_PROVIDER
AI_TEMPERATURE: float = TEMPERATURE
MIN_PROMPT_CHARACTERS: int = TARGET_PROMPT_MIN
MAX_PROMPT_CHARACTERS: int = TARGET_PROMPT_MAX
