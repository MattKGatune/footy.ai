export default function StatsTable({ shots, homeTeam, awayTeam }) {
  const h = shots.filter(s => s.is_home)
  const a = shots.filter(s => !s.is_home)
  const hXg = h.reduce((sum, s) => sum + (s.xg_pred || 0), 0)
  const aXg = a.reduce((sum, s) => sum + (s.xg_pred || 0), 0)

  const rows = [
    { label: 'Shots',      hv: h.length, av: a.length, fmt: v => v, highlight: false },
    {
      label: 'On Target',
      hv: h.filter(s => ['Goal','Saved'].includes(s.shot_outcome)).length,
      av: a.filter(s => ['Goal','Saved'].includes(s.shot_outcome)).length,
      fmt: v => v, highlight: false,
    },
    { label: 'xG',         hv: hXg,  av: aXg,  fmt: v => v.toFixed(2), highlight: true },
    {
      label: 'xG / Shot',
      hv: h.length ? hXg / h.length : 0,
      av: a.length ? aXg / a.length : 0,
      fmt: v => v.toFixed(3), highlight: true,
    },
  ]

  return (
    <div>
      {/* Header — separate from stat grid so names aren't constrained to 100px */}
      <div className="flex justify-between items-center pb-2.5 mb-1 border-b border-border">
        <span className="text-[0.75rem] font-display font-semibold uppercase tracking-wide" style={{ color: '#6c63ff' }}>
          {homeTeam}
        </span>
        <span className="text-[0.75rem] font-display font-semibold uppercase tracking-wide" style={{ color: '#e63946' }}>
          {awayTeam}
        </span>
      </div>

      {rows.map(row => {
        const total = (row.hv + row.av) || 1
        const hp = (row.hv / total * 100)
        const ap = 100 - hp
        const numColor = row.highlight ? '#2dd4bf' : '#e2e8f0'

        return (
          <div key={row.label} className="grid items-center py-2.5 border-b border-[#111e2e]"
               style={{ gridTemplateColumns: '80px 1fr 80px', gap: '12px' }}>
            <span className="text-right text-[1.05rem] font-mono font-bold tabular-nums" style={{ color: numColor }}>
              {row.fmt(row.hv)}
            </span>
            <div className="flex flex-col gap-1.5 items-center">
              <div className="flex w-full rounded-full overflow-hidden" style={{ height: '6px', background: '#080c12' }}>
                <div style={{ width: `${hp}%`, height: '100%', background: '#6c63ff' }} />
                <div style={{ width: `${ap}%`, height: '100%', background: '#e63946' }} />
              </div>
              <span className="text-[0.62rem] font-mono uppercase tracking-[1px]" style={{ color: '#3a5068' }}>
                {row.label}
              </span>
            </div>
            <span className="text-[1.05rem] font-mono font-bold tabular-nums" style={{ color: numColor }}>
              {row.fmt(row.av)}
            </span>
          </div>
        )
      })}
    </div>
  )
}
