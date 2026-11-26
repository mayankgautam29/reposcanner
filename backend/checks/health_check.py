HEALTH_FILES = {
    "README": ["readme"],
    "LICENSE": ["license", "licence"],
    ".gitignore": [".gitignore"],
    "Requirements file": [
        "requirements",
        "pyproject.toml",
        "pipfile",
        "package.json",
        "pom.xml",
        "build.gradle",
        "go.mod",
        "cargo.toml",
        "gemfile",
        "composer.json",
    ],
}


def check_health(root_files):
    results = []

    for name, starts in HEALTH_FILES.items():
        found = any(file_name.lower().startswith(tuple(starts)) for file_name in root_files)
        results.append({"name": name, "found": found})

    return results
