# Cron-Job.org Uptime Monitor

[**cron-job.org**](https://cron-job.org) is a free cron job service that can ping your Render backend every 10 minutes to prevent free-tier spin-down and alert you if the service goes down.

## Why This Matters

Render's free tier spins down after **15 minutes of inactivity**. If no one visits your app, the next request will experience a ~30s cold start. This cron job keeps the service warm.

## Setup

1. **Create an account** at [cron-job.org](https://cron-job.org)
2. **Add a new cron job:**

   | Field | Value |
   |-------|-------|
   | **Title** | `NeuroSim Warmup` |
   | **URL** | `https://neurosim-nm22.onrender.com/` |
   | **Execution interval** | Every 10 minutes |
   | **Request method** | `GET` |
   | **Timeout** | `15` seconds |
   | **Save log** | Checked |

3. **Optionally set up notifications:**
   - Go to **Account → Notifications**
   - Add your email for failure alerts
   - Configure when to notify (e.g., on failure only)

## How It Works

- The job sends a `GET` request every 10 minutes (within Render's 15-min spin-down window)
- The `/` endpoint is lightweight (no heavy processing)
- If Render returns a non-200 status or times out, cron-job.org sends an email alert

## Alternative: GitHub Actions (already configured)

We also have a GitHub Actions workflow (`.github/workflows/warmup.yml`) that pings Render every 10 minutes. However, GitHub Actions has scheduling latency (~2-10 min on free tier), so cron-job.org is more reliable for keeping the service consistently warm.

## Alternative: UptimeRobot

[UptimeRobot](https://uptimerobot.com/) offers 50 monitors on their free plan with 5-minute check intervals and email alerts.

## Note on Cold Starts

Even with a 10-minute ping, Render may occasionally spin down during maintenance periods. Cold starts take ~30 seconds. This is normal for free tier.
