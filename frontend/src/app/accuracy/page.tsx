'use client'

import { ValidationStudyPanel } from '../components/ValidationStudyPanel'
import { fadeIn } from '../../lib/easing'
import { motion } from 'framer-motion'
import { Shield, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function AccuracyPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 py-12">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs text-text-tertiary hover:text-white transition-colors mb-8"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to home
        </Link>

        <motion.div className="mb-10" {...fadeIn}>
          <div className="flex items-center gap-3 mb-3">
            <Shield className="w-6 h-6 text-neural" />
            <h1 className="text-2xl font-bold text-white">Prediction Accuracy</h1>
          </div>
          <p className="text-sm text-text-tertiary max-w-2xl leading-relaxed">
            Every analysis on MiroFish includes predicted scores — hook strength,
            viral potential, success probability. This page tracks how well those
            predictions match real-world outcomes when users submit their actual
            video performance data. We&apos;re building toward statistical significance
            (20+ entries). All data is anonymized and aggregated.
          </p>
        </motion.div>

        <motion.div {...fadeIn}>
          <ValidationStudyPanel />
        </motion.div>

        <div className="mt-12 p-5 glass-panel border border-neural/10">
          <h2 className="text-sm font-semibold text-white mb-2">Why This Matters</h2>
          <ul className="space-y-2 text-xs text-text-tertiary leading-relaxed">
            <li className="flex items-start gap-2">
              <span className="text-neural mt-0.5">→</span>
              <span><strong className="text-white/80">Transparency:</strong> We publish our prediction accuracy publicly — no black box.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-neural mt-0.5">→</span>
              <span><strong className="text-white/80">Continuous improvement:</strong> Correlations and accuracy scores help us tune our models.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-neural mt-0.5">→</span>
              <span><strong className="text-white/80">Community-driven:</strong> More validation entries = better predictions for everyone.</span>
            </li>
          </ul>
          <p className="text-xs text-text-tertiary mt-4 p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]">
            Have an analysis result? Check the &ldquo;Your Accuracy&rdquo; section on your video results page
            to submit your actual views and engagement.
          </p>
        </div>
      </div>
    </div>
  )
}
