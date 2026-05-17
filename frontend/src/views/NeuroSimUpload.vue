<template>
  <div class="neurosim-upload">
    <div class="page-header">
      <h1>NeuroSim A/B Test</h1>
      <p class="subtitle">Upload two content variants to predict which will perform better</p>
    </div>

    <!-- Variant A Upload -->
    <div class="variant-card">
      <div class="variant-header">
        <span class="variant-badge badge-a">Variant A</span>
        <span v-if="statusA" class="status-badge" :class="statusA">{{ statusA }}</span>
      </div>

      <div class="upload-zone" @click="triggerFileInput('a')" @drop.prevent="handleDrop($event, 'a')" @dragover.prevent>
        <input
          ref="fileInputA"
          type="file"
          accept="video/mp4,video/mov,video/avi,video/webm"
          @change="handleFileSelect($event, 'a')"
          style="display: none"
        />
        <div v-if="!videoA" class="upload-placeholder">
          <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <p>Drop video or click to upload</p>
          <span class="file-types">MP4, MOV, AVI, WebM</span>
        </div>
        <div v-else class="file-info">
          <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="23 7 16 12 23 17 23 7"/>
            <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
          </svg>
          <span class="file-name">{{ videoA.name }}</span>
          <span class="file-size">{{ formatFileSize(videoA.size) }}</span>
        </div>
      </div>

      <!-- ROI Scores for Variant A -->
      <div v-if="roiA" class="roi-display">
        <h3>Neural ROI Scores</h3>
        <div class="roi-grid">
          <div class="roi-item">
            <span class="roi-label">A5 (Auditory)</span>
            <div class="roi-bar"><div class="roi-fill" :style="{ width: (roiA.A5 * 100) + '%' }"></div></div>
            <span class="roi-value">{{ (roiA.A5 * 100).toFixed(0) }}%</span>
          </div>
          <div class="roi-item">
            <span class="roi-label">LO (Visual)</span>
            <div class="roi-bar"><div class="roi-fill" :style="{ width: (roiA.LO * 100) + '%' }"></div></div>
            <span class="roi-value">{{ (roiA.LO * 100).toFixed(0) }}%</span>
          </div>
          <div class="roi-item">
            <span class="roi-label">Area45 (Reward)</span>
            <div class="roi-bar"><div class="roi-fill" :style="{ width: (roiA.Area45 * 100) + '%' }"></div></div>
            <span class="roi-value">{{ (roiA.Area45 * 100).toFixed(0) }}%</span>
          </div>
          <div class="roi-item">
            <span class="roi-label">TPJ (Social)</span>
            <div class="roi-bar"><div class="roi-fill" :style="{ width: (roiA.TPJ * 100) + '%' }"></div></div>
            <span class="roi-value">{{ (roiA.TPJ * 100).toFixed(0) }}%</span>
          </div>
        </div>
        <div v-if="gateA" class="gate-status" :class="gateA.severity">
          <span class="gate-icon">{{ gateA.passed ? '✓' : '⚠' }}</span>
          <span>{{ gateA.recommendation }}</span>
        </div>
      </div>
    </div>

    <!-- Variant B Upload -->
    <div class="variant-card">
      <div class="variant-header">
        <span class="variant-badge badge-b">Variant B</span>
        <span v-if="statusB" class="status-badge" :class="statusB">{{ statusB }}</span>
      </div>

      <div class="upload-zone" @click="triggerFileInput('b')" @drop.prevent="handleDrop($event, 'b')" @dragover.prevent>
        <input
          ref="fileInputB"
          type="file"
          accept="video/mp4,video/mov,video/avi,video/webm"
          @change="handleFileSelect($event, 'b')"
          style="display: none"
        />
        <div v-if="!videoB" class="upload-placeholder">
          <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          <p>Drop video or click to upload</p>
          <span class="file-types">MP4, MOV, AVI, WebM</span>
        </div>
        <div v-else class="file-info">
          <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="23 7 16 12 23 17 23 7"/>
            <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
          </svg>
          <span class="file-name">{{ videoB.name }}</span>
          <span class="file-size">{{ formatFileSize(videoB.size) }}</span>
        </div>
      </div>

      <!-- ROI Scores for Variant B -->
      <div v-if="roiB" class="roi-display">
        <h3>Neural ROI Scores</h3>
        <div class="roi-grid">
          <div class="roi-item">
            <span class="roi-label">A5 (Auditory)</span>
            <div class="roi-bar"><div class="roi-fill" :style="{ width: (roiB.A5 * 100) + '%' }"></div></div>
            <span class="roi-value">{{ (roiB.A5 * 100).toFixed(0) }}%</span>
          </div>
          <div class="roi-item">
            <span class="roi-label">LO (Visual)</span>
            <div class="roi-bar"><div class="roi-fill" :style="{ width: (roiB.LO * 100) + '%' }"></div></div>
            <span class="roi-value">{{ (roiB.LO * 100).toFixed(0) }}%</span>
          </div>
          <div class="roi-item">
            <span class="roi-label">Area45 (Reward)</span>
            <div class="roi-bar"><div class="roi-fill" :style="{ width: (roiB.Area45 * 100) + '%' }"></div></div>
            <span class="roi-value">{{ (roiB.Area45 * 100).toFixed(0) }}%</span>
          </div>
          <div class="roi-item">
            <span class="roi-label">TPJ (Social)</span>
            <div class="roi-bar"><div class="roi-fill" :style="{ width: (roiB.TPJ * 100) + '%' }"></div></div>
            <span class="roi-value">{{ (roiB.TPJ * 100).toFixed(0) }}%</span>
          </div>
        </div>
        <div v-if="gateB" class="gate-status" :class="gateB.severity">
          <span class="gate-icon">{{ gateB.passed ? '✓' : '⚠' }}</span>
          <span>{{ gateB.recommendation }}</span>
        </div>
      </div>
    </div>

    <!-- Simulation Requirements -->
    <div class="requirements-section">
      <label for="requirements">Simulation Requirements (optional)</label>
      <textarea
        id="requirements"
        v-model="requirements"
        placeholder="e.g., Predict which version will generate more positive engagement on Twitter..."
        rows="3"
      ></textarea>
    </div>

    <!-- Action Buttons -->
    <div class="actions">
      <button
        class="btn btn-primary"
        :disabled="!canRunTest || isRunning"
        @click="runABTest"
      >
        <span v-if="isRunning" class="spinner"></span>
        {{ isRunning ? 'Running Simulation...' : 'Run A/B Test' }}
      </button>
      <button class="btn btn-secondary" @click="$router.push('/')">Back to Home</button>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      <span class="error-icon">✕</span>
      <span>{{ error }}</span>
    </div>
  </div>
