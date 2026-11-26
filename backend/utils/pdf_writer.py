from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

styles = getSampleStyleSheet()


def paragraph(text, style="BodyText"):
    return Paragraph(escape(str(text)), styles[style])


def bullet_list(items):
    return [paragraph(f"• {item}") for item in items]


def summary_table(report):
    ai = report["ai"]
    confidence = f"{ai['confidence']} / 100" if ai["status"] != "skipped" else "-"
    languages = ", ".join(f"{name} ({lines} lines)" for name, lines in report["languages"].items()) or "-"

    rows = [
        ["Final score", f"{report['final_score']} / 100 ({report['grade']})"],
        ["Rule score", f"{report['rules']['score']} / 100"],
        ["AI score", f"{ai['review']['score']} / 100" if ai["status"] == "sure" else "Not sure"],
        ["AI confidence", confidence],
        ["Files", report["total_files"]],
        ["Lines", report["total_lines"]],
        ["Languages", languages],
    ]

    table = Table([[paragraph(a, "BodyText"), paragraph(b, "BodyText")] for a, b in rows], colWidths=[120, 360])
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey)]))
    return table


def problem_lines(report):
    rules = report["rules"]
    lines = [f"{item['reason']} (-{item['points']} points)" for item in rules["penalties"]]
    for secret in rules["secrets"][:20]:
        lines.append(f"{secret['type']} in {secret['file']} line {secret['line']} ({secret['preview']})")
    return lines or ["No problems found by the rules."]


def ai_lines(ai):
    if ai["status"] == "skipped":
        return [paragraph("AI review was skipped because no source code was found.")]
    if ai["status"] == "not_sure":
        return [paragraph(f"The AI review is not sure (confidence {ai['confidence']} / 100), so it is not shown.")]

    review = ai["review"]
    story = [paragraph(f"README summary: {ai['readme_summary']}"), paragraph(review["summary"])]
    story.append(paragraph("Problems", "Heading3"))
    story += bullet_list(review["problems"])
    return story


def make_pdf(report):
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, title="Repository Scan Report")

    story = [
        paragraph("AI GitHub Repository Scanner", "Title"),
        paragraph(report["name"], "Heading2"),
        paragraph(report["url"]),
        Spacer(1, 12),
        summary_table(report),
        Spacer(1, 12),
        paragraph("Problems found", "Heading2"),
        *bullet_list(problem_lines(report)),
        Spacer(1, 12),
        paragraph("AI review", "Heading2"),
        *ai_lines(report["ai"]),
        Spacer(1, 12),
        paragraph("Suggestions", "Heading2"),
        *bullet_list(report["suggestions"] or ["No suggestions."]),
        Spacer(1, 12),
        paragraph("What each agent did", "Heading2"),
        *bullet_list(f"{step['agent']}: {step['message']}" for step in report["log"]),
    ]

    document.build(story)
    return buffer.getvalue()
