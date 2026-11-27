import os
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

import pipeline
from agents import detector_agent, fetcher_agent, report_agent, review_agent, router_agent, rule_checker_agent, validator_agent
from checks.health_check import check_health
from checks.secret_check import find_secrets
from config import SMALL_MODEL, STRONG_MODEL, VALIDATOR_MODEL, check_free_models
from main import app
from utils import llm_client, pdf_writer

FAKE_KEY = "sk-" + "a1B2c3D4e5F6g7H8i9J0k1L2"


@pytest.fixture(autouse=True)
def block_real_detector_calls(monkeypatch):
    def refuse(model, system_prompt, user_prompt):
        raise RuntimeError("blocked in tests")

    monkeypatch.setattr(detector_agent, "ask_json", refuse)


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
    monkeypatch.setattr(validator_agent, "run", lambda review, code_sample, model: {"confidence": next(answers), "reason": "r"})

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
    check_free_models(SMALL_MODEL, STRONG_MODEL, VALIDATOR_MODEL)
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


def test_gemini_client_is_created_once_and_kept(monkeypatch):
    monkeypatch.setattr(llm_client, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(llm_client, "client", None)

    first = llm_client.get_client()
    second = llm_client.get_client()

    assert first is second



class BusyGemini:
    def __init__(self, failures, code):
        self.failures = failures
        self.code = code
        self.calls = 0
        self.models = self

    def generate_content(self, model, contents, config):
        self.calls += 1
        if self.calls <= self.failures:
            raise llm_client.errors.APIError(self.code, {"error": {"message": "busy"}})
        return type("Answer", (), {"text": "done"})()


def test_busy_gemini_is_retried_until_it_answers(monkeypatch):
    fake = BusyGemini(failures=2, code=503)
    monkeypatch.setattr(llm_client, "get_client", lambda: fake)
    monkeypatch.setattr(llm_client.time, "sleep", lambda seconds: None)

    assert llm_client.ask_text(SMALL_MODEL, "system", "prompt") == "done"
    assert fake.calls == 3


def test_busy_gemini_gives_a_friendly_error_after_all_tries(monkeypatch):
    fake = BusyGemini(failures=99, code=503)
    monkeypatch.setattr(llm_client, "get_client", lambda: fake)
    monkeypatch.setattr(llm_client.time, "sleep", lambda seconds: None)

    with pytest.raises(RuntimeError, match="error 503"):
        llm_client.ask_text(SMALL_MODEL, "system", "prompt")
    assert fake.calls == llm_client.MAX_TRIES


def test_rejected_key_is_not_retried(monkeypatch):
    fake = BusyGemini(failures=99, code=400)
    monkeypatch.setattr(llm_client, "get_client", lambda: fake)
    monkeypatch.setattr(llm_client.time, "sleep", lambda seconds: None)

    with pytest.raises(RuntimeError, match="Check GEMINI_API_KEY"):
        llm_client.ask_json(SMALL_MODEL, "system", "prompt")
    assert fake.calls == 1


def run_with_busy_models(monkeypatch, busy_models):
    repo = make_repo([make_file("app.py", "print('hi')\n"), make_file("README.md", "# Hello")], ["README.md"])
    used = {"review": [], "validator": []}

    def fake_review(repo, model, code_sample, strict):
        if model in busy_models:
            raise llm_client.ModelBusyError("busy")
        used["review"].append(model)
        return {"score": 80, "summary": "ok", "problems": ["p"], "tips": ["Add tests"]}

    def fake_validate(review, code_sample, model):
        if model in busy_models:
            raise llm_client.ModelBusyError("busy")
        used["validator"].append(model)
        return {"confidence": 90, "reason": "fine"}

    monkeypatch.setattr(pipeline.fetcher_agent, "run", lambda url: repo)
    monkeypatch.setattr(review_agent, "summarise_readme", lambda repo, model: "small app" if model not in busy_models else (_ for _ in ()).throw(llm_client.ModelBusyError("busy")))
    monkeypatch.setattr(review_agent, "review_code", fake_review)
    monkeypatch.setattr(validator_agent, "run", fake_validate)

    log = []
    return pipeline.scan_repo("https://github.com/owner/repo", log), used, log


def test_busy_model_falls_back_to_another_free_model(monkeypatch):
    busy = {SMALL_MODEL}
    report, used, log = run_with_busy_models(monkeypatch, busy)

    assert report["ai"]["status"] == "sure"
    assert used["review"][0] not in busy
    assert report["ai"]["models"]["review"] == used["review"][0]
    assert report["ai"]["models"]["readme"] not in busy
    assert any("trying another free model" in step["message"] for step in log)


def test_validator_never_uses_the_review_model(monkeypatch):
    report, used, log = run_with_busy_models(monkeypatch, set())

    assert used["validator"][0] != used["review"][0]


def test_all_models_busy_gives_a_clear_error(monkeypatch):
    with pytest.raises(RuntimeError, match="Every free Gemini model is busy"):
        run_with_busy_models(monkeypatch, set(pipeline.FREE_MODELS))


class ReadTimeout(Exception):
    pass


def test_slow_gemini_is_treated_as_busy_without_retrying(monkeypatch):
    class SlowGemini:
        calls = 0
        models = None

        def __init__(self):
            self.models = self

        def generate_content(self, model, contents, config):
            self.calls += 1
            raise ReadTimeout("too slow")

    fake = SlowGemini()
    monkeypatch.setattr(llm_client, "get_client", lambda: fake)

    with pytest.raises(llm_client.ModelBusyError, match="no answer within"):
        llm_client.ask_text(SMALL_MODEL, "system", "prompt")
    assert fake.calls == 1


def test_client_is_built_with_a_timeout(monkeypatch):
    monkeypatch.setattr(llm_client, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(llm_client, "client", None)

    assert llm_client.get_client()._api_client._http_options.timeout == llm_client.TIMEOUT_MS


def test_gemini_that_never_answers_hits_the_deadline(monkeypatch):
    class HangingGemini:
        models = None

        def __init__(self):
            self.models = self

        def generate_content(self, model, contents, config):
            time.sleep(1)
            return type("Answer", (), {"text": "late"})()

    monkeypatch.setattr(llm_client, "get_client", lambda: HangingGemini())
    monkeypatch.setattr(llm_client, "DEADLINE_SECONDS", 0.1)

    with pytest.raises(llm_client.ModelBusyError, match="no answer within"):
        llm_client.ask_text(SMALL_MODEL, "system", "prompt")


def test_rate_limit_is_not_retried_on_the_same_model(monkeypatch):
    fake = BusyGemini(failures=99, code=429)
    monkeypatch.setattr(llm_client, "get_client", lambda: fake)
    monkeypatch.setattr(llm_client.time, "sleep", lambda seconds: None)

    with pytest.raises(llm_client.ModelBusyError, match="error 429"):
        llm_client.ask_text(SMALL_MODEL, "system", "prompt")
    assert fake.calls == 1


def test_validator_reuses_review_model_only_as_last_resort(monkeypatch):
    others_busy = set(pipeline.FREE_MODELS) - {SMALL_MODEL}
    report, used, log = run_with_busy_models(monkeypatch, others_busy)

    assert used["review"] == [SMALL_MODEL]
    assert used["validator"] == [SMALL_MODEL]
    assert report["ai"]["status"] == "sure"
    assert any("checked its own review" in step["message"] for step in log)


def big_python_file(path, lines):
    return make_file(path, ("value = 1" + chr(10)) * lines)


def test_detector_weights_files_by_their_lines(monkeypatch):
    repo = make_repo([big_python_file("big.py", 100), big_python_file("small.py", 20)], ["README.md"])
    answer = {
        "files": [{"path": "small.py", "ai_percent": 10}, {"path": "big.py", "ai_percent": 90}, {"path": "ghost.py", "ai_percent": 99}],
        "signals": ["Very even style"],
        "confidence": 65,
    }
    monkeypatch.setattr(detector_agent, "ask_json", lambda model, system_prompt, user_prompt: answer)

    result = detector_agent.run(repo, SMALL_MODEL)

    assert result["status"] == "done"
    assert result["percent"] == 77
    assert result["label"] == "Mostly AI-written"
    assert [item["path"] for item in result["files"]] == ["big.py", "small.py"]
    assert result["files_checked"] == 2
    assert result["lines_checked"] == 120
    assert result["confidence"] == 65
    assert result["signals"] == ["Very even style"]


@pytest.mark.parametrize("percent,label", [(0, "Mostly human-written"), (29, "Mostly human-written"), (30, "Mixed"), (69, "Mixed"), (70, "Mostly AI-written"), (100, "Mostly AI-written")])
def test_detector_labels(percent, label):
    assert detector_agent.get_label(percent) == label


def test_detector_keeps_percent_between_0_and_100(monkeypatch):
    repo = make_repo([big_python_file("a.py", 30)], ["README.md"])
    monkeypatch.setattr(detector_agent, "ask_json", lambda model, system_prompt, user_prompt: {"files": [{"path": "a.py", "ai_percent": 250}]})

    assert detector_agent.run(repo, SMALL_MODEL)["percent"] == 100


def test_detector_skips_tiny_files_without_calling_the_ai(monkeypatch):
    repo = make_repo([make_file("tiny.py", "print('hi')")], ["README.md"])

    assert detector_agent.run(repo, SMALL_MODEL)["status"] == "skipped"


def test_detector_only_sends_the_biggest_files(monkeypatch):
    files = [big_python_file(f"file{number}.py", 20 + number) for number in range(8)]
    repo = make_repo(files, ["README.md"])
    seen = {}

    def fake(model, system_prompt, user_prompt):
        seen["prompt"] = user_prompt
        return {"files": [{"path": "file7.py", "ai_percent": 40}]}

    monkeypatch.setattr(detector_agent, "ask_json", fake)
    detector_agent.run(repo, SMALL_MODEL)

    assert seen["prompt"].count("### ") == detector_agent.DETECT_FILES
    assert "### file7.py" in seen["prompt"]
    assert "### file0.py" not in seen["prompt"]


def test_detector_complains_when_the_model_returns_nothing_useful(monkeypatch):
    repo = make_repo([big_python_file("a.py", 30)], ["README.md"])
    monkeypatch.setattr(detector_agent, "ask_json", lambda model, system_prompt, user_prompt: {"files": [{"path": "other.py", "ai_percent": 50}]})

    with pytest.raises(ValueError):
        detector_agent.run(repo, SMALL_MODEL)


def scan_with_detector(monkeypatch, detector_answer):
    repo = make_repo([big_python_file("app.py", 40), make_file("README.md", "# Hello")], ["README.md"], code_lines=40)
    monkeypatch.setattr(pipeline.fetcher_agent, "run", lambda url: repo)
    monkeypatch.setattr(review_agent, "summarise_readme", lambda repo, model: "A small app.")
    monkeypatch.setattr(review_agent, "review_code", lambda repo, model, code_sample, strict: {"score": 80, "summary": "ok", "problems": [], "tips": []})
    monkeypatch.setattr(validator_agent, "run", lambda review, code_sample, model: {"confidence": 90, "reason": "r"})
    monkeypatch.setattr(detector_agent, "ask_json", detector_answer)

    log = []
    return pipeline.scan_repo("https://github.com/owner/repo", log), log


def test_report_carries_the_ai_written_estimate(monkeypatch):
    report, log = scan_with_detector(monkeypatch, lambda model, system_prompt, user_prompt: {"files": [{"path": "app.py", "ai_percent": 35}], "signals": ["Mixed style"], "confidence": 50})

    assert report["ai_detection"]["status"] == "done"
    assert report["ai_detection"]["percent"] == 35
    assert report["ai_detection"]["label"] == "Mixed"
    assert report["ai_detection"]["model"] == SMALL_MODEL
    assert report["ai_detection"]["code_lines"] == 40
    assert any(step["agent"] == "AI Detector Agent" and "35%" in step["message"] for step in log)
    assert report["final_score"] == round((report["rules"]["score"] + 80) / 2)


def test_scan_still_works_when_the_ai_check_fails(monkeypatch):
    def always_busy(model, system_prompt, user_prompt):
        raise llm_client.ModelBusyError("error 503")

    report, log = scan_with_detector(monkeypatch, always_busy)

    assert report["ai_detection"]["status"] == "unavailable"
    assert report["ai"]["status"] == "sure"
    assert any("Could not estimate AI-written code" in step["message"] for step in log)


def test_scan_without_code_skips_the_ai_check(monkeypatch):
    repo = make_repo([make_file("README.md", "# Hello")], ["README.md"], code_lines=0)
    monkeypatch.setattr(pipeline.fetcher_agent, "run", lambda url: repo)

    report = pipeline.scan_repo("https://github.com/owner/repo", [])

    assert report["ai_detection"]["status"] == "skipped"


def test_pdf_shows_the_ai_written_estimate(monkeypatch):
    report, log = scan_with_detector(monkeypatch, lambda model, system_prompt, user_prompt: {"files": [{"path": "app.py", "ai_percent": 35}], "signals": ["Mixed style"]})

    assert report_agent.build_pdf(report).startswith(b"%PDF")
    assert any("35%" in line.getPlainText() for line in pdf_writer.detection_lines(report["ai_detection"]))
    del report["ai_detection"]
    assert report_agent.build_pdf(report).startswith(b"%PDF")
