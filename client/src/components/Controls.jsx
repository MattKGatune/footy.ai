export default function Controls({ matches, onMatchSelect }) {
  const competitions = [...new Map(
    matches.map(m => [m.competition_name, m.competition_name])
  ).entries()].sort((a, b) => a[0].localeCompare(b[0]))

  function handleComp(e) {
    const comp = e.target.value
    const homeEl = document.getElementById('home-select')
    const awayEl = document.getElementById('away-select')
    homeEl.innerHTML = '<option value="">Select home team...</option>'
    awayEl.innerHTML = '<option value="">Select away team...</option>'
    awayEl.disabled = true
    if (!comp) { homeEl.disabled = true; return }
    const teams = [...new Set(
      matches.filter(m => m.competition_name === comp).map(m => m.home_team)
    )].sort()
    teams.forEach(t => {
      const o = document.createElement('option')
      o.value = t; o.textContent = t
      homeEl.appendChild(o)
    })
    homeEl.disabled = false
  }

  function handleHome(e) {
    const comp = document.getElementById('comp-select').value
    const home = e.target.value
    const awayEl = document.getElementById('away-select')
    awayEl.innerHTML = '<option value="">Select away team...</option>'
    if (!home) { awayEl.disabled = true; return }
    const teams = [...new Set(
      matches.filter(m => m.competition_name === comp && m.home_team === home).map(m => m.away_team)
    )].sort()
    teams.forEach(t => {
      const o = document.createElement('option')
      o.value = t; o.textContent = t
      awayEl.appendChild(o)
    })
    awayEl.disabled = false
  }

  function handleAway(e) {
    const comp = document.getElementById('comp-select').value
    const home = document.getElementById('home-select').value
    const away = e.target.value
    if (!away) return
    const match = matches.find(m =>
      m.competition_name === comp && m.home_team === home && m.away_team === away
    )
    if (match) onMatchSelect(match)
  }

  const selectCls = 'bg-[#1e1e2e] text-[#e0e0e0] border border-border rounded-md px-3 py-2 text-sm min-w-[200px] cursor-pointer outline-none transition-colors focus:border-accent disabled:opacity-35 disabled:cursor-not-allowed'
  const labelCls = 'text-[0.7rem] text-muted uppercase tracking-wider mb-1'

  return (
    <div className="px-8 pt-5 pb-3 flex items-end gap-4 flex-wrap">
      <div className="flex flex-col">
        <label className={labelCls}>Competition</label>
        <select id="comp-select" className={selectCls} onChange={handleComp}>
          <option value="">Select competition...</option>
          {competitions.map(([name]) => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
      </div>
      <div className="flex flex-col">
        <label className={labelCls}>Home team</label>
        <select id="home-select" className={selectCls} disabled onChange={handleHome}>
          <option value="">Select home team...</option>
        </select>
      </div>
      <div className="flex flex-col">
        <label className={labelCls}>Away team</label>
        <select id="away-select" className={selectCls} disabled onChange={handleAway}>
          <option value="">Select away team...</option>
        </select>
      </div>
    </div>
  )
}
