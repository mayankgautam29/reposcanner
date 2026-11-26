import re

SECRET_PATTERNS = {
    "OpenAI API key": re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "Private key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "Hard-coded password": re.compile(r"""(?i)(password|passwd|pwd)\s*[:=]\s*["'][^"'\s]{4,}["']"""),
    "Hard-coded key or token": re.compile(r"""(?i)(api[_-]?key|secret|token)\s*[:=]\s*["'][A-Za-z0-9_\-]{12,}["']"""),
}

PLACEHOLDER_WORDS = ["example", "your_", "your-", "xxxx", "changeme", "placeholder", "dummy"]
