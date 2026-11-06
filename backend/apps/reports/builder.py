"""Report data and PDF rendering for a single scan.

`build_report` assembles the prioritised view (also served as JSON);
`render_pdf` turns it into a PDF with ReportLab. All scanner-supplied text is
XML-escaped before it reaches ReportLab's markup-aware Paragraph.
"""
from collections import Counter
from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from apps.vulnerabilities.scoring import PRIORITIES, SEVERITY_RANK

SEVERITIES = ("critical", "high", "medium", "low", "info")
NAVY = colors.HexColor("#12264a")
WINE = colors.HexColor("#800020")
SEV_COLOR = {
    "critical": colors.HexColor("#65001a"),
    "high": colors.HexColor("#c0304f"),
    "medium": colors.HexColor("#d99a2b"),
    "low": colors.HexColor("#2b5490"),
    "info": colors.HexColor("#94a3b8"),
}
OVERALL = {"P1": "Critical", "P2": "High", "P3": "Moderate", "P4": "Low"}


def build_report(scan) -> dict:
    """Prioritised findings plus summary numbers for a scan."""
    vulns = list(scan.vulnerabilities.all())
    vulns.sort(key=lambda v: (-v.risk_score, -SEVERITY_RANK.get(v.severity, 0), v.id))

    by_severity = Counter({s: 0 for s in SEVERITIES})
    by_priority = Counter({p: 0 for p in PRIORITIES})
    items = []
    for rank, v in enumerate(vulns, start=1):
        by_severity[v.severity] += 1
        by_priority[v.priority] += 1
        items.append({
            "rank": rank,
            "id": v.id,
            "title": v.title,
            "severity": v.severity,
            "priority": v.priority,
            "priority_label": PRIORITIES[v.priority],
            "risk_score": v.risk_score,
            "cvss_score": v.cvss_score,
            "cvss_vector": v.cvss_vector,
            "cve_id": v.cve_id,
            "port": v.port,
            "service": v.service,
            "source": v.source,
            "description": v.description,
            "evidence": v.evidence,
            "recommendation": v.recommendation,
            "references": v.references,
        })

    top = next((p for p in PRIORITIES if by_priority[p]), None)
    return {
        "scan": {
            "id": scan.id,
            "name": scan.name,
            "scan_type": scan.get_scan_type_display(),
            "status": scan.status,
            "target_name": scan.target.name,
            "target_value": scan.target.value,
            "started_at": scan.started_at,
            "finished_at": scan.finished_at,
        },
        "total": len(items),
        "by_severity": dict(by_severity),
        "by_priority": dict(by_priority),
        "overall_risk": OVERALL.get(top, "None identified"),
        "simulated": any(i["source"] == "simulated" for i in items),
        "findings": items,
    }


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], textColor=NAVY, fontSize=24, alignment=0, spaceAfter=4),
        "sub": ParagraphStyle("s", parent=base["Normal"], textColor=colors.HexColor("#64748b"), fontSize=10),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], textColor=NAVY, fontSize=15, spaceBefore=14, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], textColor=NAVY, fontSize=11.5, spaceBefore=0, spaceAfter=3),
        "body": ParagraphStyle("b", parent=base["Normal"], fontSize=9.5, leading=13.5),
        "small": ParagraphStyle("sm", parent=base["Normal"], fontSize=8.5, leading=11.5, textColor=colors.HexColor("#475569")),
        "mono": ParagraphStyle("m", parent=base["Code"], fontSize=8, leading=10.5, backColor=colors.HexColor("#f1f5f9"),
                               borderPadding=4, textColor=colors.HexColor("#0f172a")),
        "cell": ParagraphStyle("c", parent=base["Normal"], fontSize=8.5, leading=11),
        "warn": ParagraphStyle("w", parent=base["Normal"], fontSize=9, leading=12, textColor=WINE,
                               backColor=colors.HexColor("#fdecef"), borderPadding=6),
    }