</template>

<script>
import { uploadVideo, getVideoStatus, createABTestWithVideos } from '../api/neurosim'

export default {
  name: 'NeuroSimUpload',
  data() {
    return {
      videoA: null,
      videoB: null,
      requirements: '',
      statusA: null,
      statusB: null,
      roiA: null,
      roiB: null,
      gateA: null,
      gateB: null,
      isRunning: false,
      error: null,
      pollIntervals: {},
    }
  },
  computed: {
    canRunTest() {
      return this.videoA && this.videoB && this.roiA && this.roiB
    },
  },
  methods: {
    triggerFileInput(variant) {
      const input = variant === 'a' ? this.$refs.fileInputA : this.$refs.fileInputB
      input.click()
    },

    handleFileSelect(event, variant) {
      const file = event.target.files[0]
      if (file) {
        this.handleFile(file, variant)
      }
    },

    handleDrop(event, variant) {
      const file = event.dataTransfer.files[0]
      if (file) {
        this.handleFile(file, variant)
      }
    },

    async handleFile(file, variant) {
      const allowed = ['video/mp4', 'video/quicktime', 'video/x-msvideo', 'video/webm']
      const ext = file.name.split('.').pop().toLowerCase()
      const allowedExts = ['mp4', 'mov', 'avi', 'webm']

      if (!allowedExts.includes(ext)) {
        this.error = `Unsupported file type. Please use MP4, MOV, AVI, or WebM.`
        return
      }

      if (variant === 'a') {
        this.videoA = file
        this.roiA = null
        this.gateA = null
        this.statusA = 'uploading'
      } else {
        this.videoB = file
        this.roiB = null
        this.gateB = null
        this.statusB = 'uploading'
      }

      try {
        const result = await uploadVideo(file, this.requirements)
        if (result.status === 'processing') {
          this.setStatus(variant, 'processing')
          this.startPolling(variant, result.video_id)
        } else if (result.status === 'complete') {
          this.setResults(variant, result)
        }
      } catch (err) {
        this.error = `Upload failed: ${err.message}`
        this.setStatus(variant, 'error')
      }
    },

    startPolling(variant, videoId) {
      this.stopPolling(variant)

      const poll = async () => {
        try {
          const result = await getVideoStatus(videoId)
          if (result.status === 'complete') {
            this.setResults(variant, result)
            this.stopPolling(variant)
          } else if (result.status === 'error') {
            this.error = result.error || 'Video processing failed'
            this.setStatus(variant, 'error')
            this.stopPolling(variant)
          } else {
            this.setStatus(variant, 'processing')
          }
        } catch (err) {
          this.error = `Failed to check video status: ${err.message}`
          this.setStatus(variant, 'error')
          this.stopPolling(variant)
        }
      }

      poll()
      const interval = setInterval(async () => {
        await poll()
      }, 3000)

      this.pollIntervals[variant] = interval
    },

    stopPolling(variant) {
      if (this.pollIntervals[variant]) {
        clearInterval(this.pollIntervals[variant])
        delete this.pollIntervals[variant]
      }
    },

    setResults(variant, result) {
      if (variant === 'a') {
        this.roiA = result.roi_scores
        this.gateA = result.stage_gate
        this.statusA = 'complete'
      } else {
        this.roiB = result.roi_scores
        this.gateB = result.stage_gate
        this.statusB = 'complete'
      }
    },

    setStatus(variant, status) {
      if (variant === 'a') {
        this.statusA = status
      } else {
        this.statusB = status
      }
    },

    async runABTest() {
      if (!this.videoA || !this.videoB) {
        this.error = 'Please upload both video variants'
        return
      }

      this.isRunning = true
      this.error = null

      try {
        const result = await createABTestWithVideos(this.videoA, this.videoB, this.requirements)

        if (result.experiment_id) {
          // Navigate to results page
          this.$router.push({
            name: 'NeuroSimDashboard',
            params: { experimentId: result.experiment_id },
          })
        } else {
          this.error = 'A/B test started but no experiment ID returned'
        }
      } catch (err) {
        this.error = `A/B test failed: ${err.message}`
      } finally {
        this.isRunning = false
      }
    },

    formatFileSize(bytes) {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    },
  },
  beforeUnmount() {
    for (const variant of Object.keys(this.pollIntervals)) {
      this.stopPolling(variant)
    }
  },
}
</script>

