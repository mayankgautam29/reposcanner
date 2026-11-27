from config import DETECT_FILE_CHARS, DETECT_FILES, DETECT_MIN_LINES
from utils.llm_client import ask_json
from utils.numbers import to_percent

SYSTEM_PROMPT = "You estimate how much code was written by an AI assistant. You always answer in JSON."

INSTRUCTIONS = (
    "For every file below, say how much of it looks written by an AI assistant, from 0 to 100. "
    "Signs of AI code: a very even style, comments that only repeat the code, perfect docstrings on everything, "
    "textbook names, no leftover quirks. "
    "Signs of human code: odd or uneven names, TODO notes, personal shortcuts, small mistakes, a mixed style. "
    "Be careful: clean code from a careful human can look like AI. If you are not sure, stay near 50. "
    'Reply in JSON with these keys: "files" (a list of objects with "path" and "ai_percent"), '
    '"signals" (3 to 5 short strings about what you noticed) and "confidence" (number from 0 to 100, how sure you are overall).'
)


def empty_result(status):
    return {
        "status": status,
        "percent": 0,
        "label": "",
        "confidence": 0,
        "files": [],
        "signals": [],
        "files_checked": 0,
        "lines_checked": 0,
        "code_lines": 0,
        "model": "",
    }


def get_label(percent):
    if percent >= 70:
        return "Mostly AI-written"
    if percent >= 30:
        return "Mixed"
    return "Mostly human-written"


def pick_files(files):
    code_files = [file for file in files if file["is_code"] and file["lines"] >= DETECT_MIN_LINES]
    code_files.sort(key=lambda file: file["lines"], reverse=True)
    return code_files[:DETECT_FILES]


def build_prompt(picked):
    parts = [f"### {file['path']}\n{file['text'][:DETECT_FILE_CHARS]}" for file in picked]
    return INSTRUCTIONS + "\n\n" + "\n\n".join(parts)


def run(repo, model):
    picked = pick_files(repo["files"])
    if not picked:
        return empty_result("skipped")

    answer = ask_json(model, SYSTEM_PROMPT, build_prompt(picked))
    lines_by_path = {file["path"]: file["lines"] for file in picked}

    checked = []
    for item in answer.get("files", []):
        if item.get("path") in lines_by_path:
            checked.append(
                {
                    "path": item["path"],
                    "percent": to_percent(item.get("ai_percent")),
                    "lines": lines_by_path[item["path"]],
                }
            )

    if not checked:
        raise ValueError("The model did not return an estimate for any file")

    lines_checked = sum(item["lines"] for item in checked)
    percent = round(sum(item["percent"] * item["lines"] for item in checked) / lines_checked)
    checked.sort(key=lambda item: item["percent"], reverse=True)

    result = empty_result("done")
    result.update(
        {
            "percent": percent,
            "label": get_label(percent),
            "confidence": to_percent(answer.get("confidence")),
            "files": checked,
            "signals": [str(signal) for signal in answer.get("signals", [])][:5],
            "files_checked": len(checked),
            "lines_checked": lines_checked,
        }
    )
    return result
