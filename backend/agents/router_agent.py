from config import BIG_CODE_LINES, SMALL_MODEL, STRONG_MODEL


def choose_model(task, repo, rules):
    if task in ("summarise_readme", "detect_ai_code"):
        return SMALL_MODEL, "simple task"

    if repo["code_lines"] > BIG_CODE_LINES:
        return STRONG_MODEL, f"big code ({repo['code_lines']} lines)"

    if rules["secrets"]:
        return STRONG_MODEL, "secrets found, needs a careful security check"

    return SMALL_MODEL, f"small code ({repo['code_lines']} lines)"
