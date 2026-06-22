import { useState } from 'react'
import { postChat } from '../api'

const PILLS = [
  'Top 10 players by xG in the Premier League',
  'Who scored the most goals in Ligue 1?',
  'Which teams averaged the most shots in Serie A?',
  'Most assists in UEFA Euro',
]

export default function ChatPanel() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  async function submit(q) {
    const text = q.trim()
    if (!text) return
    setLoading(true)
    setResult(null)
    try {
      const data = await postChat(text)
      setResult(data)
    } catch (e) {
      setResult({ error: e.message, sql: '', explanation: '', results: [], row_count: 0 })
    } finally {
      setLoading(false)
    }
  }

  const inputCls = 'flex-1 bg-bg text-[#e0e0e0] border border-border rounded-md px-3.5 py-2 text-sm outline-none transition-colors focus:border-accent'
  const btnCls = `px-5 py-2 rounded-md text-xs font-semibold tracking-wide transition-colors whitespace-nowrap
    ${loading ? 'bg-dim text-muted cursor-not-allowed' : 'bg-accent hover:bg-accent-h text-white cursor-pointer'}`

  return (
    <div className="mx-8 mb-12 bg-card border border-border rounded-xl p-6">
      <h2 className="text-[0.7rem] font-semibold text-muted uppercase tracking-[0.8px] mb-3.5">Ask the Data</h2>

      <div className="flex flex-wrap gap-2 mb-3.5">
        {PILLS.map(p => (
          <button key={p} onClick={() => { setQuestion(p); submit(p) }}
            className="bg-[#1e1e2e] border border-border rounded-full px-3 py-1 text-[0.75rem] text-[#888]
              hover:border-accent hover:text-[#c0bdff] transition-colors cursor-pointer">
            {p}
          </button>
        ))}
      </div>

      <div className="flex gap-2.5 mb-4">
        <input
          className={inputCls}
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && submit(question)}
          placeholder="Ask anything about the data..."
        />
        <button className={btnCls} onClick={() => submit(question)} disabled={loading}>
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </div>

      {result && (
        <div>
          {result.explanation && (
            <p className="text-[0.85rem] text-[#999] mb-3">{result.explanation}</p>
          )}
          {result.sql && (
            <pre className="bg-bg border border-border rounded-md px-3.5 py-3 font-mono text-[0.78rem] text-[#8b9aff] whitespace-pre-wrap break-all mb-3.5">
              {result.sql}
            </pre>
          )}
          {result.error && (
            <p className="text-sm text-danger mb-2">SQL error: {result.error}</p>
          )}
          {result.results && result.results.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-[0.8rem]">
                  <thead>
                    <tr>
                      {Object.keys(result.results[0]).map(col => (
                        <th key={col} className="text-left px-3 py-1.5 text-[0.68rem] text-muted uppercase tracking-wide border-b border-border">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.results.map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).map((val, j) => (
                          <td key={j} className="px-3 py-1.5 text-[#ccc] border-b border-[#151525]">
                            {val ?? ''}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-[0.72rem] text-muted mt-2.5">
                {result.row_count} row{result.row_count !== 1 ? 's' : ''}
              </p>
            </>
          )}
          {result.results && result.results.length === 0 && !result.error && (
            <p className="text-[0.85rem] text-muted">No rows returned.</p>
          )}
        </div>
      )}
    </div>
  )
}
