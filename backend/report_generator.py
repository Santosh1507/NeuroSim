"""Report generation for NeuroSim analyses."""

from datetime import datetime
from typing import Any, Dict


def generate_report(analysis: Dict[str, Any], video_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate a structured report from analysis data."""
    report = {
        "title": "NeuroSim Content Analysis Report",
        "generated_at": datetime.now().isoformat(),
        "version": "2.0",
    }

    if video_info:
        report["video"] = {
            "filename": video_info.get("filename", "Unknown"),
            "upload_time": video_info.get("upload_time", "Unknown"),
        }

    report["summary"] = {
        "success_probability": analysis.get("success_probability", 0),
        "viral_potential": analysis.get("viral_potential", 0),
        "hook_score": analysis.get("hook_score", 0),
        "authenticity_score": analysis.get("authenticity_score", 0),
        "risk_score": analysis.get("risk_score", 0),
    }

    report["stage_gate"] = analysis.get("stage_gate", {})
    report["recommendations"] = analysis.get("recommendations", [])
    report["sentiment"] = analysis.get("sentiment_forecast", {})
    report["cta_analysis"] = analysis.get("cta_analysis", {})
    report["brain_response"] = analysis.get("tribev2_brain_response", {})
    report["swarm_simulation"] = analysis.get("mirofish_simulation", {})

    return report


def format_report_text(report: Dict[str, Any]) -> str:
    """Format report as readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append(report["title"])
    lines.append(f"Generated: {report['generated_at']}")
    lines.append(f"Version: {report['version']}")
    lines.append("=" * 60)
    lines.append("")

    if "video" in report:
        lines.append("VIDEO INFO")
        lines.append(f"  Filename: {report['video']['filename']}")
        lines.append(f"  Uploaded: {report['video']['upload_time']}")
        lines.append("")

    lines.append("SUMMARY")
    s = report["summary"]
    lines.append(f"  Success Probability: {s['success_probability']}%")
    lines.append(f"  Viral Potential: {s['viral_potential']}%")
    lines.append(f"  Hook Score: {s['hook_score']}%")
    lines.append(f"  Authenticity: {s['authenticity_score']}%")
    lines.append(f"  Risk Score: {s['risk_score']}%")
    lines.append("")

    sg = report.get("stage_gate", {})
    lines.append("STAGE-GATE")
    lines.append(f"  W_attn: {sg.get('W_attn', 0):.3f}")
    lines.append(f"  Threshold: {sg.get('threshold', 0)}")
    lines.append(f"  Status: {'PASS' if sg.get('passed') else 'FAIL'}")
    lines.append("")

    if report.get("recommendations"):
        lines.append("RECOMMENDATIONS")
        for i, rec in enumerate(report["recommendations"], 1):
            lines.append(f"  {i}. {rec}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)
