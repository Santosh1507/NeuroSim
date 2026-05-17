<template>
  <div class="ns-dashboard">
    <nav class="ns-nav">
      <div class="ns-nav-inner">
        <router-link to="/" class="ns-brand">
          <span class="ns-logo">◉</span> NeuroSim
        </router-link>
        <div class="ns-nav-links">
          <router-link to="/" class="ns-link">Home</router-link>
          <router-link to="/neurosim" class="ns-link active">Analysis</router-link>
        </div>
      </div>
    </nav>

    <main class="ns-main">
      <!-- Upload Section -->
      <section v-if="!analysisResult" class="ns-upload-section">
        <h1 class="ns-page-title">Upload Content for Analysis</h1>
        <p class="ns-page-sub">Drop a video file to run TRIBE v2 brain encoding + MiroFish swarm simulation.</p>

        <div class="ns-upload-zone" :class="{ dragging }" @drop.prevent="handleDrop" @dragover.prevent="dragging=true" @dragleave="dragging=false" @click="$refs.fileInput.click()">
          <input ref="fileInput" type="file" accept="video/*" hidden @change="handleFileSelect" />
          <div v-if="!uploading" class="ns-upload-content">
            <div class="ns-upload-icon">🎬</div>
            <p class="ns-upload-title">Drop video here or click to browse</p>
            <p class="ns-upload-hint">MP4, MOV, AVI, WebM — max 50MB</p>
          </div>
          <div v-else class="ns-upload-progress">
            <div class="ns-spinner"></div>
            <p>Analyzing <strong>{{ fileName }}</strong>...</p>
            <p class="ns-upload-hint">Running TRIBE v2 + MiroFish pipeline</p>
          </div>
        </div>
      </section>

      <!-- Results Section -->
      <section v-else class="ns-results">
        <div class="ns-results-header">
          <div>
            <h1 class="ns-page-title">Analysis Results</h1>
            <p class="ns-page-sub">{{ fileName }} — {{ analysisResult.created_at }}</p>
          </div>
          <button class="ns-btn-outline" @click="reset">New Analysis</button>
        </div>

        <!-- Stage Gate -->
        <div class="ns-stage-gate" :class="analysisResult.stage_gate?.passed ? 'passed' : 'failed'">
          <span class="ns-sg-icon">{{ analysisResult.stage_gate?.passed ? '✅' : '⚠️' }}</span>
          <div>
            <strong>Stage-Gate: {{ analysisResult.stage_gate?.passed ? 'PASSED' : 'FAILED' }}</strong>
            <p>W_attn = {{ analysisResult.stage_gate?.W_attn?.toFixed(3) }} (threshold: {{ analysisResult.stage_gate?.threshold }})</p>
          </div>
        </div>

        <!-- Score Cards -->
        <div class="ns-scores-grid">
          <div class="ns-score-card" v-for="score in scoreCards" :key="score.label">
            <div class="ns-score-value" :style="{ color: score.color }">{{ score.value }}</div>
            <div class="ns-score-label">{{ score.label }}</div>
            <div class="ns-score-sub">{{ score.detail }}</div>
          </div>
        </div>

        <!-- Brain Response -->
        <div class="ns-panel" v-if="analysisResult.tribev2_brain_response">
          <h2 class="ns-panel-title">🧠 TRIBE v2 Brain Response</h2>
          <div class="ns-brain-grid">
            <div class="ns-brain-bar" v-for="(val, key) in analysisResult.tribev2_brain_response.cortical_response" :key="key">
              <div class="ns-bar-label">{{ formatBrainKey(key) }}</div>
              <div class="ns-bar-track">
                <div class="ns-bar-fill" :style="{ width: val + '%', background: brainColor(val) }"></div>
              </div>
              <div class="ns-bar-value">{{ val }}%</div>
            </div>
          </div>
          <div class="ns-brain-mode">Mode: {{ analysisResult.tribev2_brain_response.mode }}</div>
        </div>

        <!-- MiroFish Simulation -->
        <div class="ns-panel" v-if="analysisResult.mirofish_simulation">
          <h2 class="ns-panel-title">🐟 MiroFish Swarm Simulation</h2>
          <div class="ns-sim-stats">
            <div class="ns-sim-stat">
              <span class="ns-stat-val">{{ analysisResult.mirofish_simulation.num_agents }}</span>
              <span class="ns-stat-lbl">Agents</span>
            </div>
            <div class="ns-sim-stat">
              <span class="ns-stat-val">{{ analysisResult.mirofish_simulation.final_sentiment }}%</span>
              <span class="ns-stat-lbl">Final Sentiment</span>
            </div>
            <div class="ns-sim-stat">
              <span class="ns-stat-val">{{ analysisResult.mirofish_simulation.viral_prediction?.split(' - ')[0] }}</span>
              <span class="ns-stat-lbl">Viral Potential</span>
            </div>
            <div class="ns-sim-stat">
              <span class="ns-stat-val">{{ analysisResult.mirofish_simulation.backlash_prediction?.split(' - ')[0]?.split(' ')[0] }}</span>
              <span class="ns-stat-lbl">Backlash Risk</span>
            </div>
          </div>

          <!-- Persona Distribution -->
          <h3 class="ns-sub-title">Persona Distribution</h3>
          <div class="ns-persona-grid">
            <div class="ns-persona" v-for="(pct, type) in analysisResult.mirofish_simulation.persona_distribution" :key="type">
              <div class="ns-persona-bar">
                <div class="ns-persona-fill" :style="{ width: pct + '%' }"></div>
              </div>
              <span class="ns-persona-type">{{ type.replace(/_/g, ' ') }}</span>
              <span class="ns-persona-pct">{{ pct }}%</span>
            </div>
          </div>
        </div>

        <!-- Sentiment Forecast -->
        <div class="ns-panel" v-if="analysisResult.sentiment_forecast">
          <h2 class="ns-panel-title">📊 Sentiment Forecast</h2>
          <div class="ns-sentiment-bars">
            <div class="ns-sent-row">
              <span class="ns-sent-label">Positive</span>
              <div class="ns-sent-track"><div class="ns-sent-fill positive" :style="{ width: analysisResult.sentiment_forecast.positive_sentiment_pct + '%' }"></div></div>
              <span class="ns-sent-val">{{ analysisResult.sentiment_forecast.positive_sentiment_pct }}%</span>
            </div>
            <div class="ns-sent-row">
              <span class="ns-sent-label">Neutral</span>
              <div class="ns-sent-track"><div class="ns-sent-fill neutral" :style="{ width: analysisResult.sentiment_forecast.neutral_sentiment_pct + '%' }"></div></div>
              <span class="ns-sent-val">{{ analysisResult.sentiment_forecast.neutral_sentiment_pct }}%</span>
            </div>
            <div class="ns-sent-row">
              <span class="ns-sent-label">Negative</span>
              <div class="ns-sent-track"><div class="ns-sent-fill negative" :style="{ width: analysisResult.sentiment_forecast.negative_sentiment_pct + '%' }"></div></div>
              <span class="ns-sent-val">{{ analysisResult.sentiment_forecast.negative_sentiment_pct }}%</span>
            </div>
          </div>
        </div>

        <!-- Recommendations -->
        <div class="ns-panel" v-if="analysisResult.recommendations?.length">
          <h2 class="ns-panel-title">💡 Recommendations</h2>
          <ul class="ns-recs">
            <li v-for="(rec, i) in analysisResult.recommendations" :key="i" class="ns-rec">{{ rec }}</li>
          </ul>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { getAccessToken } from '../lib/auth'

