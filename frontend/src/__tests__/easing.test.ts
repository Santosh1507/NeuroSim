import { describe, it, expect } from 'vitest'
import {
  easeOutExpo,
  easeSpring,
  easeSmooth,
  micro,
  fadeIn,
  staggerItem,
  heroReveal,
  heroRevealDelayed,
  tabSwitch,
  pulseSlow,
  pulseSlowDelayed,
  pulseFast,
  scanLine,
  hoverLift,
  tapPress,
} from '../lib/easing'

describe('easing constants', () => {
  it('easeOutExpo is a 4-element tuple', () => {
    expect(easeOutExpo).toHaveLength(4)
    expect(easeOutExpo[0]).toBe(0.16)
    expect(easeOutExpo[1]).toBe(1)
    expect(easeOutExpo[2]).toBe(0.3)
    expect(easeOutExpo[3]).toBe(1)
  })

  it('easeSpring has overshoot > 1', () => {
    expect(easeSpring[1]).toBeGreaterThan(1)
    expect(easeSpring[0]).toBe(0.34)
  })

  it('easeSmooth has standard cubic-bezier', () => {
    expect(easeSmooth[0]).toBe(0.4)
    expect(easeSmooth[3]).toBe(1)
  })
})

describe('transition presets', () => {
  it('micro has 80ms duration', () => {
    expect(micro.duration).toBe(0.08)
    expect(micro.ease).toBe(easeOutExpo)
  })

  it('fadeIn has 500ms duration', () => {
    expect(fadeIn.duration).toBe(0.5)
  })

  it('tabSwitch has 200ms with smooth ease', () => {
    expect(tabSwitch.duration).toBe(0.2)
    expect(tabSwitch.ease).toBe(easeSmooth)
  })

  it('pulseSlow has infinite repeat', () => {
    expect(pulseSlow.repeat).toBe(Infinity)
    expect(pulseSlow.ease).toBe('easeInOut')
  })

  it('pulseFast has 2.5s duration', () => {
    expect(pulseFast.duration).toBe(2.5)
  })

  it('scanLine has linear easing', () => {
    expect(scanLine.ease).toBe('linear')
  })
})

describe('staggerItem factory', () => {
  it('returns correct delay for index 0', () => {
    const result = staggerItem(0)
    expect(result.delay).toBe(0)
    expect(result.duration).toBe(0.4)
  })

  it('returns correct delay for index 3', () => {
    const result = staggerItem(3)
    expect(result.delay).toBe(3 * 0.06)
  })

  it('accepts custom baseDelay', () => {
    const result = staggerItem(2, 0.1)
    expect(result.delay).toBe(0.2)
  })
})

describe('heroRevealDelayed factory', () => {
  it('returns default delay of 0.2', () => {
    const result = heroRevealDelayed()
    expect(result.delay).toBe(0.2)
    expect(result.duration).toBe(0.9)
  })

  it('accepts custom delay', () => {
    const result = heroRevealDelayed(0.5)
    expect(result.delay).toBe(0.5)
  })
})

describe('pulseSlowDelayed factory', () => {
  it('returns default delay of 0.5', () => {
    const result = pulseSlowDelayed()
    expect(result.delay).toBe(0.5)
  })

  it('accepts custom delay', () => {
    const result = pulseSlowDelayed(1)
    expect(result.delay).toBe(1)
  })
})

describe('interaction presets', () => {
  it('hoverLift scales to 1.02', () => {
    expect(hoverLift.whileHover.scale).toBe(1.02)
    expect(hoverLift.transition).toBe(micro)
  })

  it('tapPress scales to 0.98', () => {
    expect(tapPress.whileTap.scale).toBe(0.98)
    expect(tapPress.transition).toBe(micro)
  })
})

describe('heroReveal', () => {
  it('has 700ms duration', () => {
    expect(heroReveal.duration).toBe(0.7)
    expect(heroReveal.ease).toBe(easeOutExpo)
  })
})
