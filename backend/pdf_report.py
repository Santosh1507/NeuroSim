"""PDF report generation for NeuroSim analyses."""

from datetime import datetime
from io import BytesIO
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_report(analysis: Dict[str, Any], video_info: Dict[str, Any] = None) -> bytes:
    """Generate PDF report from analysis data."""
    video_info = video_info or {}
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72
    )

    styles = getSampleStyleSheet()
    custom_styles = [
        ParagraphStyle("ReportTitle", fontSize=24, leading=28, spaceAfter=6,
                       textColor=colors.HexColor("#0a0a0f"), fontName="Helvetica-Bold"),
        ParagraphStyle("ReportSubtitle", fontSize=11, leading=14, spaceAfter=12,
                       textColor=colors.HexColor("#666666"), fontName="Helvetica"),
        ParagraphStyle("ReportSection", fontSize=14, leading=18, spaceBefore=16, spaceAfter=8,
                       textColor=colors.HexColor("#0a0a0f"), fontName="Helvetica-Bold"),
        ParagraphStyle("ReportBody", fontSize=10, leading=14, spaceAfter=4,
                       textColor=colors.HexColor("#333333"), fontName="Helvetica"),
        ParagraphStyle("MetricValue", fontSize=18, leading=22, spaceAfter=2,
                       textColor=colors.HexColor("#0a0a0f"), fontName="Helvetica-Bold"),
        ParagraphStyle("MetricLabel", fontSize=8, leading=10, spaceAfter=8,
                       textColor=colors.HexColor("#666666"), fontName="Helvetica"),
        ParagraphStyle("ReportBullet", fontSize=10, leading=14, leftIndent=20, spaceAfter=4,
                       textColor=colors.HexColor("#333333"), fontName="Helvetica",
                       bulletIndent=10),
        ParagraphStyle("Badge", fontSize=9, leading=12, textColor=colors.white,
                       fontName="Helvetica-Bold", alignment=TA_CENTER),
        ParagraphStyle("Footer", fontSize=8, textColor=colors.HexColor("#999999"), alignment=TA_CENTER),
    ]
    for s in custom_styles:
        styles.add(s)

    story = []

    # Header with version badge
    story.append(Paragraph("NeuroSim Analysis Report", styles["ReportTitle"]))
    story.append(
        Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} | v3.0", styles["ReportSubtitle"]
        )
    )
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4deeea"), spaceAfter=12)
    )

    # Source indicator
    analysis_type = analysis.get("analysis_type", "video")
    source = analysis.get("source", "upload")
    if analysis_type == "script":
        story.append(Paragraph("Script Analysis", styles["ReportSection"]))
        story.append(Paragraph("This report was generated from text input (no video upload).", styles["ReportBody"]))
        story.append(Spacer(1, 6))
    elif analysis_type == "youtube":
        story.append(Paragraph("YouTube Analysis", styles["ReportSection"]))
        story.append(Paragraph("This report was generated from a YouTube URL.", styles["ReportBody"]))
        story.append(Spacer(1, 6))

    if video_info:
        story.append(
            Paragraph(f"File: {video_info.get('filename', 'Unknown')}", styles["ReportBody"])
        )
        story.append(Spacer(1, 12))

    # Summary metrics
    story.append(Paragraph("Summary", styles["ReportSection"]))

    metrics = [
        ("Hook Score", f"{analysis.get('hook_score', 0)}%"),
        ("Authenticity", f"{analysis.get('authenticity_score', 0)}%"),
        ("Success Probability", f"{analysis.get('success_probability', 0)}%"),
        ("Viral Potential", f"{analysis.get('viral_potential', 0)}%"),
        ("Risk Score", f"{analysis.get('risk_score', 0)}%"),
    ]

    row_colors = [colors.HexColor("#f8f8f8"), colors.white]
    metric_data = []
    for i, (label, value) in enumerate(metrics):
        bg = row_colors[i % 2]
        metric_data.append([
            Paragraph(label, styles["MetricLabel"]),
            Paragraph(value, styles["MetricValue"]),
        ])

    metric_table = Table(metric_data, colWidths=[2.5 * inch, 2 * inch])
    metric_table.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (0, 0), (-1, -1), row_colors[0]),
        ] + [
            ("BACKGROUND", (0, i), (-1, i), row_colors[i % 2]) for i in range(len(metrics))
        ])
    )
    story.append(metric_table)

    # Stage-Gate
    story.append(Paragraph("Stage-Gate Analysis", styles["ReportSection"]))
    sg = analysis.get("stage_gate", {})
    status = "PASS" if sg.get("passed") else "FAIL"
    status_color = colors.HexColor("#34d399") if sg.get("passed") else colors.HexColor("#f87171")

    sg_data = [
        [Paragraph("W_attn", styles["MetricLabel"]), Paragraph(f"{sg.get('W_attn', 0):.3f}", styles["MetricValue"])],
        [Paragraph("Threshold", styles["MetricLabel"]), Paragraph(f"{sg.get('threshold', 0):.1f}", styles["MetricValue"])],
        [Paragraph("Status", styles["MetricLabel"]), Paragraph(status, ParagraphStyle("StatusStyle", fontSize=18, leading=22, textColor=status_color, fontName="Helvetica-Bold"))],
    ]
    sg_table = Table(sg_data, colWidths=[2.5 * inch, 2 * inch])
    sg_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sg_table)

    # ROI Scores
    brain = analysis.get("analysis_response", {})
    cortical = brain.get("cortical_response", {})
    if cortical:
        story.append(Paragraph("Content Analysis", styles["ReportSection"]))
        roi_data = [
            [Paragraph(k.replace("_", " ").title(), styles["MetricLabel"]), Paragraph(f"{v:.1f}%", styles["MetricValue"])]
            for k, v in cortical.items()
        ]
        roi_table = Table(roi_data, colWidths=[2.5 * inch, 2 * inch])
        roi_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(roi_table)

    # MiroFish Swarm Simulation
    swarm = analysis.get("mirofish_simulation", {})
    if swarm:
        story.append(Paragraph("MiroFish Swarm Simulation", styles["ReportSection"]))
        swarm_data = [
            [Paragraph("Final Sentiment", styles["MetricLabel"]), Paragraph(f"{swarm.get('final_sentiment', 0):.1f}", styles["MetricValue"])],
            [Paragraph("Viral Prediction", styles["MetricLabel"]), Paragraph(str(swarm.get('viral_prediction', 'N/A')), styles["ReportBody"])],
            [Paragraph("Backlash Risk", styles["MetricLabel"]), Paragraph(str(swarm.get('backlash_prediction', 'N/A')), styles["ReportBody"])],
            [Paragraph("Share Prediction", styles["MetricLabel"]), Paragraph(f"{swarm.get('share_prediction', 0):.0f}", styles["MetricValue"])],
        ]
        swarm_table = Table(swarm_data, colWidths=[2.5 * inch, 2 * inch])
        swarm_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(swarm_table)

        # Persona distribution
        personas = swarm.get("persona_distribution", {})
        if personas:
            story.append(Spacer(1, 8))
            story.append(Paragraph("Audience Personas", styles["ReportSection"]))
            persona_data = [
                [Paragraph(k.replace("_", " ").title(), styles["MetricLabel"]), Paragraph(f"{v}%", styles["MetricValue"])]
                for k, v in sorted(personas.items(), key=lambda x: x[1], reverse=True)
            ]
            persona_table = Table(persona_data, colWidths=[2.5 * inch, 2 * inch])
            persona_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(persona_table)

    # Recommendations
    recs = analysis.get("recommendations", [])
    if recs:
        story.append(Paragraph("Recommendations", styles["ReportSection"]))
        for rec in recs:
            story.append(Paragraph(f"• {rec}", styles["ReportBullet"]))

    # Sentiment
    sentiment = analysis.get("sentiment_forecast", {})
    if sentiment:
        story.append(Paragraph("Sentiment Forecast", styles["ReportSection"]))
        sent_data = [
            [Paragraph("Positive", styles["MetricLabel"]), Paragraph(f"{sentiment.get('positive_sentiment_pct', 0):.1f}%", styles["MetricValue"])],
            [Paragraph("Negative", styles["MetricLabel"]), Paragraph(f"{sentiment.get('negative_sentiment_pct', 0):.1f}%", styles["MetricValue"])],
            [Paragraph("Neutral", styles["MetricLabel"]), Paragraph(f"{sentiment.get('neutral_sentiment_pct', 0):.1f}%", styles["MetricValue"])],
            [Paragraph("Shareability", styles["MetricLabel"]), Paragraph(f"{sentiment.get('shareability_index', 0):.1f}%", styles["MetricValue"])],
        ]
        sent_table = Table(sent_data, colWidths=[2.5 * inch, 2 * inch])
        sent_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(sent_table)

    # Footer
    story.append(Spacer(1, 24))
    story.append(
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceBefore=12)
    )
    story.append(
        Paragraph(
            "NeuroSim v3.0 — AI Content Analysis + MiroFish Swarm | Confidential",
            styles["Footer"],
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
