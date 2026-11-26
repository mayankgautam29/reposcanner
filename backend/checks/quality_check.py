import ast

from config import LONG_FILE_LINES, LONG_FUNCTION_LINES

COMMENT_STARTS = ("#", "//", "/*", "*", "<!--")
MAX_ITEMS = 10


def find_long_files(code_files):
    long_files = [
        {"file": file["path"], "lines": file["lines"]}
        for file in code_files
        if file["lines"] > LONG_FILE_LINES
    ]
    long_files.sort(key=lambda item: item["lines"], reverse=True)
    return long_files[:MAX_ITEMS]


def find_long_functions(code_files):
    long_functions = []

    for file in code_files:
        if file["extension"] != ".py":
            continue

        try:
            tree = ast.parse(file["text"])
        except (SyntaxError, ValueError, RecursionError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = node.end_lineno - node.lineno + 1
                if length > LONG_FUNCTION_LINES:
                    long_functions.append({"file": file["path"], "name": node.name, "lines": length})

    long_functions.sort(key=lambda item: item["lines"], reverse=True)
    return long_functions[:MAX_ITEMS]


def count_comments(code_files):
    code_lines = 0
    comment_lines = 0

    for file in code_files:
        for line in file["text"].splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            code_lines += 1
            if stripped.startswith(COMMENT_STARTS):
                comment_lines += 1

    if code_lines == 0:
        return 0, 0
    return code_lines, round(comment_lines * 100 / code_lines, 1)


def check_quality(files):
    code_files = [file for file in files if file["is_code"]]
    code_lines, comment_percent = count_comments(code_files)

    return {
        "long_files": find_long_files(code_files),
        "long_functions": find_long_functions(code_files),
        "code_lines": code_lines,
        "comment_percent": comment_percent,
    }
