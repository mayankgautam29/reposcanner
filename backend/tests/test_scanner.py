import os
import subprocess

import pytest
from fastapi.testclient import TestClient

import pipeline
from agents import fetcher_agent, report_agent, review_agent, router_agent, rule_checker_agent, validator_agent
from checks.health_check import check_health
from checks.secret_check import find_secrets
from config import SMALL_MODEL, STRONG_MODEL, check_free_models
from main import app
from utils import llm_client

FAKE_KEY = "sk-" + "a1B2c3D4e5F6g7H8i9J0k1L2"


def make_file(path, text):
    return {"path": path, "extension": "." + path.split(".")[-1], "is_code": path.endswith(".py"), "text": text, "lines": len(text.splitlines())}


def make_repo(files, root_files, code_lines=100):
    return {
        "name": "owner/repo",
        "url": "https://github.com/owner/repo",
        "files": files,
        "root_files": root_files,
        "total_files": len(files),
        "total_lines": sum(file["lines"] for file in files),
        "code_lines": code_lines,
        "languages": {"Python": code_lines} if code_lines else {},
    }


def test_valid_github_urls():
    assert fetcher_agent.parse_github_url("https://github.com/owner/repo") == ("owner", "repo")
    assert fetcher_agent.parse_github_url("https://github.com/owner/repo.git/") == ("owner", "repo")


@pytest.mark.parametrize(
    "url",
    ["", "hello", "http://github.com/owner/repo", "https://evil.com/github.com/owner/repo", "file:///etc/passwd", "https://github.com/owner"],
)
def test_bad_urls_are_rejected(url):
    with pytest.raises(ValueError):
        fetcher_agent.parse_github_url(url)


def test_secret_finder_hides_the_value_and_skips_placeholders():
    files = [
        make_file("app.py", f'API = "{FAKE_KEY}"\npassword = "hunter2222"\nname = "ok"\n'),
        make_file("config.py", 'password = "your_password_here"\n'),
    ]
    found = find_secrets(files)

    assert [item["type"] for item in found] == ["OpenAI API key", "Hard-coded password"]
    assert found[0]["line"] == 1
    assert all(FAKE_KEY not in item["preview"] for item in found)


def test_health_check_finds_missing_files():
    health = check_health(["README.md", "main.py"])
    missing = [item["name"] for item in health if not item["found"]]

    assert missing == ["LICENSE", ".gitignore", "Requirements file"]


def test_rule_score_uses_penalties():
    repo = make_repo([make_file("app.py", f'KEY = "{FAKE_KEY}"\n')], ["README.md", "LICENSE", ".gitignore", "requirements.txt"])
    rules = rule_checker_agent.run(repo)

    assert rules["score"] == 90
    assert rules["penalties"][0]["points"] == 10

    repo["root_files"] = ["main.py"]
    assert rule_checker_agent.run(repo)["score"] == 100 - 10 - 5 - 5 - 5 - 10


def test_long_python_function_is_flagged():
    body = "def big():\n" + "    x = 1\n" * 60
    repo = make_repo([make_file("big.py", body)], ["README.md"], code_lines=61)

    assert rule_checker_agent.run(repo)["quality"]["long_functions"][0]["name"] == "big"


def test_router_picks_model_by_task_and_size():
    small = make_repo([], [], code_lines=100)
    big = make_repo([], [], code_lines=2000)
    no_secrets = {"secrets": []}

    assert router_agent.choose_model("summarise_readme", big, no_secrets)[0] == SMALL_MODEL
    assert router_agent.choose_model("review_code", small, no_secrets)[0] == SMALL_MODEL
    assert router_agent.choose_model("review_code", big, no_secrets)[0] == STRONG_MODEL
    assert router_agent.choose_model("review_code", small, {"secrets": [1]})[0] == STRONG_MODEL


def run_with_fake_ai(monkeypatch, confidences):
    repo = make_repo([make_file("app.py", "print('hi')\n"), make_file("README.md", "# Hello")], ["README.md"])
    calls = []
    answers = iter(confidences)

    def fake_review(repo, model, code_sample, strict):
        calls.append({"model": model, "strict": strict, "size": len(code_sample)})
        return {"score": 80, "summary": "ok", "problems": ["p"], "tips": ["Add tests"]}

    monkeypatch.setattr(pipeline.fetcher_agent, "run", lambda url: repo)
    monkeypatch.setattr(review_agent, "summarise_readme", lambda repo, model: "A small app.")
    monkeypatch.setattr(review_agent, "review_code", fake_review)
    monkeypatch.setattr(validator_agent, "run", lambda review, code_sample: {"confidence": next(answers), "reason": "r"})

    return pipeline.scan_repo("https://github.com/owner/repo", []), calls


def test_confident_review_needs_one_try(monkeypatch):
    report, calls = run_with_fake_ai(monkeypatch, [90])

    assert len(calls) == 1
    assert report["ai"]["status"] == "sure"
    assert report["final_score"] == round((report["rules"]["score"] + 80) / 2)
    assert "Add tests" in report["suggestions"]


def test_low_confidence_retries_with_stronger_model(monkeypatch):
    report, calls = run_with_fake_ai(monkeypatch, [40, 60, 85])

    assert [call["strict"] for call in calls] == [False, True, True]
    assert calls[2]["model"] == STRONG_MODEL
    assert report["ai"]["tries"] == 3
    assert report["ai"]["status"] == "sure"


