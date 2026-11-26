from config import README_CHARS
from utils.llm_client import ask_json, ask_text
from utils.numbers import to_percent

README_SYSTEM_PROMPT = "You explain GitHub README files in simple words."
REVIEW_SYSTEM_PROMPT = "You are a senior code reviewer. You always answer in JSON."

JSON_FORMAT = (
    'Reply in JSON with these keys: "score" (number from 0 to 100), "summary" (2 sentences), '
    '"problems" (list of short strings), "tips" (list of short strings).'
)

STRICT_RULES = (
    "Only talk about things you can really see in the code above. "
    "Mention file names. Give 3 to 5 problems and 3 to 5 tips. "
    "The score must match the problems you list."
)


def find_readme(files):
    for file in files:
        if file["path"].lower().startswith("readme"):
            return file["text"]
    return ""


def build_code_sample(files, limit_chars):
    code_files = [file for file in files if file["is_code"]]
    code_files.sort(key=lambda file: file["lines"], reverse=True)

    per_file_limit = limit_chars // 3
    parts = []
    used = 0

    for file in code_files:
        if used >= limit_chars:
            break
        part = f"### {file['path']}\n{file['text'][:per_file_limit]}"
        parts.append(part)
        used += len(part)

    return "\n\n".join(parts)


def summarise_readme(repo, model):
    readme = find_readme(repo["files"])
    if not readme:
        return "No README file found."

    prompt = f"Summarise this README in 3 short sentences:\n\n{readme[:README_CHARS]}"
    return ask_text(model, README_SYSTEM_PROMPT, prompt)


def review_code(repo, model, code_sample, strict):
    readme = find_readme(repo["files"])
    languages = ", ".join(repo["languages"]) or "unknown"

    prompt = (
        f"Repository: {repo['name']}\n"
        f"Languages: {languages}\n\n"
        f"README:\n{readme[:README_CHARS]}\n\n"
        f"Main code:\n{code_sample}\n\n"
        f"{JSON_FORMAT}"
    )
    if strict:
        prompt += "\n" + STRICT_RULES

    answer = ask_json(model, REVIEW_SYSTEM_PROMPT, prompt)

    return {
        "score": to_percent(answer.get("score")),
        "summary": str(answer.get("summary", "")),
        "problems": [str(item) for item in answer.get("problems", [])],
        "tips": [str(item) for item in answer.get("tips", [])],
    }
