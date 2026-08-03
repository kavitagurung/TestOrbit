import { describe, expect, it } from 'vitest'
import { signals } from './demo-data'

describe('synthetic demo data', () => {
  it('keeps every signal visibly synthetic and evidence-backed', () => {
    expect(signals).toHaveLength(4)
    expect(signals.every((signal) => signal.confidence > 0 && signal.status.length > 0)).toBe(true)
  })
})

