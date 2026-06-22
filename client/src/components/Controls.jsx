export default function Controls({ matches, onMatchSelect }) {
  const competitions = [...new Map(
    matches.map(m => [m.competition_name, m.competition_name])
  ).entries()].sort((a, b) => a[0].localeCompare(b[0]))

  function handleComp(e) {
    const comp = e.target.value
    const homeEl = document.getElementById('home-select')
    const awayEl = document.getElementById('away-select')
    homeEl.innerHTML = '<option value="">Home team...</option>'
    awayEl.innerHTML = '<option value="">Away team...</option>'
    awayEl.disabled = true
    if (!comp) { homeEl.disabled = true; return }
    const teams = [...new Set(
      matches.filter(m => m.competition_name === comp).map(m => m.home_team)
    )].sort()
    teams.forEach(t => {
      const o = document.createElement('option'); o.value = t; o.textContent = t
      homeEl.appendChild(o)
    })
    homeEl.disabled = false
  }

  function handleHome(e) {
    const comp = document.getElementById('comp-select').value
    const home = e.target.value
    const awayEl = document.getElementById('away-select')
    awayEl.innerHTML = '<option value="">Away team...</option>'
    if (!home) { awayEl.disabled = true; return }
    const teams = [...new Set(
      matches.filter(m => m.competition_name === comp && m.home_team === home).map(m => m.away_team)
    )].sort()
    teams.forEach(t => {
      const o = document.createElement('option'); o.value = t; o.textContent = t
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

  const selectCls = [
    'bg-surface text-text-1 border border-border rounded-lg px-3 py-2',
    'text-[0.8rem] font-sans min-w-[190px] cursor-pointer outline-none',
    'transition-colors focus:border-home',
    'disabled:opacity-30 disabled:cursor-not-allowed',
    'appearance-none pr-8',
  ].join(' ')

  const labelCls = 'text-[0.62rem] font-mono text-text-3 uppercase tracking-[1.5px] mb-1.5'

  return (
    <div className="px-8 pt-5 pb-4 flex items-end gap-5 flex-wrap">
      {[
        { id: 'comp-select',  label: 'Competition', onChange: handleComp,  disabled: false,  placeholder: 'Select competition...' },
        { id: 'home-select',  label: 'Home',        onChange: handleHome,  disabled: true,   placeholder: 'Home team...' },
        { id: 'away-select',  label: 'Away',        onChange: handleAway,  disabled: true,   placeholder: 'Away team...' },
      ].map(({ id, label, onChange, disabled, placeholder }) => (
        <div key={id} className="relative flex flex-col">
          <label className={labelCls}>{label}</label>
          <div className="relative">
            <select id={id} className={selectCls} style={{ color: '#e2e8f0', background: '#0d1520', border: '1px solid #192637' }} disabled={disabled} onChange={onChange}>
              <option value="">{placeholder}</option>
              {id === 'comp-select' && competitions.map(([name]) => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
            <span className="absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none text-text-3 text-[0.6rem]">▼</span>
          </div>
        </div>
      ))}
    </div>
  )
}
