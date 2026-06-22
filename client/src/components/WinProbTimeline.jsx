import { useEffect, useRef } from 'react'

const Plotly = window.Plotly

export default function WinProbTimeline({ timeline }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!timeline.length || !ref.current) return

    const homeTeam = timeline[0].home_team
    const awayTeam = timeline[0].away_team
    const goals = timeline.filter(t => t.shot_outcome === 'Goal')

    const shapes = goals.map(g => ({
      type: 'line',
      x0: g.minute, x1: g.minute, y0: 0, y1: 1,
      line: { color: g.is_home ? '#6c63ff' : '#e63946', width: 1.5, dash: 'dash' },
    }))

    const annotations = goals.map(g => ({
      x: g.minute,
      y: g.is_home ? 0.95 : 0.05,
      text: `${g.is_home ? homeTeam.split(' ').pop() : awayTeam.split(' ').pop()} ${g.home_goals}-${g.away_goals}`,
      showarrow: false,
      font: { color: g.is_home ? '#6c63ff' : '#e63946', size: 10 },
      xanchor: 'left',
    }))

    Plotly.react(ref.current, [
      {
        x: timeline.map(t => t.minute),
        y: timeline.map(t => t.p_home_win),
        mode: 'lines', name: homeTeam,
        line: { color: '#6c63ff', width: 2.5 },
      },
      {
        x: timeline.map(t => t.minute),
        y: timeline.map(t => t.p_draw),
        mode: 'lines', name: 'Draw',
        line: { color: '#888', width: 1.5, dash: 'dot' },
      },
      {
        x: timeline.map(t => t.minute),
        y: timeline.map(t => t.p_away_win),
        mode: 'lines', name: awayTeam,
        line: { color: '#e63946', width: 2.5 },
      },
    ], {
      shapes,
      annotations,
      plot_bgcolor: '#080c12',
      paper_bgcolor: '#0d1520',
      font: { color: '#fff' },
      xaxis: { title: 'Minute', gridcolor: '#192637', zeroline: false, color: '#3a5068' },
      yaxis: { title: 'Win Probability', tickformat: '.0%', range: [0, 1], gridcolor: '#192637', zeroline: false, color: '#3a5068' },
      legend: { bgcolor: 'rgba(0,0,0,0.5)', font: { size: 11 } },
      margin: { t: 8, b: 40, l: 56, r: 8 },
      height: 400,
    }, { responsive: true })
  }, [timeline])

  return <div ref={ref} style={{ height: 400 }} />
}
