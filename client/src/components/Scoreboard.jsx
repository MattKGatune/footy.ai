export default function Scoreboard({ meta }) {
  if (!meta) return null
  const date = meta.match_date
    ? new Date(meta.match_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    : ''

  return (
    <div className="mx-8 mt-1 bg-card border border-border rounded-xl px-8 py-5">
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-6">
        <div className="text-right text-[1.25rem] font-bold uppercase tracking-[1.5px] text-accent">
          {meta.home_team}
        </div>
        <div className="text-center">
          <div className="text-[2.8rem] font-extrabold text-white tracking-[6px] tabular-nums leading-none">
            {meta.home_score} — {meta.away_score}
          </div>
          <div className="mt-1.5 text-[0.7rem] text-muted uppercase tracking-[0.8px]">
            {[meta.competition_name, date].filter(Boolean).join('  ·  ')}
          </div>
        </div>
        <div className="text-left text-[1.25rem] font-bold uppercase tracking-[1.5px] text-danger">
          {meta.away_team}
        </div>
      </div>
    </div>
  )
}
