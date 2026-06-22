export default function StatsTable({ shots, homeTeam, awayTeam }) {
  const h = shots.filter(s => s.is_home)
  const a = shots.filter(s => !s.is_home)
  const hXg = h.reduce((sum, s) => sum + (s.xg_pred || 0), 0)
  const aXg = a.reduce((sum, s) => sum + (s.xg_pred || 0), 0)

  const rows = [
    { label: 'Shots',     hv: h.length,   av: a.length,   fmt: v => v },
    { label: 'On Target', hv: h.filter(s => ['Goal','Saved'].includes(s.shot_outcome)).length,
                          av: a.filter(s => ['Goal','Saved'].includes(s.shot_outcome)).length, fmt: v => v },
    { label: 'xG',        hv: hXg,        av: aXg,        fmt: v => v.toFixed(2) },
    { label: 'xG / Shot', hv: h.length ? hXg / h.length : 0,
                          av: a.length ? aXg / a.length : 0, fmt: v => v.toFixed(3) },
  ]

  return (
    <div>
      <div className="grid grid-cols-[90px_1fr_90px] gap-3 pb-2.5 mb-1 border-b border-border">
        <span className="text-right text-xs font-semibold text-accent uppercase tracking-wide">{homeTeam}</span>
        <span />
        <span className="text-xs font-semibold text-danger uppercase tracking-wide">{awayTeam}</span>
      </div>
      {rows.map(row => {
        const total = (row.hv + row.av) || 1
        const hp = (row.hv / total * 100).toFixed(1)
        const ap = (100 - parseFloat(hp)).toFixed(1)
        return (
          <div key={row.label} className="grid grid-cols-[90px_1fr_90px] gap-3 items-center py-2.5 border-b border-[#151525]">
            <span className="text-right text-[1.05rem] font-bold tabular-nums text-accent">{row.fmt(row.hv)}</span>
            <div className="flex flex-col gap-1.5 items-center">
              <div className="flex w-full h-1.5 rounded-full overflow-hidden bg-bg">
                <div className="h-full bg-accent" style={{ width: `${hp}%` }} />
                <div className="h-full bg-danger" style={{ width: `${ap}%` }} />
              </div>
              <span className="text-[0.68rem] text-muted uppercase tracking-wide">{row.label}</span>
            </div>
            <span className="text-[1.05rem] font-bold tabular-nums text-danger">{row.fmt(row.av)}</span>
          </div>
        )
      })}
    </div>
  )
}