<style scoped>
.neurosim-upload {
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
  font-size: 1.1rem;
}

.variant-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.variant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.variant-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
}

.badge-a {
  background: #e3f2fd;
  color: #1976d2;
}

.badge-b {
  background: #f3e5f5;
  color: #7b1fa2;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
}

.status-badge.uploading {
  background: #fff3e0;
  color: #f57c00;
}

.status-badge.processing {
  background: #e3f2fd;
  color: #1976d2;
}

.status-badge.complete {
  background: #e8f5e9;
  color: #388e3c;
}

.status-badge.error {
  background: #ffebee;
  color: #d32f2f;
}

.upload-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s;
}

.upload-zone:hover {
  border-color: #1976d2;
}

.upload-placeholder {
  color: #666;
}

.upload-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 1rem;
  color: #999;
}

.file-types {
  display: block;
  font-size: 0.85rem;
  color: #999;
  margin-top: 0.5rem;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.file-icon {
  width: 24px;
  height: 24px;
  color: #1976d2;
}

.file-name {
  font-weight: 500;
}

.file-size {
  color: #666;
  font-size: 0.9rem;
}

.roi-display {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.roi-display h3 {
  font-size: 1rem;
  margin-bottom: 1rem;
  color: #333;
}

.roi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.roi-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.roi-label {
  font-size: 0.85rem;
  color: #666;
}

.roi-bar {
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
  font-size: 0.9rem;
  font-weight: 600;
  color: #333;
}

.gate-status {
  margin-top: 1rem;
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

.requirements-section {
  margin-bottom: 1.5rem;
}

.requirements-section label {
  display: block;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.requirements-section textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
  resize: vertical;
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

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #1976d2;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1565c0;
}

.btn-secondary {
  background: #e0e0e0;
  color: #333;
}

.btn-secondary:hover {
  background: #d0d0d0;
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  margin-right: 0.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #ffebee;
  color: #d32f2f;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>
