<template>
  <div class="crisis-report">
    <div v-if="loading" class="loading">Loading report...</div>

    <div v-else-if="report" class="report-container">
      <!-- Risk verdict above the fold -->
      <header class="report-header">
        <h1>Simulation Report</h1>
        <div class="risk-verdict" :class="riskClass">
          <span class="risk-score">{{ report.risk_score }}</span>
          <span class="risk-label">{{ report.risk_label.toUpperCase() }} RISK</span>
        </div>
        <p v-if="report.partial" class="partial-banner">
          Warning: Only {{ report.total_reactions }} of {{ report.total_personas }} reactions completed. Results may be incomplete.
        </p>
      </header>

      <!-- Sentiment breakdown -->
      <section class="sentiment-section">
        <h2>Public Sentiment</h2>
        <div class="sentiment-bar">
          <div class="sentiment-positive" :style="{ width: report.sentiment_distribution.positive * 100 + '%' }">
            {{ Math.round(report.sentiment_distribution.positive * 100) }}%
          </div>
          <div class="sentiment-neutral" :style="{ width: report.sentiment_distribution.neutral * 100 + '%' }">
            {{ Math.round(report.sentiment_distribution.neutral * 100) }}%
          </div>
          <div class="sentiment-negative" :style="{ width: report.sentiment_distribution.negative * 100 + '%' }">
            {{ Math.round(report.sentiment_distribution.negative * 100) }}%
          </div>
        </div>
        <div class="sentiment-legend">
          <span class="legend-positive">Positive</span>
          <span class="legend-neutral">Neutral</span>
          <span class="legend-negative">Negative</span>
        </div>
      </section>

      <!-- Blind spots -->
      <section v-if="report.blind_spots && report.blind_spots.length > 0" class="blind-spots-section">
        <h2>Blind Spots Detected</h2>
        <div class="blind-spots-list">
          <div
            v-for="(spot, index) in report.blind_spots"
            :key="index"
            class="blind-spot-card"
            :class="spot.severity"
          >
            <div class="spot-header">
              <span class="spot-severity">{{ spot.severity }}</span>
              <span class="spot-topic">{{ spot.topic }}</span>
            </div>
            <p class="spot-explanation">{{ spot.explanation }}</p>
            <div class="spot-meta">
              <span>{{ spot.persona_count }} personas</span>
              <span>{{ Math.round(spot.mention_ratio * 100) }}% mention rate</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Top reactions -->
      <section class="reactions-section">
        <h2>Sample Reactions</h2>
        <div class="reactions-list">
          <div
            v-for="(reaction, index) in report.top_reactions"
            :key="index"
            class="reaction-card"
            :class="reaction.sentiment"
          >
            <div class="reaction-header">
              <span class="reaction-persona">{{ reaction.persona }}</span>
              <span class="reaction-sentiment">{{ reaction.sentiment }}</span>
            </div>
            <p class="reaction-text">{{ reaction.text }}</p>
          </div>
        </div>
      </section>

      <!-- Post-report actions -->
      <section class="actions-section">
        <button class="btn-action" @click="revise">Revise & Resimulate</button>
        <button class="btn-action secondary" @click="exportPDF">Export PDF</button>
        <button class="btn-action secondary" @click="saveSimulation">Save to History</button>
      </section>
    </div>

    <div v-else class="error">
      <p>Failed to load report</p>
      <button @click="$router.push({ name: 'CrisisUpload' })">Back to Upload</button>
    </div>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'CrisisReport',
  props: {
    simulationId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      report: null,
      loading: true,
    }
  },
  computed: {
    riskClass() {
      if (!this.report) return ''
      const label = this.report.risk_label
      return `risk-${label}`
    }
  },
  async mounted() {
    await this.loadReport()
  },
  methods: {
    async loadReport() {
      try {
        const response = await api.get(`/simulations/${this.simulationId}`)
        const data = response.data

        if (data.status === 'completed' || data.status === 'partial') {
          this.report = data.result?.report || null
        } else {
          this.report = null
        }
      } catch (error) {
        console.error('Failed to load report:', error)
        this.report = null
      } finally {
        this.loading = false
      }
    },
    revise() {
      this.$router.push({ name: 'CrisisUpload' })
    },
    exportPDF() {
      window.print()
    },
    saveSimulation() {
      // TODO: Implement save to history
      alert('Simulation saved to history')
    }
  }
}
</script>

<style scoped>
.crisis-report {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.loading, .error {
  text-align: center;
  padding: 3rem;
}

.report-header {
  text-align: center;
  margin-bottom: 2rem;
}

.risk-verdict {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem 3rem;
  border-radius: 8px;
  margin: 1rem 0;
}

.risk-low {
  background: #d4edda;
  color: #155724;
}

.risk-medium {
  background: #fff3cd;
  color: #856404;
}

.risk-high {
  background: #f8d7da;
  color: #721c24;
}

.risk-critical {
  background: #dc3545;
  color: white;
}

.risk-score {
  font-size: 3rem;
  font-weight: bold;
}

.risk-label {
  font-size: 1.2rem;
  font-weight: 600;
  letter-spacing: 2px;
}

.partial-banner {
  background: #fff3cd;
  color: #856404;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.sentiment-section {
  margin-bottom: 2rem;
}

.sentiment-bar {
  display: flex;
  height: 40px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.sentiment-positive {
  background: #28a745;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
}

.sentiment-neutral {
  background: #ffc107;
  color: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
}

.sentiment-negative {
  background: #dc3545;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
}

.sentiment-legend {
  display: flex;
  justify-content: center;
  gap: 2rem;
  font-size: 0.9rem;
}

.legend-positive { color: #28a745; }
.legend-neutral { color: #ffc107; }
.legend-negative { color: #dc3545; }

.blind-spots-section {
  margin-bottom: 2rem;
}

.blind-spots-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.blind-spot-card {
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid;
}

.blind-spot-card.critical {
  background: #f8d7da;
  border-color: #dc3545;
}

.blind-spot-card.high {
  background: #fff3cd;
  border-color: #ffc107;
}

.blind-spot-card.medium {
  background: #e2e3e5;
  border-color: #6c757d;
}

.spot-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.spot-severity {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  background: rgba(0,0,0,0.1);
}

.spot-topic {
  font-weight: 600;
  font-size: 1.1rem;
}

.spot-explanation {
  margin: 0 0 0.5rem;
  color: #555;
}

.spot-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #888;
}

.reactions-section {
  margin-bottom: 2rem;
}

.reactions-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.reaction-card {
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid;
}

.reaction-card.positive {
  background: #d4edda;
  border-color: #28a745;
}

.reaction-card.neutral {
  background: #e2e3e5;
  border-color: #6c757d;
}

.reaction-card.negative {
  background: #f8d7da;
  border-color: #dc3545;
}

.reaction-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.reaction-persona {
  font-weight: 600;
  font-size: 0.9rem;
}

.reaction-sentiment {
  font-size: 0.8rem;
  text-transform: uppercase;
  font-weight: 600;
}

.reaction-text {
  margin: 0;
  font-style: italic;
  color: #333;
}

.actions-section {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
}

.btn-action {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  font-weight: 600;
}

.btn-action:hover {
  background: #0056b3;
}

.btn-action.secondary {
  background: #6c757d;
}

.btn-action.secondary:hover {
  background: #545b62;
}
</style>
