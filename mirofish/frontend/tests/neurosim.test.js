import { mount } from '@vue/test-utils'
import { describe, it, expect, vi, beforeEach } from 'vitest'

import NeuroSimUpload from '../src/views/NeuroSimUpload.vue'
import { uploadVideo, getVideoStatus, createABTestWithVideos } from '../src/api/neurosim'

vi.mock('../src/api/neurosim', () => ({
  uploadVideo: vi.fn(),
  getVideoStatus: vi.fn(),
  createABTestWithVideos: vi.fn(),
}))

describe('NeuroSim upload flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('polls video status and stores ROI results after upload', async () => {
    uploadVideo.mockResolvedValue({ video_id: 'video_123', status: 'processing' })
    getVideoStatus.mockResolvedValue({
      video_id: 'video_123',
      status: 'complete',
      roi_scores: { A5: 0.6, LO: 0.7, Area45: 0.8, TPJ: 0.9 },
      stage_gate: { passed: true, severity: 'pass', recommendation: 'Proceed' },
    })

    const wrapper = mount(NeuroSimUpload, {
      global: {
        mocks: {
          $router: { push: vi.fn() },
        },
      },
    })

    await wrapper.vm.handleFile(new File(['video'], 'a.mp4', { type: 'video/mp4' }), 'a')
    await wrapper.vm.$nextTick()

    expect(uploadVideo).toHaveBeenCalledOnce()
    expect(getVideoStatus).toHaveBeenCalledWith('video_123')
    expect(wrapper.vm.statusA).toBe('complete')
    expect(wrapper.vm.roiA.A5).toBe(0.6)
  })

  it('navigates to dashboard when multipart A/B creation returns an experiment ID', async () => {
    const push = vi.fn()
    createABTestWithVideos.mockResolvedValue({ experiment_id: 'ab_123', status: 'processing' })

    const wrapper = mount(NeuroSimUpload, {
      global: {
        mocks: {
          $router: { push },
        },
      },
    })

    wrapper.vm.videoA = new File(['a'], 'a.mp4', { type: 'video/mp4' })
    wrapper.vm.videoB = new File(['b'], 'b.mp4', { type: 'video/mp4' })
    wrapper.vm.roiA = { A5: 0.6, LO: 0.7, Area45: 0.8, TPJ: 0.9 }
    wrapper.vm.roiB = { A5: 0.5, LO: 0.6, Area45: 0.7, TPJ: 0.8 }

    await wrapper.vm.runABTest()

    expect(createABTestWithVideos).toHaveBeenCalledOnce()
    expect(push).toHaveBeenCalledWith({
      name: 'NeuroSimDashboard',
      params: { experimentId: 'ab_123' },
    })
  })
})
