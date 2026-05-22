"""Waitlist signup routes with PostgreSQL persistence and SMTP HTML emails."""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from database import db
from config import settings
from routes.digest import _send_email_smtp

logger = logging.getLogger(__name__)

router = APIRouter(tags=["waitlist"])


class WaitlistRequest(BaseModel):

    email: EmailStr
    name: Optional[str] = None


def _format_waitlist_html(email: str, name: str, queue_position: int) -> str:
    """Build a premium HTML email body for the waitlist confirmation."""
    display_name = name if name else "there"
    dashboard_url = settings.app_base_url.rstrip("/") if settings.app_base_url else "https://neurosimai.vercel.app"
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      margin: 0;
      padding: 0;
      background-color: #030712;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #f3f4f6;
    }}
    .email-container {{
      max-width: 580px;
      margin: 40px auto;
      background-color: #0b0f19;
      border: 1px solid #1f2937;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    .header {{
      background: linear-gradient(135deg, #1e1b4b, #311042);
      padding: 48px 32px;
      text-align: center;
      border-bottom: 1px solid #1f2937;
    }}
    .logo {{
      font-size: 26px;
      font-weight: 800;
      color: #ffffff;
      letter-spacing: -0.03em;
      margin: 0 0 12px 0;
      background: linear-gradient(to right, #6366f1, #d946ef);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .title {{
      font-size: 20px;
      font-weight: 700;
      color: #ffffff;
      margin: 0;
    }}
    .content {{
      padding: 32px;
      line-height: 1.6;
    }}
    .greeting {{
      font-size: 16px;
      font-weight: 600;
      color: #ffffff;
      margin-top: 0;
    }}
    .body-text {{
      font-size: 15px;
      color: #9ca3af;
      margin-bottom: 24px;
    }}
    .badge {{
      display: inline-block;
      background: rgba(99, 102, 241, 0.15);
      border: 1px solid rgba(99, 102, 241, 0.3);
      color: #818cf8;
      font-size: 13px;
      font-weight: 600;
      padding: 4px 12px;
      border-radius: 9999px;
      margin-bottom: 24px;
    }}
    .position-box {{
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(217, 70, 239, 0.05));
      border: 1px solid rgba(99, 102, 241, 0.2);
      border-radius: 12px;
      padding: 24px;
      text-align: center;
      margin-bottom: 32px;
    }}
    .position-label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #9ca3af;
      margin-bottom: 8px;
    }}
    .position-number {{
      font-size: 42px;
      font-weight: 800;
      color: #ffffff;
      margin: 0;
      background: linear-gradient(to right, #818cf8, #f472b6);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .features-title {{
      font-size: 14px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #e5e7eb;
      margin-bottom: 16px;
      border-bottom: 1px solid #1f2937;
      padding-bottom: 8px;
    }}
    .feature-item {{
      margin-bottom: 16px;
    }}
    .feature-name {{
      font-size: 14px;
      font-weight: 600;
      color: #ffffff;
    }}
    .feature-desc {{
      font-size: 13px;
      color: #9ca3af;
      margin: 2px 0 0 0;
    }}
    .cta-button {{
      display: block;
      background: linear-gradient(to right, #6366f1, #d946ef);
      color: #ffffff !important;
      text-align: center;
      text-decoration: none;
      font-weight: 600;
      font-size: 15px;
      padding: 14px 24px;
      border-radius: 8px;
      margin-top: 32px;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }}
    .footer {{
      padding: 24px 32px;
      background-color: #070a13;
      border-top: 1px solid #1f2937;
      text-align: center;
      font-size: 12px;
      color: #4b5563;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <div class="logo">NeuroSim</div>
      <div class="title">You're on the list!</div>
    </div>
    <div class="content">
      <p class="greeting">Hi {display_name},</p>
      <p class="body-text">
        Thank you for your interest in NeuroSim! We are building the next generation of predictive content optimization tools, combining state-of-the-art vision models with neural cognitive engagement prediction.
      </p>
      
      <div class="position-box">
        <div class="position-label">Your Waitlist Position</div>
        <div class="position-number">#{queue_position}</div>
      </div>

      <div class="features-title">What is NeuroSim?</div>
      
      <div class="feature-item">
        <div class="feature-name">🧠 Real-time Multimodal Video Scoring</div>
        <p class="feature-desc">Upload your video clips to extract frame-by-frame engagement trends, CTA efficacy, and predicted hook scores using advanced AI vision.</p>
      </div>

      <div class="feature-item">
        <div class="feature-name">📊 Predictive A/B Testing Workspace</div>
        <p class="feature-desc">Persist, compare, and contrast variations of scripts or videos side-by-side to optimize retention curves and maximize virality potential.</p>
      </div>

      <div class="feature-item">
        <div class="feature-name">⚡ Cognitive Brain Model Visualization</div>
        <p class="feature-desc">Map visual, auditory, and emotional stimuli straight to a interactive 3D representation of regional cortical activation.</p>
      </div>

      <a href="{dashboard_url}" class="cta-button">Visit NeuroSim Workspace</a>
    </div>
    <div class="footer">
      &copy; 2026 NeuroSim AI. All rights reserved.<br>
      You received this email because you signed up for the NeuroSim waitlist with the email: {email}.
    </div>
  </div>
</body>
</html>
"""
    return html


@router.post("/waitlist")
@router.post("/api/v1/waitlist")
async def join_waitlist(req: WaitlistRequest):
    """Register email persistently, calculate queue position, and send transactional confirmation."""
    email = req.email.lower().strip()
    
    # 1. Prevent duplicates
    is_registered = await db.is_waitlist_email_registered(email)
    if is_registered:
        raise HTTPException(
            status_code=409,
            detail="You're already on the waitlist!"
        )
        
    # 2. Insert persistently to DB
    try:
        record = await db.insert_waitlist(email)
        queue_pos = record.get("queue_position", 1)
    except ValueError as val_err:
        raise HTTPException(status_code=409, detail=str(val_err))
    except Exception as e:
        logger.error(f"Failed to insert into waitlist: {e}")
        raise HTTPException(status_code=500, detail="Database insertion failed.")

    # 3. Send transactional confirmation email
    smtp_configured = bool(settings.email_host and settings.email_username)
    email_status = "simulated"
    
    subject = "Welcome to the NeuroSim Waitlist! 🚀"
    html_body = _format_waitlist_html(email, req.name, queue_pos)
    
    if smtp_configured:
        ok = _send_email_smtp(email, subject, html_body)
        if ok:
            email_status = "delivered"
            logger.info(f"[WAITLIST] Sent confirmation email to {email}")
        else:
            email_status = "failed"
            logger.error(f"[WAITLIST] Failed to send confirmation email to {email}")
    else:
        logger.info(f"[WAITLIST] [SIMULATED] Sent confirmation email to {email}")
        
    return {
        "message": "Joined waitlist!",
        "email": email,
        "queue_position": queue_pos,
        "email_status": email_status
    }
