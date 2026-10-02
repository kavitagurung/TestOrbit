import { API_BASE } from './api'
import { useRemoteJson } from './useRemoteJson'

type Activity = { scope: string; items: { id: number; competitor: string; source_name: string; source_url: string; detected_at: string; kind: 'baseline' | 'content_changed' }[] }
function isActivity(value: unknown): value is Activity {
  if (!value || typeof value !== 'object') return false
  const data = value as Activity
  return typeof data.scope === 'string' && Array.isArray(data.items) && data.items.every(item => item && typeof item.id === 'number' && typeof item.competitor === 'string' && typeof item.source_name === 'string' && typeof item.source_url === 'string' && /^https?:\/\//.test(item.source_url) && typeof item.detected_at === 'string' && ['baseline', 'content_changed'].includes(item.kind))
}
export function CollectedSourcesPanel() {
  const { data, error, retry } = useRemoteJson<Activity>(`${API_BASE}/api/v1/intelligence/collection-activity`, isActivity)
  return <section className="panel"><p className="eyebrow">COLLECTED SOURCE ACTIVITY</p><h2>Latest stored source snapshots</h2>
    {error ? <div role="alert"><p>{error}</p><button className="quiet" onClick={retry}>Retry collection activity</button></div> : !data ? <p className="muted">Loading stored collection activity…</p> : <>
      <p className="muted">{data.scope}</p>
      {!data.items.length && <p>No source snapshots have been stored yet. Collection has not produced evidence in this database.</p>}
      {data.items.map(item => <article key={item.id} className="signal real-signal"><div><p className="signal-meta">{item.competitor} · {new Date(item.detected_at).toLocaleString()}</p><h3>{item.source_name}</h3><p>{item.kind === 'baseline' ? 'Initial baseline captured' : 'Source content changed — review required'}</p><a href={item.source_url} target="_blank" rel="noreferrer">View public source →</a></div></article>)}
    </>}
  </section>
}
