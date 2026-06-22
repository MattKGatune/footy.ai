const BASE = ''

export async function fetchMatches() {
  const res = await fetch(`${BASE}/matches`)
  if (!res.ok) throw new Error('Failed to load matches')
  return res.json()
}

export async function fetchShots(matchId) {
  const res = await fetch(`${BASE}/matches/${matchId}/shots`)
  if (!res.ok) throw new Error('Failed to load shots')
  return res.json()
}

export async function fetchTimeline(matchId) {
  const res = await fetch(`${BASE}/matches/${matchId}/timeline`)
  if (!res.ok) throw new Error('Failed to load timeline')
  return res.json()
}

export async function fetchNarrative(matchId) {
  const res = await fetch(`${BASE}/matches/${matchId}/narrative`)
  if (!res.ok) throw new Error('Failed to load narrative')
  return res.json()
}

export async function postChat(question) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })
  if (!res.ok) throw new Error('Chat request failed')
  return res.json()
}
