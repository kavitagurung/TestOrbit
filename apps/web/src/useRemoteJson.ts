import { useEffect, useState } from 'react'

// Bound cold starts and cancel obsolete requests when a filter changes.
export function useRemoteJson<T>(url: string, validate: (value: unknown) => value is T) {
  const [state, setState] = useState<{ url: string; data: T | null; error: string | null }>({ url, data: null, error: null })
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    let active = true
    let timedOut = false
    setState({ url, data: null, error: null })
    const timer = window.setTimeout(() => { timedOut = true; controller.abort() }, 90000)
    void (async () => {
      try {
        const response = await fetch(url, { signal: controller.signal })
        if (!response.ok) throw new Error('The service could not complete this request. Please retry.')
        const value: unknown = await response.json()
        if (!validate(value)) throw new Error('The service returned an invalid response. Please retry.')
        if (active) setState({ url, data: value, error: null })
      } catch (error) {
        if (active) setState({ url, data: null, error: timedOut ? 'The service took too long to respond. Please retry.' : error instanceof Error ? error.message : 'Unable to reach the service. Please retry.' })
      } finally {
        window.clearTimeout(timer)
      }
    })()
    return () => { active = false; window.clearTimeout(timer); controller.abort() }
  }, [url, attempt, validate])
  return { data: state.url === url ? state.data : null, error: state.url === url ? state.error : null, retry: () => setAttempt(value => value + 1) }
}