def test_three_low_confidences_mark_result_not_sure(monkeypatch):
    report, calls = run_with_fake_ai(monkeypatch, [10, 20, 30])

    assert len(calls) == 3
    assert report["ai"]["status"] == "not_sure"
    assert report["ai"]["review"] is None
    assert report["final_score"] == report["rules"]["score"]


def test_repo_without_code_skips_ai(monkeypatch):
    repo = make_repo([make_file("README.md", "# Hello")], ["README.md"], code_lines=0)
    monkeypatch.setattr(pipeline.fetcher_agent, "run", lambda url: repo)

    report = pipeline.scan_repo("https://github.com/owner/repo", [])

    assert report["ai"]["status"] == "skipped"


def test_fetcher_reads_a_real_git_repo(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "README.md").write_text("# Demo\n")
    (source / "main.py").write_text("print('hello')\nprint('bye')\n")
    (source / "node_modules").mkdir()
    (source / "node_modules" / "skip.js").write_text("var a;\n")
    (source / "logo.bin").write_bytes(b"\x00\x01\x02")
    for command in (["init"], ["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "first"]):
        subprocess.run(["git", *command], cwd=source, check=True, capture_output=True)

    real_clone = fetcher_agent.Repo.clone_from
    monkeypatch.setattr(fetcher_agent.Repo, "clone_from", lambda url, folder, **options: real_clone(str(source), folder, **options))

    repo = fetcher_agent.run("https://github.com/owner/demo")

    assert repo["name"] == "owner/demo"
    assert repo["total_files"] == 3
    assert repo["languages"] == {"Python": 2}
    assert sorted(file["path"] for file in repo["files"]) == ["README.md", "main.py"]


def test_api_rejects_bad_link():
    response = TestClient(app).post("/scan", json={"url": "not a link"})

    assert response.status_code == 400


def test_api_scan_job_gives_report(monkeypatch):
    run_with_fake_ai(monkeypatch, [90, 90])
    client = TestClient(app)

    job_id = client.post("/scan", json={"url": "https://github.com/owner/repo"}).json()["id"]
    job = client.get(f"/scan/{job_id}").json()

    assert job["status"] == "done"
    assert job["report"]["name"] == "owner/repo"
    assert job["log"][0]["agent"] == "Fetcher Agent"


def test_api_scan_job_reports_errors(monkeypatch):
    def broken_fetch(url):
        raise ValueError("Could not download the repository.")

    monkeypatch.setattr(pipeline.fetcher_agent, "run", broken_fetch)
    client = TestClient(app)

    job_id = client.post("/scan", json={"url": "https://github.com/owner/repo"}).json()["id"]
    job = client.get(f"/scan/{job_id}").json()

    assert job["status"] == "error"
    assert job["error"] == "Could not download the repository."


def test_api_unknown_scan_is_404():
    assert TestClient(app).get("/scan/does-not-exist").status_code == 404


def test_health_and_cors():
    client = TestClient(app)

    assert client.get("/health").json() == {"status": "ok"}
    answer = client.options("/scan", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"})
    assert answer.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_api_makes_pdf(monkeypatch):
    report, _ = run_with_fake_ai(monkeypatch, [90])
    response = TestClient(app).post("/report/pdf", json=report)

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")


def test_pdf_for_not_sure_report(monkeypatch):
    report, _ = run_with_fake_ai(monkeypatch, [1, 2, 3])

    assert report_agent.build_pdf(report).startswith(b"%PDF")


class FakeGemini:
    def __init__(self, text):
        self.text = text
        self.last_call = None
        self.models = self

    def generate_content(self, model, contents, config):
        self.last_call = {"model": model, "contents": contents, "config": config}
        return type("Answer", (), {"text": self.text})()


def test_gemini_client_asks_for_json(monkeypatch):
    fake = FakeGemini('{"score": 70}')
    monkeypatch.setattr(llm_client, "get_client", lambda: fake)

    assert llm_client.ask_json(SMALL_MODEL, "be strict", "review this") == {"score": 70}
    assert fake.last_call["model"] == SMALL_MODEL
    assert fake.last_call["contents"] == "review this"
    assert fake.last_call["config"].system_instruction == "be strict"
    assert fake.last_call["config"].response_mime_type == "application/json"


def test_gemini_client_asks_for_text(monkeypatch):
    fake = FakeGemini("A short summary.")
    monkeypatch.setattr(llm_client, "get_client", lambda: fake)

    assert llm_client.ask_text(SMALL_MODEL, "be brief", "summarise") == "A short summary."
    assert fake.last_call["config"].response_mime_type is None


def test_missing_key_gives_clear_error(monkeypatch):
    monkeypatch.setattr(llm_client, "GEMINI_API_KEY", "")

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        llm_client.get_client()


def test_paid_model_is_refused_before_any_call(monkeypatch):
    fake = FakeGemini("{}")
    monkeypatch.setattr(llm_client, "get_client", lambda: fake)

    with pytest.raises(ValueError, match="free model list"):
        llm_client.ask_json("gemini-3.1-pro-preview", "system", "prompt")
    with pytest.raises(ValueError, match="free model list"):
        llm_client.ask_text("gemini-2.5-pro", "system", "prompt")
    assert fake.last_call is None


def test_default_models_are_all_free():
    check_free_models(SMALL_MODEL, STRONG_MODEL, validator_agent.VALIDATOR_MODEL)
    with pytest.raises(ValueError):
        check_free_models("some-paid-model")


def test_backend_refuses_to_start_with_a_paid_model():
    result = subprocess.run(
        ["python", "-c", "import config"],
        env={**os.environ, "STRONG_MODEL": "gemini-3.1-pro-preview"},
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "free model list" in result.stderr
