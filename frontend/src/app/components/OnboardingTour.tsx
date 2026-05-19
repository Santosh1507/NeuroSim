"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ChevronRight, Upload, BarChart3, Share2, Download } from "lucide-react";

interface OnboardingTourProps {
  onComplete: () => void;
}

const steps = [
  {
    title: "Welcome to NeuroSim",
    description: "Predict how your video content will perform before you publish. Let's walk through the key features.",
    icon: BarChart3,
  },
  {
    title: "Upload Your Video",
    description: "Drag and drop or click to upload. We support MP4, MOV, AVI, and WebM. Free tier: 10 analyses/month.",
    icon: Upload,
  },
  {
    title: "Neural Analysis",
    description: "Your video is transcribed and analyzed using brain-inspired ROI scoring. Results include hook score, viral potential, and risk assessment.",
    icon: BarChart3,
  },
  {
    title: "Share & Export",
    description: "Share results with a link, export as PDF, or embed on your site. Links expire after 7 days.",
    icon: Share2,
  },
  {
    title: "You're Ready!",
    description: "Upload your first video to get started. The analysis takes 30-60 seconds depending on video length.",
    icon: Download,
  },
];

export default function OnboardingTour({ onComplete }: OnboardingTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const seen = localStorage.getItem("neurosim_onboarding_seen");
    if (!seen) {
      setIsOpen(true);
    }
  }, []);

  const handleComplete = () => {
    localStorage.setItem("neurosim_onboarding_seen", "true");
    setIsOpen(false);
    onComplete();
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const StepIcon = steps[currentStep].icon;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-void/80 backdrop-blur-sm"
          onClick={handleComplete}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
            className="glass-panel-elevated max-w-lg w-full mx-4 p-8 relative"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="onboarding-title"
          >
            <button
              onClick={handleComplete}
              className="absolute top-4 right-4 p-2 rounded-lg hover:bg-surface/50 transition-colors"
              aria-label="Close onboarding"
            >
              <X className="w-5 h-5 text-text-secondary" />
            </button>

            <div className="flex items-center gap-4 mb-6">
              <div className="w-12 h-12 rounded-xl bg-neural/10 flex items-center justify-center">
                <StepIcon className="w-6 h-6 text-neural" />
              </div>
              <h2 id="onboarding-title" className="text-xl font-display font-semibold text-text-primary">
                {steps[currentStep].title}
              </h2>
            </div>

            <p className="text-text-secondary mb-8 leading-relaxed">
              {steps[currentStep].description}
            </p>

            {/* Progress dots */}
            <div className="flex gap-2 mb-6">
              {steps.map((_, i) => (
                <div
                  key={i}
                  className={`h-1 flex-1 rounded-full transition-colors ${
                    i <= currentStep ? "bg-neural" : "bg-surface"
                  }`}
                />
              ))}
            </div>

            <div className="flex justify-between items-center">
              <button
                onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                className="btn-ghost text-sm"
                disabled={currentStep === 0}
              >
                Back
              </button>
              <button onClick={handleNext} className="btn-neural text-sm">
                {currentStep < steps.length - 1 ? (
                  <span className="flex items-center gap-1">
                    Next <ChevronRight className="w-4 h-4" />
                  </span>
                ) : (
                  "Get Started"
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
