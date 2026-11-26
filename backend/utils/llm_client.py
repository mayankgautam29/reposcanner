import json
import time

from google import genai
from google.genai import errors, types

from config import GEMINI_API_KEY, check_free_models

RETRY_CODES = [429, 500, 503, 504]
MAX_TRIES = 4
WAIT_SECONDS = 3

client = None


def get_client():
    global client
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it in backend/.env")
    if client is None:
        client = genai.Client(api_key=GEMINI_API_KEY)
    return client


def explain_error(error):
    if error.code == 429:
        return "The free Gemini limit is used up for now (error 429). Wait a few minutes and scan again."
    if error.code in RETRY_CODES:
        return f"Gemini is busy right now (error {error.code}). Wait a minute and scan again."
    if error.code in (400, 401, 403):
        return f"Gemini refused the request (error {error.code}). Check GEMINI_API_KEY."
    return f"Gemini returned an error ({error.code})."


def generate(model, contents, config):
    for attempt in range(1, MAX_TRIES + 1):
        try:
            return get_client().models.generate_content(model=model, contents=contents, config=config)
        except errors.APIError as error:
            if error.code not in RETRY_CODES or attempt == MAX_TRIES:
                raise RuntimeError(explain_error(error)) from error
            time.sleep(WAIT_SECONDS * attempt)


def ask_text(model, system_prompt, user_prompt):
    check_free_models(model)
    response = generate(model, user_prompt, types.GenerateContentConfig(system_instruction=system_prompt))
    return response.text


def ask_json(model, system_prompt, user_prompt):
    check_free_models(model)
    config = types.GenerateContentConfig(system_instruction=system_prompt, response_mime_type="application/json")
    response = generate(model, user_prompt, config)
    return json.loads(response.text)
