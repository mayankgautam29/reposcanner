import os

from dotenv import load_dotenv

load_dotenv()

FREE_MODELS = ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.8-flash"]


def check_free_models(*models):
    for model in models:
        if model not in FREE_MODELS:
            raise ValueError(f"{model} is not on the free model list. Use one of: {', '.join(FREE_MODELS)}")


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SMALL_MODEL = os.getenv("SMALL_MODEL", "gemini-3.5-flash-lite")
STRONG_MODEL = os.getenv("STRONG_MODEL", "gemini-3.8-flash")
VALIDATOR_MODEL = os.getenv("VALIDATOR_MODEL", "gemini-3.6-flash")

check_free_models(SMALL_MODEL, STRONG_MODEL, VALIDATOR_MODEL)
FRONTEND_URLS = [url.strip().rstrip("/") for url in os.getenv("FRONTEND_URL", "http://localhost:3000").split(",")]

CONFIDENCE_LIMIT = 70

MAX_FILE_SIZE = 200_000
LONG_FILE_LINES = 300
LONG_FUNCTION_LINES = 50
MIN_COMMENT_PERCENT = 5

BIG_CODE_LINES = 500

NORMAL_CHUNK_CHARS = 12000
SMALL_CHUNK_CHARS = 4000
README_CHARS = 3000
