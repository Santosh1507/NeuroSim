import service from './index'

/**
 * Upload a video file for NeuroSim processing.
 * @param {File} videoFile - The video file to upload
 * @param {string} context - Optional simulation context
 * @returns {Promise} Processing result
 */
export function uploadVideo(videoFile, context = '') {
  const formData = new FormData()
  formData.append('video', videoFile)
  if (context) {
    formData.append('context', context)
  }

  return service.post('/api/neurosim/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000, // 10 minutes for video processing
  })
}

/**
 * Get background video processing status.
 * @param {string} videoId - Stable video job ID returned by uploadVideo
 * @returns {Promise} Video processing status and ROI scores when complete
 */
export function getVideoStatus(videoId) {
  return service.get(`/api/neurosim/video/${videoId}/status`)
}

/**
 * Evaluate text content without video upload.
 * @param {string} transcript - Content text
 * @param {string} context - Optional simulation context
 * @returns {Promise} ROI scores, stage-gate, bridge params
 */
export function evaluateContent(transcript, context = '') {
  return service.post('/api/neurosim/evaluate', {
    transcript,
    context,
  })
}

/**
 * Create an A/B test with two text variants.
 * @param {object} variantA - { transcript, ... }
 * @param {object} variantB - { transcript, ... }
 * @param {string} requirements - Simulation requirements
 * @param {number} numAgents - Number of agents (default 100)
 * @param {number} numRounds - Number of rounds (default 10)
 * @returns {Promise} Experiment ID and status
 */
export function createABTest(variantA, variantB, requirements = '', numAgents = 100, numRounds = 10) {
  return service.post('/api/neurosim/ab-test', {
    variant_a: variantA,
    variant_b: variantB,
    simulation_requirements: requirements,
    num_agents: numAgents,
    num_rounds: numRounds,
  })
}

/**
 * Create an A/B test with two video files.
 * @param {File} videoA - Video file for variant A
 * @param {File} videoB - Video file for variant B
 * @param {string} context - Simulation context
 * @returns {Promise} Processing status
 */
export function createABTestWithVideos(videoA, videoB, context = '') {
  const formData = new FormData()
  formData.append('video_a', videoA)
  formData.append('video_b', videoB)
  if (context) {
    formData.append('context', context)
  }

  return service.post('/api/neurosim/ab-test', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000,
  })
}

/**
 * Get A/B experiment details.
 * @param {string} experimentId - Experiment ID
 * @returns {Promise} Experiment data
 */
export function getABTest(experimentId) {
  return service.get(`/api/neurosim/ab-test/${experimentId}`)
}

/**
 * Get A/B experiment results.
 * @param {string} experimentId - Experiment ID
 * @returns {Promise} Comparison results
 */
export function getABTestResults(experimentId) {
  return service.get(`/api/neurosim/ab-test/${experimentId}/results`)
}

/**
 * List all A/B experiments.
 * @returns {Promise} List of experiments
 */
export function listExperiments() {
  return service.get('/api/neurosim/experiments')
}

/**
 * Calculate bridge parameters from ROI scores.
 * @param {object} roiScores - { A5, LO, Area45, TPJ }
 * @returns {Promise} Bridge params and personas
 */
export function calculateBridge(roiScores) {
  return service.post('/api/neurosim/bridge', {
    roi_scores: roiScores,
  })
}
