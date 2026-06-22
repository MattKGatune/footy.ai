import { useState } from 'react'
import { fetchNarrative } from '../api'

export default function NarrativeCard({ matchId }) {
  const [state, setState] = useState('idle') // idle | loading | done | error
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  async function generate() {
    setState('loading')
    try {
      const res = await fetchNarrative(matchId)
      setData(res)
      setState('done')
    } catch (e) {
      setError(e.message)
      setState('error')
    }
  }

  const btnLabel = state === 'loading' ? 'Generating...' : state === 'done' ? 'Regenerate' : 'Generate AI Analysis'
  const btnCls = `px-4 py-2 rounded-md text-xs font-semibold tracking-wide transition-colors
    ${state === 'loading'
      ? 'bg-dim text-muted cursor-not-allowed'
      : 'bg-accent hover:bg-accent-h text-white cursor-pointer'}`

  return (
    <div className="mx-8 mb-5 bg-card border border-border rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-[0.7rem] font-semibold text-muted uppercase tracking-[0.8px]">Match Analysis</h2>
        <button className={btnCls} onClick={generate} disabled={state === 'loading'}>
          {btnLabel}
        </button>
      </div>

      {state === 'loading' && (
        <p className="text-sm text-muted text-center py-5">Analysing match data with Claude...</p>
      )}

      {state === 'error' && (
        <p className="text-sm text-danger">{error}</p>
      )}

      {state === 'done' && data && (
        <>
          <p className="text-sm text-[#ccc] leading-relaxed mb-4">{data.narrative.summary}</p>
          <ul className="mb-4 list-none">
            {data.narrative.key_moments.map((m, i) => (
              <li key={i} className="relative pl-4 py-1.5 text-[0.85rem] text-[#bbb] border-b border-[#151525] leading-snug
                before:absolute before:left-0 before:text-accent before:content-['•']">
                {m}
              </li>
            ))}
          </ul>
          <p className="text-[0.85rem] text-[#999] italic leading-relaxed border-l-2 border-accent pl-3">
            {data.narrative.tactical_note}
          </p>
        </>
      )}
    </div>
  )
}
