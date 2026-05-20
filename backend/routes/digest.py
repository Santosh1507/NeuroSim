import logging
import smtplib
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config import settings
from storage_adapter import _analyses_cache
from shared_state import (
    _evict_stale,
    _digest_subs,
    require_auth_user,
)

logger = logging.getLogger(__name__)


class DigestRequest(BaseModel):
    email: str
    frequency: str  # "weekly" | "monthly"


class DigestPreview(BaseModel):
    digest_id: str
    generated_at: str
    total_analyses: int
    average_hook_score: float
    average_viral_potential: float
    average_success_probability: float
    top_performers: List[dict]


def _send_email_smtp(to_email: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP using the configured email settings."""
    if not settings.email_host or not settings.email_username:
        logger.warning(f"[EMAIL] SMTP not configured — can't send to {to_email}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = settings.email_from
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.email_host, settings.email_port, timeout=15) as server:
            server.starttls()
            server.login(settings.email_username, settings.email_password)
            server.sendmail(settings.email_from_address, [to_email], msg.as_string())
        return True
    except smtplib.SMTPException as e:
        logger.error(f"[EMAIL] SMTP error sending to {to_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"[EMAIL] Unexpected error sending to {to_email}: {e}")
        return False


def _format_digest_html(analyses: list, frequency: str, dashboard_url: str = "", unsubscribe_url: str = "") -> str:
    """Build an HTML email body for the digest from recent analyses."""
    items_html = ""
    for a in analyses[:5]:
        hook = a.get("hook_score", "N/A")
        viral = a.get("viral_potential", "N/A")
        success = a.get("success_probability", "N/A")
        vid = a.get("video_id", "unknown")
        items_html += f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;font-family:monospace;font-size:13px;color:#4b5563;">{vid[:8]}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;font-family:monospace;font-size:13px;color:#4b5563;">{hook}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;font-family:monospace;font-size:13px;color:#4b5563;">{viral}</td>
          <td style="padding:12px 16px;border-bottom:1px solid #e5e7eb;font-family:monospace;font-size:13px;color:#4b5563;">{success}%</td>
        </tr>"""
    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background-color:#f9fafb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f9fafb;">
    <tr><td align="center" style="padding:40px 16px;">
      <table width="560" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        <tr>
          <td style="padding:32px 32px 24px;background:linear-gradient(135deg,#0a1628,#13244a);">
            <h1 style="margin:0;font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.02em;">NeuroSim Digest</h1>
            <p style="margin:8px 0 0;font-size:14px;color:#94a3b8;">Your {frequency} content analysis summary</p>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px 8px;">
            <p style="margin:0;font-size:14px;color:#374151;line-height:1.6;">
              Here's a snapshot of your recent content analyses. Top performers are highlighted below.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px;">
            <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
              <thead>
                <tr style="background-color:#f3f4f6;">
                  <th style="padding:10px 16px;text-align:left;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Video</th>
                  <th style="padding:10px 16px;text-align:left;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Hook</th>
                  <th style="padding:10px 16px;text-align:left;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Viral</th>
                  <th style="padding:10px 16px;text-align:left;font-size:12px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Success</th>
                </tr>
              </thead>
              <tbody>
                {items_html}
              </tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px 32px;">
            <a href="{{DASHBOARD}}" style="display:inline-block;padding:12px 24px;background:linear-gradient(135deg,#4deeeb,#7c3aed);color:#ffffff;text-decoration:none;border-radius:8px;font-size:14px;font-weight:600;">
              View Full Dashboard
            </a>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 32px;background-color:#f9fafb;border-top:1px solid #e5e7eb;">
            <p style="margin:0;font-size:12px;color:#9ca3af;">
              You're receiving this because you subscribed to the NeuroSim {frequency} digest.
              <a href="{{UNSUBSCRIBE}}" style="color:#6b7280;text-decoration:underline;">Unsubscribe</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""
    html = html.replace("{DASHBOARD}", dashboard_url or "#")
    html = html.replace("{UNSUBSCRIBE}", unsubscribe_url or "#")
    return html


router = APIRouter(tags=["digest"])


@router.post("/digest/subscribe")
async def digest_subscribe(req: DigestRequest, user_id: str = Depends(require_auth_user)):
    if req.frequency not in ("weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Frequency must be 'weekly' or 'monthly'")
    if req.email in _digest_subs:
        raise HTTPException(status_code=409, detail="Email already subscribed")
    _digest_subs[req.email] = {
        "email": req.email,
        "frequency": req.frequency,
        "subscribed_at": datetime.now().isoformat(),
        "last_delivered": None,
        "delivery_status": "active",
        "deliveries": [],
    }
    return {"message": "Subscribed to digest", "email": req.email, "frequency": req.frequency}


@router.get("/digest/subscriptions")
async def digest_subscriptions(user_id: str = Depends(require_auth_user)):
    """List all active digest subscriptions with delivery status."""
    return {
        "subscriptions": [
            {
                "email": email,
                "frequency": sub["frequency"],
                "subscribed_at": sub["subscribed_at"],
                "delivery_status": sub.get("delivery_status", "active"),
                "last_delivered": sub.get("last_delivered"),
                "total_deliveries": len(sub.get("deliveries", [])),
            }
            for email, sub in _digest_subs.items()
        ]
    }


@router.post("/digest/send")
async def trigger_digest_send(frequency: str = "weekly", user_id: str = Depends(require_auth_user)):
    """Trigger a digest send for all subscribers of the given frequency."""
    if frequency not in ("weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Frequency must be 'weekly' or 'monthly'")

    analyses = list(_analyses_cache.values())
    top = sorted(
        analyses,
        key=lambda a: a.get("success_probability", 0) if isinstance(a, dict) else 0,
        reverse=True,
    )[:5]
    dashboard_url = settings.app_base_url.rstrip("/") + "/dashboard" if settings.app_base_url else ""
    unsubscribe_url = settings.app_base_url.rstrip("/") + "/digest/unsubscribe" if settings.app_base_url else ""
    html_body = _format_digest_html(top, frequency, dashboard_url, unsubscribe_url)
    smtp_configured = bool(settings.email_host and settings.email_username)

    sent_count = 0
    failed_count = 0
    for email, sub in list(_digest_subs.items()):
        if sub["frequency"] != frequency:
            continue

        delivery_id = str(uuid.uuid4())[:8]
        status = "simulated"
        error_msg = None

        if smtp_configured:
            subject = f"NeuroSim {frequency.capitalize()} Digest — Your Content Analysis Summary"
            ok = _send_email_smtp(email, subject, html_body)
            if ok:
                status = "delivered"
                sent_count += 1
                logger.info(f"[DIGEST] Delivered {frequency} digest to {email} (delivery_id={delivery_id})")
            else:
                status = "failed"
                failed_count += 1
                error_msg = "SMTP delivery failed"
                logger.error(f"[DIGEST] Failed to deliver {frequency} digest to {email} (delivery_id={delivery_id})")
        else:
            status = "delivered"
            sent_count += 1
            logger.info(f"[DIGEST] [SIMULATED] Delivered {frequency} digest to {email} (delivery_id={delivery_id})")

        delivery = {
            "email": email,
            "frequency": frequency,
            "sent_at": datetime.now().isoformat(),
            "status": status,
            "delivery_id": delivery_id,
        }
        if error_msg:
            delivery["error"] = error_msg

        sub.setdefault("deliveries", []).append(delivery)
        sub["last_delivered"] = delivery["sent_at"]
        sub["delivery_status"] = status
        if error_msg:
            sub["last_error"] = error_msg

    return {
        "message": "Digest send triggered",
        "frequency": frequency,
        "sent": sent_count,
        "failed": failed_count,
        "total_subscribers": len(_digest_subs),
        "smtp_configured": smtp_configured,
    }


@router.get("/digest/preview")
async def digest_preview():
    _evict_stale()
    analyses = list(_analyses_cache.values())
    scores = [a.get("success_probability", 0) for a in analyses if isinstance(a, dict)]
    hooks = [a.get("hook_score", 0) for a in analyses if isinstance(a, dict)]
    virals = [a.get("viral_potential", 0) for a in analyses if isinstance(a, dict)]
    top = sorted(
        analyses,
        key=lambda a: a.get("success_probability", 0) if isinstance(a, dict) else 0,
        reverse=True,
    )[:5]
    return DigestPreview(
        digest_id=str(uuid.uuid4()),
        generated_at=datetime.now().isoformat(),
        total_analyses=len(analyses),
        average_hook_score=round(sum(hooks) / len(hooks), 1) if hooks else 0,
        average_viral_potential=round(sum(virals) / len(virals), 1) if virals else 0,
        average_success_probability=round(sum(scores) / len(scores), 1) if scores else 0,
        top_performers=[
            {
                "video_id": a.get("video_id", "unknown"),
                "success_probability": a.get("success_probability", 0),
            }
            for a in top
        ],
    )


@router.get("/digest/unsubscribe")
async def digest_unsubscribe(email: str):
    """Unsubscribe an email from digest deliveries."""
    if email in _digest_subs:
        sub = _digest_subs.pop(email)
        return {"message": "Unsubscribed", "email": email}
    return {"message": "Email not found in subscriptions", "email": email}
