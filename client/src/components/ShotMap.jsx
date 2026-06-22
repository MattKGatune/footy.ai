import { useEffect, useRef } from 'react'

const Plotly = window.Plotly

function rect(x0, y0, x1, y1) {
  return { type: 'rect', x0, y0, x1, y1, line: { color: 'rgba(255,255,255,0.5)', width: 1 } }
}
function line(x0, y0, x1, y1) {
  return { type: 'line', x0, y0, x1, y1, line: { color: 'rgba(255,255,255,0.5)', width: 1 } }
}

const pitchShapes = [
  rect(0, 0, 120, 80),
  rect(102, 18, 120, 62),
  rect(0, 18, 18, 62),
  rect(114, 30, 120, 50),
  rect(0, 30, 6, 50),
  line(60, 0, 60, 80),
  { type: 'circle', x0: 50, y0: 30, x1: 70, y1: 50, line: { color: 'rgba(255,255,255,0.5)', width: 1 } },
  rect(120, 36, 122, 44),
  rect(-2, 36, 0, 44),
]

export default function ShotMap({ shots }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!shots.length || !ref.current) return

    const teams = [...new Set(shots.map(s => s.team_name))]
    const traces = teams.map(team => {
      const ts = shots.filter(s => s.team_name === team).map(s => ({
        ...s,
        px: s.is_home ? s.location_x : 120 - s.location_x,
        py: s.is_home ? s.location_y : 80 - s.location_y,
      }))
      const isHome = ts[0]?.is_home ?? true
      return {
        x: ts.map(s => s.px),
        y: ts.map(s => s.py),
        mode: 'markers',
        name: team,
        marker: {
          size: ts.map(s => (s.xg_pred || 0.05) * 60 + 6),
          color: isHome ? '#6c63ff' : '#e63946',
          symbol: ts.map(s => s.shot_outcome === 'Goal' ? 'star' : 'circle'),
          line: { color: 'white', width: 1 },
          opacity: 0.85,
        },
        text: ts.map(s =>
          `${s.player_name}<br>Min ${s.minute}<br>xG: ${(s.xg_pred || 0).toFixed(2)}<br>${s.shot_outcome}`
        ),
        hoverinfo: 'text',
        type: 'scatter',
      }
    })

    Plotly.react(ref.current, traces, {
      shapes: pitchShapes,
      plot_bgcolor: '#224422',
      paper_bgcolor: '#0d1520',
      font: { color: '#fff' },
      xaxis: { range: [-5, 125], showgrid: false, zeroline: false, visible: false },
      yaxis: { range: [-5, 85], showgrid: false, zeroline: false, visible: false, scaleanchor: 'x', scaleratio: 1 },
      legend: { bgcolor: 'rgba(0,0,0,0.5)', font: { size: 11 } },
      margin: { t: 8, b: 8, l: 8, r: 8 },
      height: 400,
    }, { responsive: true })
  }, [shots])

  return <div ref={ref} style={{ height: 400 }} />
}
