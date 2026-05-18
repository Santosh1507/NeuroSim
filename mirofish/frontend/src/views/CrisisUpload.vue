<template>
  <div class="crisis-upload">
    <div class="upload-container">
      <header class="upload-header">
        <h1>PR Crisis Simulator</h1>
        <p class="subtitle">Test your press release before it goes public. Get 50 simulated reactions in under 2 minutes.</p>
      </header>

      <!-- Empty state for first-time users -->
      <div v-if="!hasHistory" class="empty-state">
        <div class="sample-report">
          <h3>How it works</h3>
          <ol>
            <li>Paste your press release or statement below</li>
            <li>Our AI simulates 50 diverse public reactions</li>
            <li>Get a risk report with blind spots you might have missed</li>
          </ol>
          <button class="btn-sample" @click="loadSample">Try with a sample document</button>
        </div>
      </div>

      <!-- Document input form -->
      <form @submit.prevent="submitSimulation" class="upload-form">
        <div class="form-group">
          <label for="document-type">Document Type</label>
          <select id="document-type" v-model="documentType" class="form-select">
            <option value="press_release">Press Release</option>
            <option value="statement">Public Statement</option>
            <option value="blog_post">Blog Post</option>
          </select>
        </div>

        <div class="form-group">
          <label for="document">Document Text</label>
          <textarea
            id="document"
            v-model="document"
            placeholder="Paste your press release, statement, or blog post here..."
            rows="12"
            class="form-textarea"
            :class="{ 'error': validationError }"
            @input="validateLength"
          ></textarea>
          <div class="char-count" :class="{ 'error': validationError }">
            {{ document.length }} / 10,000 characters
            <span v-if="document.length > 0 && document.length < 100" class="warning">
              (minimum 100 characters)
            </span>
          </div>
        </div>

        <div v-if="validationError" class="error-message">
          {{ validationError }}
        </div>

        <button
          type="submit"
          class="btn-submit"
          :disabled="isSubmitting || !isValid"
        >
          <span v-if="isSubmitting">Submitting...</span>
          <span v-else>Run Simulation</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'CrisisUpload',
  data() {
    return {
      document: '',
      documentType: 'press_release',
      validationError: '',
      isSubmitting: false,
      hasHistory: false,
    }
  },
  computed: {
    isValid() {
      return this.document.length >= 100 && this.document.length <= 10000 && !this.validationError
    }
  },
  methods: {
    validateLength() {
      if (this.document.length > 10000) {
        this.validationError = 'Document too long (max 10,000 characters)'
      } else if (this.document.length > 0 && this.document.length < 100) {
        this.validationError = 'Document too short (min 100 characters)'
      } else {
        this.validationError = ''
      }
    },
    async submitSimulation() {
      if (!this.isValid) return

      this.isSubmitting = true
      this.validationError = ''

      try {
        const response = await api.post('/simulations', {
          document: this.document,
          document_type: this.documentType
        })

        if (response.status === 202) {
          this.$router.push({
            name: 'CrisisProgress',
            params: { simulationId: response.data.simulation_id }
          })
        }
      } catch (error) {
        if (error.response) {
          this.validationError = error.response.data.error || 'Simulation failed'
        } else {
          this.validationError = 'Network error. Please try again.'
        }
      } finally {
        this.isSubmitting = false
      }
    },
    loadSample() {
      this.document = `FOR IMMEDIATE RELEASE

Acme Corporation Announces Major Restructuring Plan

NEW YORK, May 16, 2026 — Acme Corporation today announced a comprehensive restructuring plan designed to streamline operations and improve profitability. The plan includes the consolidation of three regional offices and a reduction in workforce affecting approximately 15% of employees globally.

"We recognize this is difficult news for our team members," said CEO Jane Smith. "However, these changes are necessary to ensure Acme's long-term competitiveness in an evolving market. We are committed to supporting affected employees with severance packages, extended benefits, and career transition services."

The company expects the restructuring to generate annual cost savings of approximately $50 million, beginning in fiscal year 2027. Acme also announced plans to reinvest a portion of these savings into its digital transformation initiative.

The restructuring is expected to be completed by Q4 2026.`
      this.documentType = 'press_release'
      this.validationError = ''
    }
  }
}
</script>

<style scoped>
.crisis-upload {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.upload-header {
  text-align: center;
  margin-bottom: 2rem;
}

.upload-header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
}

.empty-state {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.sample-report h3 {
  margin-bottom: 1rem;
}

.sample-report ol {
  margin-bottom: 1.5rem;
  padding-left: 1.5rem;
}

.sample-report li {
  margin-bottom: 0.5rem;
  color: #555;
}

.btn-sample {
  background: #e9ecef;
  border: 1px solid #dee2e6;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-sample:hover {
  background: #dee2e6;
}

.upload-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-group label {
  font-weight: 600;
  font-size: 0.9rem;
}

.form-select, .form-textarea {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  font-family: inherit;
}

.form-textarea {
  resize: vertical;
  min-height: 200px;
}

.form-textarea.error {
  border-color: #dc3545;
}

.char-count {
  font-size: 0.8rem;
  color: #666;
  text-align: right;
}

.char-count.error {
  color: #dc3545;
}

.char-count .warning {
  color: #ffc107;
}

.error-message {
  color: #dc3545;
  font-size: 0.9rem;
  padding: 0.5rem;
  background: #fff5f5;
  border-radius: 4px;
}

.btn-submit {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  font-weight: 600;
}

.btn-submit:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-submit:hover:not(:disabled) {
  background: #0056b3;
}
</style>