const API = import.meta.env.VITE_API_BASE_URL || ''
const uploading = ref(false)
const dragging = ref(false)
const fileName = ref('')
const analysisResult = ref(null)

const scoreCards = computed(() => {
  const r = analysisResult.value
  if (!r) return []
  return [
    { label: 'Hook Score', value: r.hook_score, detail: r.hook_details?.strength || '', color: r.hook_score > 70 ? '#06d6a0' : r.hook_score > 50 ? '#ffd166' : '#ef476f' },
    { label: 'Authenticity', value: r.authenticity_score, detail: r.authenticity_details?.authenticity_level || '', color: r.authenticity_score > 70 ? '#06d6a0' : '#ffd166' },
    { label: 'Viral Potential', value: r.viral_potential, detail: '', color: r.viral_potential > 50 ? '#06d6a0' : '#ffd166' },
    { label: 'Success Prob.', value: r.success_probability + '%', detail: '', color: '#4361ee' },
    { label: 'Risk Score', value: r.risk_score, detail: '', color: r.risk_score > 50 ? '#ef476f' : '#06d6a0' },
    { label: 'Shareability', value: (r.sentiment_forecast?.shareability_index || 0) + '%', detail: '', color: '#06d6a0' },
  ]
})

function formatBrainKey(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function brainColor(val) {
  if (val > 70) return '#06d6a0'
  if (val > 50) return '#4361ee'
  if (val > 30) return '#ffd166'
  return '#ef476f'
}

async function uploadFile(file) {
  uploading.value = true
  fileName.value = file.name
  try {
    const form = new FormData()
    form.append('file', file)
    const token = getAccessToken()
    const headers = token ? { Authorization: `Bearer ${token}` } : {}
    const { data } = await axios.post(`${API}/api/neurosim/analyze`, form, { headers })
    analysisResult.value = data
  } catch (e) {
    alert('Analysis failed: ' + (e.response?.data?.error || e.message))
  } finally {
    uploading.value = false
  }
}

function handleFileSelect(e) { if (e.target.files[0]) uploadFile(e.target.files[0]) }
function handleDrop(e) { dragging.value = false; if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]) }
function reset() { analysisResult.value = null; fileName.value = '' }
</script>

