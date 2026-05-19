# Phase 2: Pre-Revenue Hardening — Detailed Tasks

## T7: Onboarding Flow

### Step 1: Create `frontend/src/app/components/OnboardingTour.tsx`

```tsx
"use client";
import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ChevronRight, Upload, BarChart3, Share2, Download } from "lucide-react";

interface OnboardingTourProps { onComplete: () => void; }

const steps = [
  { title: "Welcome to NeuroSim", description: "Predict how your video content will perform before you publish.", icon: BarChart3 },
  { title: "Upload Your Video", description: "Drag and drop or click to upload. MP4, MOV, AVI, WebM. Free: 10 analyses/month.", icon: Upload },
  { title: "Neural Analysis", description: "Transcribed and analyzed using brain-inspired ROI scoring. Hook score, viral potential, risk assessment.", icon: BarChart3 },
  { title: "Share & Export", description: "Share results with a link, export as PDF, or embed. Links expire after 7 days.", icon: Share2 },
  { title: "You're Ready!", description: "Upload your first video. Analysis takes 30-60 seconds.", icon: Download },
];

export default function OnboardingTour({ onComplete }: OnboardingTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("neurosim_onboarding_seen")) setIsOpen(true);
  }, []);

  const handleComplete = () => {
    localStorage.setItem("neurosim_onboarding_seen", "true");
    setIsOpen(false);
    onComplete();
  };

  const StepIcon = steps[currentStep].icon;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-void/80 backdrop-blur-sm"
          onClick={handleComplete}>
          <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
            className="glass-panel-elevated max-w-lg w-full mx-4 p-8 relative"
            onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="onboarding-title">
            <button onClick={handleComplete} className="absolute top-4 right-4 p-2 rounded-lg hover:bg-surface/50" aria-label="Close onboarding">
              <X className="w-5 h-5 text-text-secondary" />
            </button>
            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-neural/10 flex items-center justify-center">
                <StepIcon className="w-6 h-6 text-neural" />
              </div>
              <h2 id="onboarding-title" className="text-xl font-display font-semibold text-text-primary">{steps[currentStep].title}</h2>
            </div>
            <p className="text-text-secondary mb-8 leading-relaxed">{steps[currentStep].description}</p>
            <div className="flex gap-2 mb-6">
              {steps.map((_, i) => (
                <div key={i} className={`h-1 flex-1 rounded-full transition-colors ${i <= currentStep ? "bg-neural" : "bg-surface"}`} />
              ))}
            </div>
            <div className="flex justify-between items-center">
              <button onClick={() => setCurrentStep(Math.max(0, currentStep - 1))} className="btn-ghost text-sm" disabled={currentStep === 0}>Back</button>
              <button onClick={currentStep < steps.length - 1 ? () => setCurrentStep(currentStep + 1) : handleComplete} className="btn-neural text-sm">
                {currentStep < steps.length - 1 ? <span className="flex items-center gap-1">Next <ChevronRight className="w-4 h-4" /></span> : "Get Started"}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### Step 2: Integrate into dashboard

In `frontend/src/app/dashboard/page.tsx`:
```tsx
import OnboardingTour from "../components/OnboardingTour";
// Add: <OnboardingTour onComplete={() => {}} />
```

### Step 3: Commit
```bash
git add frontend/src/app/components/OnboardingTour.tsx frontend/src/app/dashboard/page.tsx
git commit -m "feat: add onboarding tour for first-time users"
```

---

## T8: Guest Session Recovery

### Step 1: Add recovery to auth-context.tsx

In `frontend/src/lib/auth-context.tsx`, add:
```tsx
const recoverGuestSession = async () => {
  const guestId = localStorage.getItem("neurosim_guest_id");
  if (!guestId || !user) return;
  try {
    const resp = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/merge`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ guest_session_id: guestId, user_id: user.id }),
    });
    if (resp.ok) { localStorage.removeItem("neurosim_guest_id"); window.location.reload(); }
  } catch (e) { console.error("Guest recovery failed:", e); }
};
```

### Step 2: Show recovery banner in dashboard

```tsx
{isSignedIn && localStorage.getItem("neurosim_guest_id") && (
  <div className="glass-panel p-4 mb-4 border border-neural/30">
    <p className="text-sm text-text-primary">
      You have videos from a guest session.{" "}
      <button onClick={recoverGuestSession} className="text-neural underline">Merge them into your account</button>
    </p>
  </div>
)}
```

### Step 3: Commit
```bash
git add frontend/src/lib/auth-context.tsx frontend/src/app/dashboard/page.tsx
git commit -m "feat: add guest session recovery with merge banner"
```

---

## T9: Rate Limiting (Production-Ready)

### Step 1: Update `backend/rate_limiter.py`

Add `reset()` method and `check_api_limit()` dependency:
```python
def reset(self, ip: str) -> None:
    self._requests[ip] = []

api_limiter = RateLimiter(max_requests=60, window_seconds=60)

def check_api_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    if not api_limiter.is_allowed(ip):
        raise HTTPException(status_code=429, detail={"error": "Rate limit exceeded", "message": "Too many requests."})
```

### Step 2: Apply to endpoints in main.py

Add `Depends(check_api_limit)` to: `/analyses/{id}`, `/videos`, `/api/analytics`, `/api/premium/status`

### Step 3: Create `backend/test_rate_limiting_extended.py`

```python
import pytest
from rate_limiter import RateLimiter
import time

class TestRateLimiterExtended:
    def test_reset_clears(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.is_allowed("1.2.3.4")
        limiter.reset("1.2.3.4")
        assert limiter.is_allowed("1.2.3.4")

    def test_different_ips_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        assert limiter.is_allowed("1.1.1.1")
        assert not limiter.is_allowed("1.1.1.1")
        assert limiter.is_allowed("2.2.2.2")

    def test_remaining_count(self):
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        limiter.is_allowed("1.2.3.4")
        limiter.is_allowed("1.2.3.4")
        assert limiter.remaining("1.2.3.4") == 3

    def test_window_expiry(self, monkeypatch):
        limiter = RateLimiter(max_requests=1, window_seconds=1)
        assert limiter.is_allowed("1.2.3.4")
        assert not limiter.is_allowed("1.2.3.4")
        monkeypatch.setattr(time, "time", lambda: time.time() + 2)
        assert limiter.is_allowed("1.2.3.4")
```

### Step 4: Run tests
```bash
cd backend && python -m pytest test_rate_limiting_extended.py -v
```

### Step 5: Commit
```bash
git add backend/rate_limiter.py backend/main.py backend/test_rate_limiting_extended.py
git commit -m "feat: extend rate limiting with reset and API-level limits"
```

---

## T10: Monitoring & Observability

### Step 1: Create `backend/monitoring.py`

```python
import time
from typing import Dict, List

class MetricsCollector:
    def __init__(self):
        self._request_counts: Dict[str, int] = {}
        self._error_counts: Dict[str, int] = {}
        self._response_times: Dict[str, List[float]] = {}
        self._start_time = time.time()

    def record_request(self, method: str, path: str, status: int, duration_ms: float):
        key = f"{method} {path}"
        self._request_counts[key] = self._request_counts.get(key, 0) + 1
        if status >= 500:
            self._error_counts[key] = self._error_counts.get(key, 0) + 1
        if key not in self._response_times:
            self._response_times[key] = []
        self._response_times[key].append(duration_ms)
        if len(self._response_times[key]) > 100:
            self._response_times[key] = self._response_times[key][-100:]

    def get_summary(self) -> dict:
        uptime = time.time() - self._start_time
        total_requests = sum(self._request_counts.values())
        total_errors = sum(self._error_counts.values())
        avg_times = {k: round(sum(v)/len(v), 2) for k, v in self._response_times.items() if v}
        return {
            "uptime_seconds": round(uptime, 0), "total_requests": total_requests,
            "total_errors": total_errors, "error_rate": round(total_errors / max(total_requests, 1), 4),
            "avg_response_times_ms": avg_times,
            "top_endpoints": sorted(self._request_counts.items(), key=lambda x: x[1], reverse=True)[:10],
        }

metrics = MetricsCollector()
```

### Step 2: Add middleware to main.py

```python
from monitoring import metrics

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    metrics.record_request(method=request.method, path=request.url.path, status=response.status_code, duration_ms=duration_ms)
    return response

@app.get("/api/metrics")
async def get_metrics():
    return metrics.get_summary()
```

### Step 3: Create `frontend/src/lib/error-reporter.ts`

```typescript
interface ErrorReport {
  message: string; stack?: string; url: string; timestamp: string; userAgent: string;
}

export function reportError(error: Error | string, context?: Record<string, unknown>) {
  const report: ErrorReport = {
    message: typeof error === "string" ? error : error.message,
    stack: typeof error === "object" ? error.stack : undefined,
    url: window.location.href, timestamp: new Date().toISOString(), userAgent: navigator.userAgent, ...context,
  };
  if (process.env.NODE_ENV === "development") console.error("[NeuroSim Error]", report);
  if (process.env.NODE_ENV === "production") {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/error-report`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(report),
    }).catch(() => {});
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("error", (e) => reportError(e.error));
  window.addEventListener("unhandledrejection", (e) => reportError(e.reason));
}
```

### Step 4: Commit
```bash
git add backend/monitoring.py backend/main.py frontend/src/lib/error-reporter.ts
git commit -m "feat: add monitoring middleware and frontend error reporter"
```

---

## T11: PDF Report E2E Verification

### Step 1: Add to `backend/test_api.py`

```python
def test_pdf_report_download():
    from main import app
    client = TestClient(app)
    # Upload
    with open("test_video.mp4", "rb") as f:
        resp = client.post("/upload?user_id=pdf_test", files={"file": ("test.mp4", f, "video/mp4")})
    assert resp.status_code == 200
    video_id = resp.json()["video_id"]
    _wait_for_analysis(client, video_id)
    # Download PDF
    pdf_resp = client.get(f"/reports/{video_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content[:4] == b"%PDF"
```

### Step 2: Run test
```bash
cd backend && python -m pytest test_api.py::test_pdf_report_download -v
```

### Step 3: Commit
```bash
git add backend/test_api.py
git commit -m "test: add PDF report e2e download verification"
```

---

## T12: Full Test Suite Verification

### Step 1: Backend
```bash
cd backend && python -m pytest -v --tb=short
```
Expected: 100+ PASS

### Step 2: Frontend
```bash
cd frontend && npx vitest run
```
Expected: 16 PASS

### Step 3: Commit
```bash
git add . && git commit -m "v2.6: pre-revenue hardening complete"
```
