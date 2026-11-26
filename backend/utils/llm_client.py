import json

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, check_free_models


def get_client():
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it in backend/.env")
    return genai.Client(api_key=GEMINI_API_KEY)


def ask_text(model, system_prompt, user_prompt):
    check_free_models(model)
    response = get_client().models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text


def ask_json(model, system_prompt, user_prompt):
    check_free_models(model)
    response = get_client().models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
        ),
    )
    return json.loads(response.text)
