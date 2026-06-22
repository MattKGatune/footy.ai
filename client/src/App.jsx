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

  const card = 'bg-surface border border-border rounded-xl p-4'
  const label = 'text-[0.65rem] font-semibold font-display text-text-3 uppercase tracking-[1.5px] mb-3'

  return (
    <div className="bg-bg min-h-screen">
      {/* Signature top line */}
      <div className="fixed top-0 left-0 right-0 h-[2px] z-50"
           style={{ background: 'linear-gradient(to right, #6c63ff, #e63946)' }} />

      <header className="bg-surface border-b border-border px-8 pt-[2px]">
        <div className="py-3.5 flex items-center justify-between">
          <h1 className="font-display text-[1.2rem] font-bold text-text-1 tracking-tight">
            footy<span className="text-home">.ai</span>
          </h1>
          {loading && (
            <span className="text-[0.72rem] font-mono text-text-3 tracking-widest animate-pulse">
              LOADING
            </span>
          )}
        </div>
      </header>

      <Controls matches={matches} onMatchSelect={handleMatchSelect} />

      {selectedMeta && <Scoreboard meta={selectedMeta} />}

      {shots.length > 0 && timeline.length > 0 && (
        <div className="grid grid-cols-2 gap-4 px-8 pt-5">
          <div className={card}>
            <p className={label}>Shot Map</p>
            <ShotMap shots={shots} />
          </div>
          <div className={card}>
            <p className={label}>Win Probability</p>
            <WinProbTimeline timeline={timeline} />
          </div>
        </div>
      )}

      {shots.length > 0 && (
        <div className="px-8 py-4">
          <div className={card}>
            <p className={label}>Match Stats</p>
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
