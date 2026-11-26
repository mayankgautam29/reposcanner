from checks.secret_patterns import PLACEHOLDER_WORDS, SECRET_PATTERNS

MAX_LINE_LENGTH = 500


def is_placeholder(line):
    lower_line = line.lower()
    return any(word in lower_line for word in PLACEHOLDER_WORDS)


def hide_secret(text):
    return text[:4] + "****"


def find_secrets(files):
    found = []

    for file in files:
        for line_number, line in enumerate(file["text"].splitlines(), start=1):
            line = line[:MAX_LINE_LENGTH]
            if is_placeholder(line):
                continue

            for secret_type, pattern in SECRET_PATTERNS.items():
                match = pattern.search(line)
                if match:
                    found.append(
                        {
                            "file": file["path"],
                            "line": line_number,
                            "type": secret_type,
                            "preview": hide_secret(match.group(0)),
                        }
                    )
                    break

    return found
