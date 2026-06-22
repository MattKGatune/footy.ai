import { useState } from 'react'
import { fetchNarrative } from '../api'

export default function NarrativeCard({ matchId }) {
  const [state, setState] = useState('idle')
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

  const btnLabel = state === 'loading' ? 'Generating...' : state === 'done' ? 'Regenerate' : 'Generate Analysis'
  const btnCls = `px-4 py-1.5 rounded-md text-[0.72rem] font-mono font-bold uppercase tracking-wider transition-colors
    ${state === 'loading'
      ? 'bg-surface-2 text-text-3 cursor-not-allowed border border-border'
      : 'bg-transparent border border-home text-home hover:bg-home hover:text-white cursor-pointer'}`

  return (
    <div className="mx-8 mb-4 bg-surface border border-border rounded-xl p-6">
      <div className="flex items-center justify-between mb-5">
        <span className="text-[0.65rem] font-mono text-text-3 uppercase tracking-[1.5px]">Match Analysis</span>
        <button className={btnCls} onClick={generate} disabled={state === 'loading'}>
          {btnLabel}
        </button>
      </div>

      {state === 'idle' && (
        <p className="text-[0.8rem] text-text-3 font-mono">
          Generate an AI-written match report based on xG and shot data.
        </p>
      )}

      {state === 'loading' && (
        <p className="text-[0.8rem] text-text-3 font-mono animate-pulse">Analysing with Claude...</p>
      )}

      {state === 'error' && (
        <p className="text-[0.8rem] text-away">{error}</p>
      )}

      {state === 'done' && data && (
        <div className="space-y-5">
          <p className="text-[0.9rem] text-text-1 leading-relaxed font-sans">
            {data.narrative.summary}
          </p>
          <div className="border-l-2 border-border pl-4 space-y-2">
            {data.narrative.key_moments.map((m, i) => (
              <div key={i} className="flex gap-3 text-[0.82rem] text-text-2 leading-snug">
                <span className="text-data font-mono shrink-0">→</span>
                <span>{m}</span>
              </div>
            ))}
          </div>
          <p className="text-[0.82rem] text-text-2 italic leading-relaxed border-t border-border pt-4">
            {data.narrative.tactical_note}
          </p>
        </div>
      )}
    </div>
  )
}
