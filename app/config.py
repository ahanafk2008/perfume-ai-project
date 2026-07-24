"""Application configuration.

Central configuration for paths, AI providers,
limits, and runtime settings.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =========================
# Paths
# =========================

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = PROJECT_ROOT / "data"

DATABASE_PATH: Path = DATA_DIR / "products.db"


# =========================
# AI Provider
# =========================

DEFAULT_PROVIDER: str = os.getenv(
    "AI_PROVIDER",
    "ollama",
)


# Ollama
OLLAMA_MODEL: str = os.getenv(
    "OLLAMA_MODEL",
    "qwen3:14b",
)

# Gemini
GEMINI_MODEL: str = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


GEMINI_MODELS: list[str] = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


# =========================
# Search
# =========================

MAX_SEARCH_RESULTS: int = int(
    os.getenv(
        "MAX_SEARCH_RESULTS",
        "8",
    )
)


# =========================
# Conversation
# =========================

MAX_HISTORY_EXCHANGES: int = int(
    os.getenv(
        "MAX_HISTORY_EXCHANGES",
        "10",
    )
)


MAX_HISTORY_MESSAGES: int = (
    MAX_HISTORY_EXCHANGES * 2
)


# =========================
# Prompt
# =========================

TARGET_PROMPT_MIN: int = 1500

TARGET_PROMPT_MAX: int = 2500

PROMPT_HARD_LIMIT: int = 9000


# =========================
# Generation
# =========================

TEMPERATURE: float = float(
    os.getenv(
        "AI_TEMPERATURE",
        "0.2",
    )
)


# =========================
# Compatibility aliases
# =========================

BASE_DIR: Path = PROJECT_ROOT

DEFAULT_AI_PROVIDER: str = DEFAULT_PROVIDER

AI_TEMPERATURE: float = TEMPERATURE

MIN_PROMPT_CHARACTERS: int = TARGET_PROMPT_MIN

MAX_PROMPT_CHARACTERS: int = TARGET_PROMPT_MAX