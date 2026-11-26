from agents import fetcher_agent, report_agent, review_agent, router_agent, rule_checker_agent, validator_agent
from config import CONFIDENCE_LIMIT, FREE_MODELS, NORMAL_CHUNK_CHARS, SMALL_CHUNK_CHARS, STRONG_MODEL, VALIDATOR_MODEL
from utils.llm_client import ModelBusyError


def add_log(log, agent, message):
    log.append({"agent": agent, "message": message})


def model_order(first, avoid=None):
    models = [first] + [model for model in FREE_MODELS if model != first]
    return [model for model in models if model != avoid]


def call_with_fallback(models, log, agent, action):
    for model in models:
        try:
            return model, action(model)
        except ModelBusyError:
            add_log(log, agent, f"{model} is busy, trying another free model")
    raise RuntimeError("Every free Gemini model is busy right now. Wait a minute and scan again.")


def make_retry_plans(first_model):
    return [
        {"model": first_model, "chunk_chars": NORMAL_CHUNK_CHARS, "strict": False, "note": "first try"},
        {"model": first_model, "chunk_chars": SMALL_CHUNK_CHARS, "strict": True, "note": "retry 1: better prompt and smaller code chunks"},
        {"model": STRONG_MODEL, "chunk_chars": SMALL_CHUNK_CHARS, "strict": True, "note": "retry 2: stronger model"},
    ]


def review_with_retries(repo, first_model, log):
    for number, plan in enumerate(make_retry_plans(first_model), start=1):
        code_sample = review_agent.build_code_sample(repo["files"], plan["chunk_chars"])

        review_model, review = call_with_fallback(
            model_order(plan["model"]),
            log,
            "AI Review Agent",
            lambda model: review_agent.review_code(repo, model, code_sample, plan["strict"]),
        )
        add_log(log, "AI Review Agent", f"Try {number} ({plan['note']}) using {review_model}: score {review['score']}/100")

        validator_model, validation = call_with_fallback(
            model_order(VALIDATOR_MODEL, avoid=review_model),
            log,
            "Validator Agent",
            lambda model: validator_agent.run(review, code_sample, model),
        )
        add_log(log, "Validator Agent", f"Try {number} using {validator_model}: confidence {validation['confidence']}/100. {validation['reason']}")

        if validation["confidence"] >= CONFIDENCE_LIMIT:
            return review, validation, number, review_model, validator_model, True

    add_log(log, "Validator Agent", f"Confidence stayed below {CONFIDENCE_LIMIT} after {number} tries, so the result is marked not sure")
    return review, validation, number, review_model, validator_model, False


def run_ai_review(repo, rules, log):
    if repo["code_lines"] == 0:
        add_log(log, "Router Agent", "No source code found, so the AI review is skipped")
        return {"status": "skipped", "readme_summary": "", "review": None, "confidence": 0, "confidence_reason": "", "tries": 0, "models": {}}

    readme_model, reason = router_agent.choose_model("summarise_readme", repo, rules)
    add_log(log, "Router Agent", f"README summary goes to {readme_model} ({reason})")
    readme_model, readme_summary = call_with_fallback(
        model_order(readme_model),
        log,
        "Router Agent",
        lambda model: review_agent.summarise_readme(repo, model),
    )

    review_model, reason = router_agent.choose_model("review_code", repo, rules)
    add_log(log, "Router Agent", f"Code review goes to {review_model} ({reason})")
    review, validation, tries, used_review_model, used_validator_model, is_sure = review_with_retries(repo, review_model, log)

    return {
        "status": "sure" if is_sure else "not_sure",
        "readme_summary": readme_summary,
        "review": review if is_sure else None,
        "confidence": validation["confidence"],
        "confidence_reason": validation["reason"],
        "tries": tries,
        "models": {"readme": readme_model, "review": used_review_model, "validator": used_validator_model},
    }


def scan_repo(url, log):
    repo = fetcher_agent.run(url)
    add_log(log, "Fetcher Agent", f"Downloaded {repo['name']}: {repo['total_files']} files, {repo['total_lines']} lines")

    rules = rule_checker_agent.run(repo)
    add_log(log, "Rule Checker Agent", f"Found {len(rules['secrets'])} secret(s), rule score {rules['score']}/100")

    ai = run_ai_review(repo, rules, log)

    report = report_agent.build_report(repo, rules, ai, log)
    add_log(log, "Report Agent", f"Final score {report['final_score']}/100 ({report['grade']})")
    return report
