// @vitest-environment jsdom
import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { CompetitiveAnalysisPanel } from './App'

let container: HTMLDivElement
let root: Root
const result = (summary: string) => ({ mode: 'rule_based_fallback', range_days: 90, summary, themes: [], feature_leaders: [], recommendations: [], fallback_reason: 'no_evidence' })
const response = (summary: string) => new Response(JSON.stringify(result(summary)))
beforeEach(() => {
  Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true })
  container = document.createElement('div')
  document.body.appendChild(container)
  root = createRoot(container)
})
afterEach(async () => { await act(async () => root.unmount()); container.remove(); vi.unstubAllGlobals(); vi.useRealTimers() })
it('shows an error and recovers when Retry is clicked', async () => {
  const fetch = vi.fn().mockRejectedValueOnce(new TypeError('Failed to fetch')).mockResolvedValueOnce(response('Recovered summary'))
  vi.stubGlobal('fetch', fetch)
  await act(async () => root.render(<CompetitiveAnalysisPanel />))
  expect(container.textContent).toContain('Failed to fetch')
  expect(container.textContent).not.toContain('Loading an evidence-grounded')
  await act(async () => container.querySelector('button')!.click())
  expect(container.textContent).toContain('Recovered summary')
})
it('rejects malformed provider payloads without crashing the page', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ summary: 'bad', themes: null }))))
  await act(async () => root.render(<CompetitiveAnalysisPanel />))
  expect(container.textContent).toContain('invalid response')
})
it('times out a hanging request', async () => {
  vi.useFakeTimers()
  vi.stubGlobal('fetch', vi.fn((_url, options) => new Promise((_resolve, reject) => options.signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError'))))))
  await act(async () => root.render(<CompetitiveAnalysisPanel />))
  await act(async () => vi.advanceTimersByTimeAsync(90000))
  expect(container.textContent).toContain('took too long')
})
it('does not let an old range response overwrite the latest selection', async () => {
  let resolveOld!: (value: Response) => void
  const fetch = vi.fn().mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve })).mockResolvedValueOnce(response('New range'))
  vi.stubGlobal('fetch', fetch)
  await act(async () => root.render(<CompetitiveAnalysisPanel />))
  await act(async () => { const select = container.querySelector('select')!; select.value = '7'; select.dispatchEvent(new Event('change', { bubbles: true })) })
  await act(async () => resolveOld(response('Old range')))
  expect(container.textContent).toContain('New range')
  expect(container.textContent).not.toContain('Old range')
})