def _p(text, style) -> Paragraph:
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(18 * mm, 10 * mm, "CVST vulnerability report - confidential")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def render_pdf(report: dict) -> bytes:
    st = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
        title=f"CVST report - {report['scan']['name']}", author="CVST",
    )
    width = A4[0] - 36 * mm
    scan = report["scan"]
    story = [
        Paragraph("Vulnerability assessment report", st["title"]),
        _p(f"{scan['name']}  |  generated {timezone.now():%d %b %Y %H:%M} UTC", st["sub"]),
        Spacer(1, 8),
    ]
    if report["simulated"]:
        story += [_p("This report contains SIMULATED demo findings. No packets were sent to the target.", st["warn"]),
                  Spacer(1, 8)]

    def fmt(dt):
        return dt.strftime("%d %b %Y %H:%M UTC") if dt else "-"

    meta = [
        ["Target", f"{scan['target_name']} ({scan['target_value']})"],
        ["Assessment", scan["scan_type"]],
        ["Started", fmt(scan["started_at"])],
        ["Finished", fmt(scan["finished_at"])],
        ["Overall risk", report["overall_risk"]],
        ["Findings", str(report["total"])],
    ]
    t = Table([[_p(k, st["small"]), _p(v, st["body"])] for k, v in meta], colWidths=[32 * mm, width - 32 * mm])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [t, Paragraph("Executive summary", st["h1"])]

    counts = Table(
        [[s.title() for s in SEVERITIES], [str(report["by_severity"][s]) for s in SEVERITIES]],
        colWidths=[width / 5] * 5,
    )
    style = [("ALIGN", (0, 0), (-1, -1), "CENTER"), ("FONTSIZE", (0, 1), (-1, 1), 16),
             ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
             ("BOTTOMPADDING", (0, 1), (-1, 1), 8), ("TOPPADDING", (0, 1), (-1, 1), 8)]
    for i, s in enumerate(SEVERITIES):
        style.append(("BACKGROUND", (i, 0), (i, 0), SEV_COLOR[s]))
    counts.setStyle(TableStyle(style))
    story += [counts, Spacer(1, 8)]

    p1, p2 = report["by_priority"]["P1"], report["by_priority"]["P2"]
    if report["total"] == 0:
        summary = "No findings were recorded for this assessment."
    else:
        summary = (f"{report['total']} finding(s) were recorded. {p1} require immediate action (P1) and {p2} "
                   "are urgent (P2). Findings below are ranked by risk score, which combines the CVSS base score "
                   "(or a nominal estimate for exposure findings without one), the presence of a known CVE, and "
                   "whether the service gives direct control or data when exposed.")
    story.append(_p(summary, st["body"]))

    if report["findings"]:
        story.append(Paragraph("Remediation priorities", st["h1"]))
        rows = [["#", "Priority", "Severity", "Finding", "CVSS", "Risk"]]
        for f in report["findings"]:
            rows.append([
                str(f["rank"]), f["priority"], f["severity"].title(), _p(f["title"], st["cell"]),
                f"{f['cvss_score']:.1f}" if f["cvss_score"] is not None else "n/a", f"{f['risk_score']:.0f}",
            ])
        table = Table(rows, colWidths=[9 * mm, 16 * mm, 20 * mm, width - 75 * mm, 15 * mm, 15 * mm], repeatRows=1)
        ts = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
              ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
              ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
              ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0"))]
        for i, f in enumerate(report["findings"], start=1):
            ts.append(("TEXTCOLOR", (2, i), (2, i), SEV_COLOR[f["severity"]]))
            ts.append(("FONTNAME", (1, i), (2, i), "Helvetica-Bold"))
        table.setStyle(TableStyle(ts))
        story += [table, Spacer(1, 4),
                  _p("P1 fix immediately | P2 fix urgently | P3 plan a fix | P4 monitor / backlog", st["small"]),
                  PageBreak(), Paragraph("Detailed findings", st["h1"])]

        for f in report["findings"]:
            head = f"{f['rank']}. {f['title']}"
            bits = [f"{f['severity'].title()} | {f['priority']} - {f['priority_label']}",
                    f"Risk {f['risk_score']:.0f}/100"]
            if f["cvss_score"] is not None:
                bits.append(f"CVSS {f['cvss_score']:.1f}")
            if f["cve_id"]:
                bits.append(f["cve_id"])
            if f["port"]:
                bits.append(f"port {f['port']}" + (f"/{f['service']}" if f["service"] else ""))
            block = [_p(head, st["h2"]), _p("  |  ".join(bits), st["small"]), Spacer(1, 3)]
            if f["cvss_vector"]:
                block.append(_p(f["cvss_vector"], st["small"]))
            block.append(_p(f["description"] or "No description recorded.", st["body"]))
            if f["evidence"]:
                block += [Spacer(1, 3), _p("Evidence", st["small"]), _p(f["evidence"], st["mono"])]
            if f["recommendation"]:
                block += [Spacer(1, 3), _p("Recommended fix", st["small"]), _p(f["recommendation"], st["body"])]
            if f["references"]:
                block += [Spacer(1, 3), _p("References: " + "  ".join(f["references"][:4]), st["small"])]
            block.append(Spacer(1, 12))
            story.append(KeepTogether(block))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()
