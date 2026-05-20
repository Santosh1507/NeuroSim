interface ErrorReport {
  message: string;
  stack?: string;
  url: string;
  timestamp: string;
  userAgent: string;
}

export function reportError(error: Error | string, context?: Record<string, unknown>) {
  const report: ErrorReport = {
    message: typeof error === "string" ? error : error.message,
    stack: typeof error === "object" ? error.stack : undefined,
    url: window.location.href,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    ...context,
  };

  if (process.env.NODE_ENV === "development") {
    console.error("[NeuroSim Error]", report);
  }

  if (process.env.NODE_ENV === "production") {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/error-report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(report),
    }).catch(() => {});
  }
}

if (typeof window !== "undefined") {
  window.addEventListener("error", (event) => {
    reportError(event.error);
  });

  window.addEventListener("unhandledrejection", (event) => {
    reportError(event.reason);
  });
}
