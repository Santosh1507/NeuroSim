<template>
  <div class="neurosim-dashboard">
    <div class="page-header">
      <h1>A/B Test Results</h1>
      <p class="subtitle" v-if="experiment">Experiment: {{ experiment.id || experiment.experiment_id }}</p>
      <p v-if="loading" class="loading-text">Loading results...</p>
      <p v-else-if="processingMessage" class="loading-text">{{ processingMessage }}</p>
    </div>

    <div v-if="error" class="error-message">
      <span class="error-icon">✕</span>
      <span>{{ error }}</span>
    </div>

    <div v-if="experiment && comparison" class="results-container">
      <!-- Winner Banner -->
      <div class="winner-banner" :class="comparison.winner">
        <div class="winner-icon">
          <span v-if="comparison.winner === 'A'">🅰️</span>
          <span v-else-if="comparison.winner === 'B'">🅱️</span>
          <span v-else>🤝</span>
        </div>
        <div class="winner-text">
          <h2>
            <span v-if="comparison.winner === 'A'">Variant A Wins</span>
            <span v-else-if="comparison.winner === 'B'">Variant B Wins</span>
            <span v-else>It's a Tie</span>
          </h2>
          <p>{{ comparison.recommendation }}</p>
          <span class="confidence-badge" :class="comparison.confidence">
            {{ comparison.confidence }} confidence
          </span>
        </div>
      </div>

      <!-- Side-by-Side Comparison -->
      <div class="comparison-grid">
        <!-- Variant A -->
        <div class="variant-panel panel-a">
          <h3>Variant A</h3>

          <div class="metric-group">
            <h4>Neural ROI Scores</h4>
            <div class="roi-display">
              <div class="roi-item" v-for="(score, key) in variantA.roi_scores" :key="key">
                <span class="roi-label">{{ key }}</span>
                <div class="roi-bar"><div class="roi-fill" :style="{ width: (score * 100) + '%' }"></div></div>
                <span class="roi-value">{{ (score * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>

          <div class="metric-group">
            <h4>Simulation Results</h4>
            <div v-if="variantA.result" class="results-list">
              <div class="result-item">
                <span class="result-label">Final Sentiment</span>
                <span class="result-value">{{ variantA.result.final_sentiment }}%</span>
              </div>
              <div class="result-item">
                <span class="result-label">Viral Prediction</span>
                <span class="result-value">{{ variantA.result.viral_prediction }}</span>
              </div>
              <div class="result-item">
                <span class="result-label">Backlash Risk</span>
                <span class="result-value">{{ variantA.result.backlash_prediction }}</span>
              </div>
              <div class="result-item">
                <span class="result-label">Share Likelihood</span>
                <span class="result-value">{{ variantA.result.share_likelihood }}%</span>
              </div>
              <div class="result-item">
                <span class="result-label">Engagement Score</span>
                <span class="result-value">{{ variantA.result.engagement_score }}</span>
              </div>
            </div>
          </div>

          <div class="metric-group">
            <h4>Stage-Gate</h4>
            <div class="gate-status" :class="variantA.stage_gate.severity">
              <span class="gate-icon">{{ variantA.stage_gate.passed ? '✓' : '⚠' }}</span>
              <span>Gate Score: {{ (variantA.stage_gate.gate_score * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>

        <!-- Variant B -->
        <div class="variant-panel panel-b">
          <h3>Variant B</h3>

          <div class="metric-group">
            <h4>Neural ROI Scores</h4>
            <div class="roi-display">
              <div class="roi-item" v-for="(score, key) in variantB.roi_scores" :key="key">
                <span class="roi-label">{{ key }}</span>
                <div class="roi-bar"><div class="roi-fill" :style="{ width: (score * 100) + '%' }"></div></div>
                <span class="roi-value">{{ (score * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>

          <div class="metric-group">
            <h4>Simulation Results</h4>
            <div v-if="variantB.result" class="results-list">
              <div class="result-item">
                <span class="result-label">Final Sentiment</span>
                <span class="result-value">{{ variantB.result.final_sentiment }}%</span>
              </div>
              <div class="result-item">
                <span class="result-label">Viral Prediction</span>
                <span class="result-value">{{ variantB.result.viral_prediction }}</span>
              </div>
              <div class="result-item">
                <span class="result-label">Backlash Risk</span>
                <span class="result-value">{{ variantB.result.backlash_prediction }}</span>
              </div>
              <div class="result-item">
                <span class="result-label">Share Likelihood</span>
                <span class="result-value">{{ variantB.result.share_likelihood }}%</span>
              </div>
              <div class="result-item">
                <span class="result-label">Engagement Score</span>
                <span class="result-value">{{ variantB.result.engagement_score }}</span>
              </div>
            </div>
          </div>

          <div class="metric-group">
            <h4>Stage-Gate</h4>
            <div class="gate-status" :class="variantB.stage_gate.severity">
              <span class="gate-icon">{{ variantB.stage_gate.passed ? '✓' : '⚠' }}</span>
              <span>Gate Score: {{ (variantB.stage_gate.gate_score * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Sentiment Timeline Chart -->
      <div class="chart-section">
        <h3>Sentiment Over Time</h3>
        <div class="chart-container">
          <div v-if="variantA.result && variantB.result" class="timeline-chart">
            <div class="timeline-row" v-for="(point, idx) in variantA.result.history" :key="idx">
              <span class="round-label">Round {{ point.round }}</span>
              <div class="sentiment-bar">
                <div class="sentiment-fill sentiment-a" :style="{ width: (point.avg_sentiment * 100) + '%' }"></div>
              </div>
              <span class="sentiment-value">{{ (point.avg_sentiment * 100).toFixed(0) }}%</span>
              <div class="sentiment-bar">
                <div class="sentiment-fill sentiment-b" :style="{ width: (variantB.result.history[idx]?.avg_sentiment * 100 || 0) + '%' }"></div>
              </div>
              <span class="sentiment-value">{{ (variantB.result.history[idx]?.avg_sentiment * 100 || 0).toFixed(0) }}%</span>
            </div>
            <div class="chart-legend">
              <span class="legend-item"><span class="legend-dot dot-a"></span> Variant A</span>
              <span class="legend-item"><span class="legend-dot dot-b"></span> Variant B</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="actions">
        <button class="btn btn-primary" @click="$router.push('/neurosim')">New A/B Test</button>
        <button class="btn btn-secondary" @click="$router.push('/')">Back to Home</button>
      </div>
    </div>
  </div>
</template>

<script>
import { getABTestResults } from '../api/neurosim'

export default {
  name: 'NeuroSimDashboard',
  props: {
    experimentId: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      experiment: null,
      comparison: null,
      variantA: null,
      variantB: null,
      loading: true,
      error: null,
      pollInterval: null,
      processingMessage: '',
    }
  },
  mounted() {
    this.fetchResults()
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  },
  methods: {
    async fetchResults() {
      const initialLoad = !this.experiment
      this.loading = initialLoad
      this.error = null

      try {
        const result = await getABTestResults(this.experimentId)

        if (result.status === 'completed') {
          this.experiment = result
          this.comparison = result.comparison
          this.variantA = result.variant_a
          this.variantB = result.variant_b
          this.processingMessage = ''
          this.stopPolling()
        } else if (['processing', 'created', 'running'].includes(result.status)) {
          this.experiment = {
            id: this.experimentId,
            experiment_id: this.experimentId,
            status: result.status,
          }
          this.processingMessage = result.message || 'Experiment is still running'
          this.ensurePolling()
        } else if (result.status === 'failed') {
          this.processingMessage = ''
          this.stopPolling()
          this.error = result.message || 'Experiment failed'
        } else {
          this.error = result.message || 'Unknown status'
        }
      } catch (err) {
        this.error = `Failed to load results: ${err.message}`
      } finally {
        this.loading = false
      }
    },

    ensurePolling() {
      if (this.pollInterval) return
      this.pollInterval = setInterval(() => {
        this.fetchResults()
      }, 3000)
    },

    stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
        this.pollInterval = null
      }
    },
  },
}
</script>

<style scoped>
.neurosim-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.page-header {
  text-align: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  font-size: 0.9rem;
}

.loading-text {
  color: #1976d2;
  font-style: italic;
}

.error-message {
  padding: 0.75rem;
  background: #ffebee;
  color: #d32f2f;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.results-container {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.winner-banner {
  padding: 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.winner-banner.A {
  background: linear-gradient(135deg, #e3f2fd, #bbdefb);
  border: 2px solid #1976d2;
}

.winner-banner.B {
  background: linear-gradient(135deg, #f3e5f5, #e1bee7);
  border: 2px solid #7b1fa2;
}

.winner-banner.tie {
  background: #f5f5f5;
  border: 2px solid #9e9e9e;
}

.winner-icon {
  font-size: 3rem;
}

.winner-text h2 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.winner-text p {
  color: #666;
  margin-bottom: 0.5rem;
}

.confidence-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.confidence-badge.high {
  background: #e8f5e9;
  color: #388e3c;
}

.confidence-badge.moderate {
  background: #fff3e0;
  color: #f57c00;
}

.confidence-badge.low {
  background: #f5f5f5;
  color: #9e9e9e;
}

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.variant-panel {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 1.5rem;
}

.variant-panel h3 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e0e0e0;
}

.panel-a h3 {
  color: #1976d2;
  border-bottom-color: #1976d2;
}

.panel-b h3 {
  color: #7b1fa2;
  border-bottom-color: #7b1fa2;
}

.metric-group {
  margin-bottom: 1.5rem;
}

.metric-group h4 {
  font-size: 0.95rem;
  color: #666;
  margin-bottom: 0.75rem;
}

.roi-display {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.roi-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.roi-label {
  width: 80px;
  font-size: 0.85rem;
  color: #666;
}

.roi-bar {
  flex: 1;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.roi-fill {
  height: 100%;
  background: linear-gradient(90deg, #1976d2, #7b1fa2);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.roi-value {
  width: 40px;
  text-align: right;
  font-size: 0.9rem;
  font-weight: 600;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.result-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f0f0f0;
}

.result-label {
  color: #666;
  font-size: 0.9rem;
}

.result-value {
  font-weight: 500;
  font-size: 0.9rem;
}

.gate-status {
  padding: 0.75rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.gate-status.pass {
  background: #e8f5e9;
  color: #388e3c;
}

.gate-status.pass_weak {
  background: #fff3e0;
  color: #f57c00;
}

.gate-status.fail {
  background: #ffebee;
  color: #d32f2f;
}

.chart-section {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 1.5rem;
}

.chart-section h3 {
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.timeline-chart {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.timeline-row {
  display: grid;
  grid-template-columns: 80px 1fr 50px 1fr 50px;
  align-items: center;
  gap: 0.75rem;
}

.round-label {
  font-size: 0.85rem;
  color: #666;
}

.sentiment-bar {
  height: 20px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.sentiment-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.sentiment-a {
  background: #1976d2;
}

.sentiment-b {
  background: #7b1fa2;
}

.sentiment-value {
  font-size: 0.85rem;
  font-weight: 500;
  text-align: right;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot-a {
  background: #1976d2;
}

.dot-b {
  background: #7b1fa2;
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #1976d2;
  color: white;
}

.btn-primary:hover {
  background: #1565c0;
}

.btn-secondary {
  background: #e0e0e0;
  color: #333;
}

.btn-secondary:hover {
  background: #d0d0d0;
}

@media (max-width: 768px) {
  .comparison-grid {
    grid-template-columns: 1fr;
  }

  .timeline-row {
    grid-template-columns: 60px 1fr 40px;
  }

  .timeline-row > :nth-child(4),
  .timeline-row > :nth-child(5) {
    display: none;
  }
}
</style>
