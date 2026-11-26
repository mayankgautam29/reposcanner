from agents import fetcher_agent, report_agent, review_agent, router_agent, rule_checker_agent, validator_agent
from config import CONFIDENCE_LIMIT, NORMAL_CHUNK_CHARS, SMALL_CHUNK_CHARS, STRONG_MODEL, VALIDATOR_MODEL


def add_log(log, agent, message):
    log.append({"agent": agent, "message": message})


def make_retry_plans(first_model):
    return [
        {"model": first_model, "chunk_chars": NORMAL_CHUNK_CHARS, "strict": False, "note": "first try"},
        {"model": first_model, "chunk_chars": SMALL_CHUNK_CHARS, "strict": True, "note": "retry 1: better prompt and smaller code chunks"},
        {"model": STRONG_MODEL, "chunk_chars": SMALL_CHUNK_CHARS, "strict": True, "note": "retry 2: stronger model"},
    ]


def review_with_retries(repo, first_model, log):
    for number, plan in enumerate(make_retry_plans(first_model), start=1):
        code_sample = review_agent.build_code_sample(repo["files"], plan["chunk_chars"])
        review = review_agent.review_code(repo, plan["model"], code_sample, plan["strict"])
        add_log(log, "AI Review Agent", f"Try {number} ({plan['note']}) using {plan['model']}: score {review['score']}/100")

        validation = validator_agent.run(review, code_sample)
        add_log(log, "Validator Agent", f"Try {number}: confidence {validation['confidence']}/100. {validation['reason']}")

        if validation["confidence"] >= CONFIDENCE_LIMIT:
            return review, validation, number, plan["model"], True

    add_log(log, "Validator Agent", f"Confidence stayed below {CONFIDENCE_LIMIT} after {number} tries, so the result is marked not sure")
    return review, validation, number, plan["model"], False


def run_ai_review(repo, rules, log):
    if repo["code_lines"] == 0:
        add_log(log, "Router Agent", "No source code found, so the AI review is skipped")
        return {"status": "skipped", "readme_summary": "", "review": None, "confidence": 0, "confidence_reason": "", "tries": 0, "models": {}}

    readme_model, reason = router_agent.choose_model("summarise_readme", repo, rules)
    add_log(log, "Router Agent", f"README summary goes to {readme_model} ({reason})")
    readme_summary = review_agent.summarise_readme(repo, readme_model)

    review_model, reason = router_agent.choose_model("review_code", repo, rules)
    add_log(log, "Router Agent", f"Code review goes to {review_model} ({reason})")
    review, validation, tries, last_model, is_sure = review_with_retries(repo, review_model, log)

    return {
        "status": "sure" if is_sure else "not_sure",
        "readme_summary": readme_summary,
        "review": review if is_sure else None,
        "confidence": validation["confidence"],
        "confidence_reason": validation["reason"],
        "tries": tries,
        "models": {"readme": readme_model, "review": last_model, "validator": VALIDATOR_MODEL},
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
