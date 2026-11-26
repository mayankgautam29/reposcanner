from config import MIN_COMMENT_PERCENT

MISSING_FILE_RULES = {
    "README": (10, "Add a README file that explains what the project does"),
    "LICENSE": (5, "Add a LICENSE file"),
    ".gitignore": (5, "Add a .gitignore file"),
    "Requirements file": (5, "Add a requirements file (requirements.txt or package.json)"),
}

SECRET_PENALTY = 10
MAX_SECRET_PENALTY = 40
LONG_FILE_PENALTY = 2
MAX_LONG_FILE_PENALTY = 10
LONG_FUNCTION_PENALTY = 1
MAX_LONG_FUNCTION_PENALTY = 10
LOW_COMMENTS_PENALTY = 5
MIN_LINES_FOR_COMMENT_CHECK = 50


def calculate_rule_score(secrets, health, quality):
    penalties = []
    suggestions = []

    for item in health:
        if not item["found"]:
            points, suggestion = MISSING_FILE_RULES[item["name"]]
            penalties.append({"reason": f"{item['name']} is missing", "points": points})
            suggestions.append(suggestion)

    if secrets:
        points = min(len(secrets) * SECRET_PENALTY, MAX_SECRET_PENALTY)
        penalties.append({"reason": f"{len(secrets)} secret(s) found in code", "points": points})
        suggestions.append("Remove passwords and API keys from the code and keep them in a .env file")

    if quality["long_files"]:
        points = min(len(quality["long_files"]) * LONG_FILE_PENALTY, MAX_LONG_FILE_PENALTY)
        penalties.append({"reason": f"{len(quality['long_files'])} very long file(s)", "points": points})
        suggestions.append("Split very long files into smaller files")

    if quality["long_functions"]:
        points = min(len(quality["long_functions"]) * LONG_FUNCTION_PENALTY, MAX_LONG_FUNCTION_PENALTY)
        penalties.append({"reason": f"{len(quality['long_functions'])} very long function(s)", "points": points})
        suggestions.append("Break long functions into smaller functions")

    has_enough_code = quality["code_lines"] >= MIN_LINES_FOR_COMMENT_CHECK
    if has_enough_code and quality["comment_percent"] < MIN_COMMENT_PERCENT:
        penalties.append({"reason": f"Only {quality['comment_percent']}% of lines are comments", "points": LOW_COMMENTS_PENALTY})
        suggestions.append("Add comments to explain the important parts of the code")

    score = max(0, 100 - sum(item["points"] for item in penalties))
    return score, penalties, suggestions
