export type Signal = { id: string; vendor: string; title: string; category: string; date: string; confidence: number; status: string; score: number; excerpt: string }

export const signals: Signal[] = [
  { id: 'sig-001', vendor: 'NovaTest', title: 'Announced guided AI test planning', category: 'New AI capability', date: '2026-07-30', confidence: 92, status: 'Confirmed by official announcement', score: 88, excerpt: 'Synthetic release note describes guided test-plan generation with human review.' },
  { id: 'sig-002', vendor: 'VerityQA', title: 'Added synthetic Workday coverage', category: 'New ERP support', date: '2026-07-27', confidence: 84, status: 'Confirmed by official documentation', score: 81, excerpt: 'Synthetic documentation now lists Workday among enterprise application examples.' },
  { id: 'sig-003', vendor: 'OrbitSpec', title: 'Changed trial messaging', category: 'Trial change', date: '2026-07-24', confidence: 68, status: 'Official marketing claim only', score: 56, excerpt: 'Synthetic pricing page changed from “start free” to “request access”.' },
  { id: 'sig-004', vendor: 'NovaTest', title: 'Published CI workflow connector', category: 'New integration', date: '2026-07-21', confidence: 89, status: 'Confirmed by official documentation', score: 76, excerpt: 'Synthetic integration guide describes pipeline-result artifacts.' },
]

export const competitors = [
  { name: 'NovaTest', category: 'AI-native competitor', focus: 'Enterprise web and API testing', changed: 3 },
  { name: 'VerityQA', category: 'ERP specialist', focus: 'Business-process assurance', changed: 2 },
  { name: 'OrbitSpec', category: 'Enterprise competitor', focus: 'Cross-application quality', changed: 1 },
]

export const matrix = [
  ['Natural-language test creation', 'Confirmed', 'Partial', 'Announced'],
  ['Workday', 'Unknown', 'Confirmed', 'Requires validation'],
  ['Self-healing selectors', 'Confirmed', 'Partial', 'Not found'],
  ['GitHub Actions', 'Confirmed', 'Partial', 'Confirmed'],
]

