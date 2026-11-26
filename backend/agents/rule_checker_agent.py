from checks.health_check import check_health
from checks.quality_check import check_quality
from checks.rule_score import calculate_rule_score
from checks.secret_check import find_secrets


def run(repo):
    secrets = find_secrets(repo["files"])
    health = check_health(repo["root_files"])
    quality = check_quality(repo["files"])
    score, penalties, suggestions = calculate_rule_score(secrets, health, quality)

    return {
        "secrets": secrets,
        "health": health,
        "quality": quality,
        "score": score,
        "penalties": penalties,
        "suggestions": suggestions,
    }
