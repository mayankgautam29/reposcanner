from utils.pdf_writer import make_pdf


def get_grade(score):
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Needs improvement"
    return "Poor"


def build_report(repo, rules, ai, log):
    if ai["status"] == "sure":
        final_score = round((rules["score"] + ai["review"]["score"]) / 2)
        suggestions = rules["suggestions"] + ai["review"]["tips"]
    else:
        final_score = rules["score"]
        suggestions = rules["suggestions"]

    return {
        "name": repo["name"],
        "url": repo["url"],
        "languages": repo["languages"],
        "total_files": repo["total_files"],
        "total_lines": repo["total_lines"],
        "rules": {
            "score": rules["score"],
            "penalties": rules["penalties"],
            "secrets": rules["secrets"],
            "health": rules["health"],
            "quality": rules["quality"],
        },
        "ai": ai,
        "final_score": final_score,
        "grade": get_grade(final_score),
        "suggestions": suggestions,
        "log": log,
    }


def build_pdf(report):
    return make_pdf(report)
