# Deploy NeuroSim with original UI + email/password auth
Write-Host "Deploying original UI with email auth..."
cd "$env:TEMP\neurosim-clean"
vercel --prod --yes 2>&1
