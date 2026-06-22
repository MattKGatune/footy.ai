import { useState } from 'react'
import { postChat } from '../api'

const PILLS = [
  'Top 10 players by xG in the Premier League',
  'Who scored the most goals in Ligue 1?',
  'Which teams averaged the most shots in Serie A?',
  'Most assists in UEFA Euro',
]

function highlightSQL(sql) {
  const keywords = /\b(SELECT|FROM|WHERE|AND|OR|GROUP BY|ORDER BY|LIMIT|JOIN|ON|AS|COUNT|SUM|AVG|ROUND|DISTINCT|ILIKE|NOT|IN|IS|NULL|CASE|WHEN|THEN|ELSE|END|DESC|ASC|LEFT|INNER|HAVING)\b/g
  return sql.replace(keywords, match => `<span style="color:#2dd4bf">${match}</span>`)
}

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

  return (
    <div className="mx-8 mb-12 bg-surface border border-border rounded-xl p-6">
      <span className="text-[0.65rem] font-mono text-text-3 uppercase tracking-[1.5px] block mb-4">Ask the Data</span>

      <div className="flex flex-wrap gap-2 mb-4">
        {PILLS.map(p => (
          <button key={p} onClick={() => { setQuestion(p); submit(p) }}
            className="bg-bg border border-border rounded-full px-3 py-1 text-[0.72rem] font-mono text-text-3
              hover:border-border-2 hover:text-text-2 transition-colors cursor-pointer">
            {p}
          </button>
        ))}
      </div>

      <div className="flex gap-2.5 mb-5">
        <input
          className="flex-1 bg-bg text-text-1 border border-border rounded-lg px-3.5 py-2 text-[0.85rem] font-sans
            outline-none transition-colors focus:border-home placeholder:text-text-3"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && submit(question)}
          placeholder="e.g. Who had the most shots in the Premier League last season?"
        />
        <button
          onClick={() => submit(question)}
          disabled={loading}
          className={`px-5 py-2 rounded-lg text-[0.72rem] font-mono font-bold uppercase tracking-wider transition-colors
            ${loading ? 'bg-surface-2 text-text-3 cursor-not-allowed border border-border'
                      : 'bg-home hover:bg-home-h text-white cursor-pointer'}`}>
          {loading ? '...' : 'Ask'}
        </button>
      </div>

      {result && (
        <div className="space-y-4">
          {result.explanation && (
            <p className="text-[0.82rem] text-text-2 font-sans">{result.explanation}</p>
          )}

          {result.sql && (
            <pre
              className="bg-bg border border-border rounded-lg px-4 py-3 font-mono text-[0.75rem] text-text-2 whitespace-pre-wrap break-all leading-relaxed"
              dangerouslySetInnerHTML={{ __html: highlightSQL(result.sql) }}
            />
          )}

          {result.error && (
            <p className="text-[0.8rem] text-away font-mono">Error: {result.error}</p>
          )}

          {result.results && result.results.length > 0 && (
            <>
              <div className="overflow-x-auto rounded-lg border border-border">
                <table className="w-full border-collapse text-[0.78rem]">
                  <thead>
                    <tr className="border-b border-border">
                      {Object.keys(result.results[0]).map(col => (
                        <th key={col} className="text-left px-4 py-2 text-[0.62rem] font-mono text-text-3 uppercase tracking-[1px] whitespace-nowrap bg-surface-2">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.results.map((row, i) => (
                      <tr key={i} className="border-b border-[#111e2e] hover:bg-surface-2 transition-colors">
                        {Object.values(row).map((val, j) => (
                          <td key={j} className="px-4 py-2 font-mono text-text-1 whitespace-nowrap">
                            {val ?? '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-[0.65rem] font-mono text-text-3 uppercase tracking-widest">
                {result.row_count} row{result.row_count !== 1 ? 's' : ''}
              </p>
            </>
          )}

          {result.results && result.results.length === 0 && !result.error && (
            <p className="text-[0.8rem] font-mono text-text-3">No rows returned.</p>
          )}
        </div>
      )}
    </div>
  )
}
