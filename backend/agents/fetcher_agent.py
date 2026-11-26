import os
import re
import shutil
import stat
import tempfile

from git import Repo
from git.exc import GitCommandError

from config import MAX_FILE_SIZE

GITHUB_URL = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+?)(\.git)?/?$")

SKIP_FOLDERS = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".next"}

LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".rs": "Rust",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".dart": "Dart",
    ".html": "HTML",
    ".css": "CSS",
}


def parse_github_url(url):
    match = GITHUB_URL.match(url.strip())
    if not match:
        raise ValueError("Please enter a valid public GitHub link like https://github.com/owner/repo")
    return match.group(1), match.group(2)


def read_text(path):
    if os.path.getsize(path) > MAX_FILE_SIZE:
        return None
    with open(path, "rb") as file:
        data = file.read()
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="ignore")


def read_repo_files(folder):
    files = []
    root_files = []
    total_files = 0

    for current, folders, names in os.walk(folder):
        folders[:] = [name for name in folders if name not in SKIP_FOLDERS]
        for name in names:
            path = os.path.join(current, name)
            if os.path.islink(path):
                continue

            total_files += 1
            if current == folder:
                root_files.append(name)

            text = read_text(path)
            if text is None:
                continue

            extension = os.path.splitext(name)[1].lower()
            files.append(
                {
                    "path": os.path.relpath(path, folder).replace("\\", "/"),
                    "extension": extension,
                    "is_code": extension in LANGUAGES,
                    "text": text,
                    "lines": len(text.splitlines()),
                }
            )

    return files, root_files, total_files


def count_languages(files):
    languages = {}
    for file in files:
        language = LANGUAGES.get(file["extension"])
        if language:
            languages[language] = languages.get(language, 0) + file["lines"]
    return languages


def remove_folder(folder):
    def make_writable_and_retry(function, path, error):
        os.chmod(path, stat.S_IWRITE)
        function(path)

    shutil.rmtree(folder, onexc=make_writable_and_retry)


def run(url):
    owner, repo_name = parse_github_url(url)
    folder = tempfile.mkdtemp()

    try:
        Repo.clone_from(
            f"https://github.com/{owner}/{repo_name}.git",
            folder,
            depth=1,
            env={"GIT_TERMINAL_PROMPT": "0"},
        )
        files, root_files, total_files = read_repo_files(folder)
    except GitCommandError:
        raise ValueError("Could not download the repository. Check that the link is correct and the repo is public.")
    finally:
        remove_folder(folder)

    languages = count_languages(files)

    return {
        "name": f"{owner}/{repo_name}",
        "url": f"https://github.com/{owner}/{repo_name}",
        "files": files,
        "root_files": root_files,
        "total_files": total_files,
        "total_lines": sum(file["lines"] for file in files),
        "code_lines": sum(languages.values()),
        "languages": languages,
    }
