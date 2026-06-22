export default function Scoreboard({ meta }) {
  if (!meta) return null

  const date = meta.match_date
    ? new Date(meta.match_date).toLocaleDateString('en-GB', {
        day: 'numeric', month: 'short', year: 'numeric',
      })
    : ''

  return (
    <div className="mx-8 mt-1 relative overflow-hidden rounded-xl border border-border">
      {/* Team-color split gradient */}
      <div className="absolute inset-0 pointer-events-none"
           style={{ background: 'linear-gradient(to right, rgba(108,99,255,0.09) 0%, transparent 38%, transparent 62%, rgba(230,57,70,0.09) 100%)' }} />

      <div className="relative px-10 py-7">
        {/* Eyebrow */}
        <div className="text-center mb-5">
          <span className="font-mono text-[0.62rem] text-text-3 uppercase tracking-[2.5px]">
            {meta.competition_name}
            {date && <span className="mx-2.5 text-border">|</span>}
            {date}
          </span>
        </div>

        {/* Score row */}
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-6">
          <div className="text-right">
            <span className="font-display text-[1.35rem] font-bold uppercase tracking-[2px] text-text-1">
              {meta.home_team}
            </span>
          </div>

          <div className="flex items-center gap-1 px-4">
            <span className="font-mono text-[3.5rem] font-bold text-text-1 tabular-nums leading-none">
              {meta.home_score}
            </span>
            <span className="font-mono text-[2rem] font-bold text-text-3 leading-none mx-1 tabular-nums">
              –
            </span>
            <span className="font-mono text-[3.5rem] font-bold text-text-1 tabular-nums leading-none">
              {meta.away_score}
            </span>
          </div>

          <div className="text-left">
            <span className="font-display text-[1.35rem] font-bold uppercase tracking-[2px] text-text-1">
              {meta.away_team}
            </span>
          </div>
        </div>

        {/* Home / Away indicators */}
        <div className="flex justify-between mt-5 px-1">
          <span className="flex items-center gap-1.5 text-[0.62rem] font-mono text-text-3 uppercase tracking-widest">
            <span className="w-1.5 h-1.5 rounded-full bg-home inline-block" />
            Home
          </span>
          <span className="flex items-center gap-1.5 text-[0.62rem] font-mono text-text-3 uppercase tracking-widest">
            Away
            <span className="w-1.5 h-1.5 rounded-full bg-away inline-block" />
          </span>
        </div>
      </div>
    </div>
  )
}