<style scoped>
.ns-dashboard { background: #000; color: #fff; min-height: 100vh; font-family: 'Inter', sans-serif; }
.ns-nav { position: sticky; top: 0; z-index: 50; background: rgba(0,0,0,0.85); backdrop-filter: blur(16px); border-bottom: 1px solid rgba(255,255,255,0.06); }
.ns-nav-inner { max-width: 1200px; margin: 0 auto; padding: 0 32px; height: 56px; display: flex; align-items: center; justify-content: space-between; }
.ns-brand { color: #fff; text-decoration: none; font-weight: 700; font-size: 1.1rem; display: flex; align-items: center; gap: 8px; }
.ns-logo { color: #06d6a0; }
.ns-nav-links { display: flex; gap: 24px; }
.ns-link { color: rgba(255,255,255,0.5); text-decoration: none; font-size: 0.9rem; font-weight: 500; }
.ns-link.active, .ns-link:hover { color: #fff; }

.ns-main { max-width: 1200px; margin: 0 auto; padding: 48px 32px; }
.ns-page-title { font-size: 2rem; font-weight: 700; letter-spacing: -1px; margin: 0 0 8px; }
.ns-page-sub { color: rgba(255,255,255,0.5); margin: 0 0 32px; font-size: 0.95rem; }

/* Upload */
.ns-upload-zone { border: 2px dashed rgba(255,255,255,0.1); border-radius: 16px; padding: 80px 40px; text-align: center; cursor: pointer; transition: all 0.3s; background: rgba(255,255,255,0.02); }
.ns-upload-zone:hover, .ns-upload-zone.dragging { border-color: #06d6a0; background: rgba(6,214,160,0.04); }
.ns-upload-icon { font-size: 3rem; margin-bottom: 16px; }
.ns-upload-title { font-size: 1.1rem; font-weight: 600; margin: 0 0 8px; }
.ns-upload-hint { color: rgba(255,255,255,0.4); font-size: 0.85rem; font-family: 'JetBrains Mono', monospace; }
.ns-spinner { width: 32px; height: 32px; border: 3px solid rgba(255,255,255,0.1); border-top-color: #06d6a0; border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Results */
.ns-results-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.ns-btn-outline { background: none; border: 1px solid rgba(255,255,255,0.15); color: #fff; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-family: inherit; font-size: 0.9rem; transition: all 0.2s; }
.ns-btn-outline:hover { border-color: #06d6a0; color: #06d6a0; }

/* Stage Gate */
.ns-stage-gate { display: flex; align-items: center; gap: 16px; padding: 20px 24px; border-radius: 12px; margin-bottom: 24px; border: 1px solid; }
.ns-stage-gate.passed { background: rgba(6,214,160,0.06); border-color: rgba(6,214,160,0.2); }
.ns-stage-gate.failed { background: rgba(239,71,111,0.06); border-color: rgba(239,71,111,0.2); }
.ns-stage-gate p { margin: 4px 0 0; font-size: 0.85rem; color: rgba(255,255,255,0.5); font-family: 'JetBrains Mono', monospace; }
.ns-sg-icon { font-size: 1.5rem; }

/* Score Cards */
.ns-scores-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 16px; margin-bottom: 32px; }
.ns-score-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 24px; text-align: center; }
.ns-score-value { font-size: 2rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.ns-score-label { font-size: 0.8rem; color: rgba(255,255,255,0.5); margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }
.ns-score-sub { font-size: 0.75rem; color: rgba(255,255,255,0.3); margin-top: 4px; }

/* Panels */
.ns-panel { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 16px; padding: 32px; margin-bottom: 24px; }
.ns-panel-title { font-size: 1.2rem; font-weight: 600; margin: 0 0 24px; }
.ns-sub-title { font-size: 0.95rem; font-weight: 600; margin: 24px 0 16px; color: rgba(255,255,255,0.7); }

/* Brain Bars */
.ns-brain-grid { display: flex; flex-direction: column; gap: 12px; }
.ns-brain-bar { display: grid; grid-template-columns: 180px 1fr 60px; align-items: center; gap: 12px; }
.ns-bar-label { font-size: 0.85rem; color: rgba(255,255,255,0.6); }
.ns-bar-track { height: 8px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; }
.ns-bar-fill { height: 100%; border-radius: 4px; transition: width 1s ease; }
.ns-bar-value { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; text-align: right; }
.ns-brain-mode { margin-top: 16px; font-size: 0.75rem; color: rgba(255,255,255,0.3); font-family: 'JetBrains Mono', monospace; }

/* Simulation Stats */
.ns-sim-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.ns-sim-stat { text-align: center; padding: 16px; background: rgba(255,255,255,0.03); border-radius: 8px; }
.ns-stat-val { display: block; font-size: 1.4rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; color: #06d6a0; }
.ns-stat-lbl { display: block; font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }

/* Persona */
.ns-persona-grid { display: flex; flex-direction: column; gap: 8px; }
.ns-persona { display: grid; grid-template-columns: 1fr 140px 50px; align-items: center; gap: 12px; }
.ns-persona-bar { height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
.ns-persona-fill { height: 100%; background: #4361ee; border-radius: 3px; }
.ns-persona-type { font-size: 0.8rem; color: rgba(255,255,255,0.6); text-transform: capitalize; }
.ns-persona-pct { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; text-align: right; }

/* Sentiment */
.ns-sent-row { display: grid; grid-template-columns: 80px 1fr 50px; align-items: center; gap: 12px; margin-bottom: 8px; }
.ns-sent-label { font-size: 0.85rem; color: rgba(255,255,255,0.6); }
.ns-sent-track { height: 10px; background: rgba(255,255,255,0.06); border-radius: 5px; overflow: hidden; }
.ns-sent-fill { height: 100%; border-radius: 5px; transition: width 1s; }
.ns-sent-fill.positive { background: #06d6a0; }
.ns-sent-fill.neutral { background: #ffd166; }
.ns-sent-fill.negative { background: #ef476f; }
.ns-sent-val { font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; text-align: right; }

/* Recommendations */
.ns-recs { list-style: none; padding: 0; margin: 0; }
.ns-rec { padding: 12px 16px; background: rgba(255,255,255,0.03); border-radius: 8px; margin-bottom: 8px; font-size: 0.9rem; line-height: 1.5; border-left: 3px solid #06d6a0; color: rgba(255,255,255,0.8); }

@media (max-width: 768px) {
  .ns-scores-grid { grid-template-columns: repeat(2, 1fr); }
  .ns-sim-stats { grid-template-columns: repeat(2, 1fr); }
  .ns-brain-bar { grid-template-columns: 1fr; }
}
</style>
