# Deploy NeuroSim v3.0 — Setup Script
# Run this after cloning to set up all deployment surfaces.

param(
    [switch]$SkipSecrets,
    [switch]$SkipDeploy,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path $PSScriptRoot -Parent

Write-Host "=== NeuroSim v3.0 Deploy Setup ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check prerequisites
Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Yellow

$hasGh = Get-Command gh -ErrorAction SilentlyContinue
if (-not $hasGh) {
    Write-Host "  ERROR: GitHub CLI (gh) not installed. Install from https://cli.github.com/" -ForegroundColor Red
    exit 1
}

$ghAuth = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Not authenticated with GitHub CLI. Run: gh auth login" -ForegroundColor Red
    exit 1
}
Write-Host "  GitHub CLI: authenticated" -ForegroundColor Green

# Check if repo is connected
$remoteUrl = git remote get-url origin 2>$null
if (-not $remoteUrl) {
    Write-Host "  ERROR: No git remote 'origin' found." -ForegroundColor Red
    exit 1
}
Write-Host "  Remote: $remoteUrl" -ForegroundColor Green

# Check Vercel connection
$vercelDir = Join-Path $repoRoot ".vercel"
if (Test-Path $vercelDir) {
    Write-Host "  Vercel: connected (.vercel/ found)" -ForegroundColor Green
} else {
    Write-Host "  Vercel: NOT connected — run 'vercel link' in the repo root" -ForegroundColor Yellow
}

# Step 2: Set GitHub secrets (Render only — Vercel auto-deploys on push)
if (-not $SkipSecrets) {
    Write-Host ""
    Write-Host "[2/5] Setting GitHub Actions secrets (Render only)..." -ForegroundColor Yellow
    Write-Host "  Note: Vercel auto-deploys on push — no secrets needed."
    Write-Host ""
    Write-Host "  Get these from Render dashboard:"
    Write-Host "    - API Key: https://dashboard.render.com/user/settings > API Keys"
    Write-Host "    - Service ID: Render dashboard > neurosim-api > Settings > Service ID"
    Write-Host ""

    $renderApiKey = Read-Host "  Render API Key"
    $renderServiceId = Read-Host "  Render Service ID"

    if ($DryRun) {
        Write-Host "  [DRY RUN] Would set secrets:" -ForegroundColor Gray
        Write-Host "    RENDER_API_KEY = $($renderApiKey.Substring(0,8))..."
        Write-Host "    RENDER_SERVICE_ID = $renderServiceId"
    } else {
        gh secret set RENDER_API_KEY --body $renderApiKey
        gh secret set RENDER_SERVICE_ID --body $renderServiceId
        Write-Host "  Secrets set successfully." -ForegroundColor Green
    }
}

# Step 3: Verify existing Render deploy
Write-Host ""
Write-Host "[3/5] Checking existing Render deployment..." -ForegroundColor Yellow

$healthUrl = "https://neurosim-nm22.onrender.com/health"
try {
    $response = Invoke-WebRequest -Uri $healthUrl -Method GET -TimeoutSec 10
    $body = $response.Content | ConvertFrom-Json
    if ($body.status -eq "healthy") {
        Write-Host "  Backend is healthy at $healthUrl" -ForegroundColor Green
        Write-Host "  Version: $($body.version), Whisper: $($body.whisper), Supabase: $($body.supabase)" -ForegroundColor Gray
    } else {
        Write-Host "  Backend responded but status is not healthy: $($body.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Backend unreachable at $healthUrl" -ForegroundColor Yellow
    Write-Host "  This is normal if Render hasn't deployed the latest code yet." -ForegroundColor Gray
}

# Step 4: Trigger deploy
if (-not $SkipDeploy) {
    Write-Host ""
    Write-Host "[4/5] Triggering Render deploy..." -ForegroundColor Yellow

    if ($DryRun) {
        Write-Host "  [DRY RUN] Would trigger deploy via Render API" -ForegroundColor Gray
    } else {
        if ($renderServiceId -and $renderApiKey) {
            try {
                Invoke-WebRequest -Uri "https://api.render.com/v1/services/$renderServiceId/deploys" -Method POST -Headers @{
                    "Authorization" = "Bearer $renderApiKey"
                    "Content-Type" = "application/json"
                } -TimeoutSec 30 | Out-Null
                Write-Host "  Deploy triggered! Watch at https://dashboard.render.com" -ForegroundColor Green
            } catch {
                Write-Host "  Deploy trigger failed: $_" -ForegroundColor Yellow
                Write-Host "  Pushing to master will trigger auto-deploy instead." -ForegroundColor Gray
            }
        } else {
            Write-Host "  No Render credentials. Push to master to trigger auto-deploy." -ForegroundColor Gray
        }
    }
}

# Step 5: Summary
Write-Host ""
Write-Host "[5/5] Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Set Supabase env vars in Render dashboard:"
Write-Host "   - SUPABASE_URL"
Write-Host "   - SUPABASE_SERVICE_KEY"
Write-Host "   - SUPABASE_JWT_SECRET"
Write-Host ""
Write-Host "2. Run database migrations (after Supabase is set):"
Write-Host "   cd backend"
Write-Host "   python migrate.py"
Write-Host ""
Write-Host "3. Verify deploys:"
Write-Host "   curl https://neurosim-nm22.onrender.com/health"
Write-Host "   curl https://neurosim-nm22.onrender.com/api/metrics"
Write-Host ""
Write-Host "4. Read the launch plan:"
Write-Host "   docs/launch-plan.md"
Write-Host ""
Write-Host "5. Read the full deploy guide:"
Write-Host "   docs/deploy-guide.md"
