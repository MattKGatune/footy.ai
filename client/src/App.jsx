import { useState, useEffect } from 'react'
import { fetchMatches, fetchShots, fetchTimeline } from './api'
import Controls from './components/Controls'
import Scoreboard from './components/Scoreboard'
import ShotMap from './components/ShotMap'
import WinProbTimeline from './components/WinProbTimeline'
import StatsTable from './components/StatsTable'
import NarrativeCard from './components/NarrativeCard'
import ChatPanel from './components/ChatPanel'

export default function App() {
  const [matches, setMatches] = useState([])
  const [selectedMeta, setSelectedMeta] = useState(null)
  const [shots, setShots] = useState([])
  const [timeline, setTimeline] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchMatches().then(setMatches).catch(console.error)
  }, [])

  async function handleMatchSelect(meta) {
    setSelectedMeta(null)
    setShots([])
    setTimeline([])
    setLoading(true)
    try {
      const [s, t] = await Promise.all([
        fetchShots(meta.match_id),
        fetchTimeline(meta.match_id),
      ])
      setShots(s)
      setTimeline(t)
      setSelectedMeta(meta)
    } catch (e) {
      console.error('Failed to load match:', e)
    } finally {
      setLoading(false)
    }
  }

  const homeTeam = timeline[0]?.home_team ?? selectedMeta?.home_team ?? ''
  const awayTeam = timeline[0]?.away_team ?? selectedMeta?.away_team ?? ''

  const cardCls = 'bg-card border border-border rounded-xl p-4'
  const labelCls = 'text-[0.7rem] font-semibold text-muted uppercase tracking-[0.8px] mb-2.5'

  return (
    <div className="bg-bg min-h-screen">
      <header className="bg-card border-b border-border px-8 py-3.5 flex items-center">
        <h1 className="text-[1.3rem] font-bold text-white tracking-tight">
          footy<span className="text-accent">.ai</span>
        </h1>
      </header>

      <Controls matches={matches} onMatchSelect={handleMatchSelect} />

      {loading && (
        <p className="px-8 pb-2 text-sm text-accent">Loading...</p>
      )}

      {selectedMeta && <Scoreboard meta={selectedMeta} />}

      {shots.length > 0 && timeline.length > 0 && (
        <div className="grid grid-cols-2 gap-5 px-8 pt-5">
          <div className={cardCls}>
            <p className={labelCls}>Shot Map</p>
            <ShotMap shots={shots} />
          </div>
          <div className={cardCls}>
            <p className={labelCls}>Win Probability</p>
            <WinProbTimeline timeline={timeline} />
          </div>
        </div>
      )}

      {shots.length > 0 && (
        <div className="px-8 py-5">
          <div className={cardCls}>
            <p className={labelCls}>Match Stats</p>
            <StatsTable shots={shots} homeTeam={homeTeam} awayTeam={awayTeam} />
          </div>
        </div>
      )}

      {selectedMeta && (
        <NarrativeCard matchId={selectedMeta.match_id} key={selectedMeta.match_id} />
      )}

      <ChatPanel />
    </div>
  )
}
