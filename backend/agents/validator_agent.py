import json

from utils.llm_client import ask_json
from utils.numbers import to_percent

SYSTEM_PROMPT = "You are a strict checker of code reviews. You always answer in JSON."


def run(review, code_sample, model):
    prompt = (
        "Another AI reviewed the code below. Check if its review is correct, fair and based on the code.\n\n"
        f"Review:\n{json.dumps(review)}\n\n"
        f"Code that was reviewed:\n{code_sample}\n\n"
        'Reply in JSON with two keys: "confidence" (number from 0 to 100) and "reason" (one sentence).'
    )

    answer = ask_json(model, SYSTEM_PROMPT, prompt)

    return {
        "confidence": to_percent(answer.get("confidence")),
        "reason": str(answer.get("reason", "")),
    }
