import json
import time
from concurrent.futures import ThreadPoolExecutor

from google import genai
from google.genai import errors, types

from config import GEMINI_API_KEY, check_free_models

RETRY_CODES = [429, 500, 503, 504]
MAX_TRIES = 3
WAIT_SECONDS = 2
TIMEOUT_MS = 45_000
DEADLINE_SECONDS = 50

client = None


class ModelBusyError(RuntimeError):
    pass


def get_client():
    global client
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it in backend/.env")
    if client is None:
        client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=TIMEOUT_MS))
    return client


def explain_error(error):
    if error.code in (400, 401, 403):
        return f"Gemini refused the request (error {error.code}). Check GEMINI_API_KEY."
    return f"Gemini returned an error ({error.code})."


def send_with_deadline(model, contents, config):
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(lambda: get_client().models.generate_content(model=model, contents=contents, config=config))
    try:
        return future.result(timeout=DEADLINE_SECONDS)
    finally:
        pool.shutdown(wait=False)


def generate(model, contents, config):
    too_slow = ModelBusyError(f"no answer within {DEADLINE_SECONDS} seconds")

    for attempt in range(1, MAX_TRIES + 1):
        try:
            return send_with_deadline(model, contents, config)
        except TimeoutError as error:
            raise too_slow from error
        except errors.APIError as error:
            if error.code not in RETRY_CODES:
                raise RuntimeError(explain_error(error)) from error
            if attempt == MAX_TRIES or error.code == 429:
                raise ModelBusyError(f"error {error.code}") from error
            time.sleep(WAIT_SECONDS * attempt)
        except Exception as error:
            if "Timeout" in type(error).__name__:
                raise too_slow from error
            raise


def ask_text(model, system_prompt, user_prompt):
    check_free_models(model)
    response = generate(model, user_prompt, types.GenerateContentConfig(system_instruction=system_prompt))
    return response.text


def ask_json(model, system_prompt, user_prompt):
    check_free_models(model)
    config = types.GenerateContentConfig(system_instruction=system_prompt, response_mime_type="application/json")
    response = generate(model, user_prompt, config)
    return json.loads(response.text)
