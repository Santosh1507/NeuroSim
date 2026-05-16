<template>
  <div class="crisis-progress">
    <div class="progress-container">
      <h2>Simulating Public Reactions</h2>

      <!-- Queued state -->
      <div v-if="status === 'queued'" class="status-queued">
        <div class="spinner"></div>
        <p class="status-text">Your simulation is in the queue</p>
        <p v-if="queuePosition >= 0" class="queue-info">
          Position: {{ queuePosition + 1 }} | Estimated wait: {{ estimatedWait }}s
        </p>
      </div>

      <!-- Running state with progress -->
      <div v-else-if="status === 'running'" class="status-running">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <p class="stage-label">{{ stageLabel }}</p>
        <p class="progress-detail">{{ reactionsCount }} / {{ totalPersonas }} reactions generated</p>
      </div>

      <!-- Failed state -->
      <div v-else-if="status === 'failed'" class="status-failed">
        <div class="error-icon">!</div>
        <p class="error-message">{{ errorMessage || 'Simulation failed' }}</p>
        <button class="btn-retry" @click="retry">Retry</button>
      </div>

      <!-- Completed - redirect handled by watcher -->
    </div>
  </div>
</template>

<script>
import api from '../api'

const STAGE_LABELS = {
  'queued': 'Waiting in queue...',
  'initializing': 'Initializing simulation...',
  'generating_personas': 'Generating 50 diverse personas...',
  'simulating_reactions': 'Simulating public reactions...',
  'analyzing_blind_spots': 'Analyzing blind spots...',
  'generating_report': 'Generating risk report...',
  'completed': 'Complete!',
  'failed': 'Simulation failed',
}

export default {
  name: 'CrisisProgress',
  props: {
    simulationId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      status: 'queued',
      progress: 0,
      stage: 'queued',
      reactionsCount: 0,
      totalPersonas: 50,
      queuePosition: -1,
      estimatedWait: 0,
      errorMessage: '',
      pollInterval: null,
      pollCount: 0,
      maxPolls: 120, // 10 minutes at 5s intervals
    }
  },
  computed: {
    progressPercent() {
      return Math.round(this.progress * 100)
    },
    stageLabel() {
      return STAGE_LABELS[this.stage] || this.stage
    }
  },
  watch: {
    status(newStatus) {
      if (newStatus === 'completed' || newStatus === 'partial') {
        this.$router.push({
          name: 'CrisisReport',
          params: { simulationId: this.simulationId }
        })
      }
    }
  },
  mounted() {
    this.startPolling()
  },
  beforeUnmount() {
    this.stopPolling()
  },
  methods: {
    async pollStatus() {
      try {
        const response = await api.get(`/simulations/${this.simulationId}`)
        const data = response.data

        this.status = data.status
        this.progress = data.progress || 0
        this.stage = data.stage || this.stage
        this.reactionsCount = data.reactions_count || 0
        this.totalPersonas = data.total_personas || 50
        this.queuePosition = data.queue_position ?? -1
        this.estimatedWait = data.estimated_wait_seconds || 0
        this.errorMessage = data.error || ''

        if (data.status === 'failed') {
          this.stopPolling()
        }
      } catch (error) {
        if (error.response?.status === 404) {
          this.errorMessage = 'Simulation not found'
          this.stopPolling()
        } else if (this.pollCount < 10) {
          // Retry on transient errors
          console.warn('Poll error, will retry:', error.message)
        } else {
          this.errorMessage = 'Connection error. Please check your network.'
          this.stopPolling()
        }
      }

      this.pollCount++
      if (this.pollCount >= this.maxPolls) {
        this.errorMessage = 'Simulation timed out. Please try again.'
        this.stopPolling()
      }
    },
    startPolling() {
      this.pollStatus() // Immediate first poll
      this.pollInterval = setInterval(this.pollStatus, 5000)
    },
    stopPolling() {
      if (this.pollInterval) {
        clearInterval(this.pollInterval)
        this.pollInterval = null
      }
    },
    retry() {
      this.status = 'queued'
      this.progress = 0
      this.stage = 'queued'
      this.errorMessage = ''
      this.pollCount = 0
      this.startPolling()
    }
  }
}
</script>

<style scoped>
.crisis-progress {
  max-width: 600px;
  margin: 0 auto;
  padding: 3rem 1rem;
  text-align: center;
}

.progress-container h2 {
  margin-bottom: 2rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e9ecef;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.status-text {
  font-size: 1.1rem;
  color: #666;
}

.queue-info {
  color: #888;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 1rem;
}

.progress-fill {
  height: 100%;
  background: #007bff;
  transition: width 0.3s ease;
}

.stage-label {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.progress-detail {
  color: #666;
  font-size: 0.9rem;
}

.status-failed {
  padding: 2rem;
}

.error-icon {
  width: 60px;
  height: 60px;
  background: #dc3545;
  color: white;
  font-size: 2rem;
  font-weight: bold;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}

.error-message {
  color: #dc3545;
  margin-bottom: 1.5rem;
}

.btn-retry {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
}

.btn-retry:hover {
  background: #0056b3;
}
</style>
