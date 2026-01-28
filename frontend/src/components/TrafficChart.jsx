import { useMemo } from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import './TrafficChart.css'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend)

const LOCATION_COLORS = [
  '#2563eb',
  '#10b981',
  '#8b5cf6',
  '#f59e0b',
  '#0ea5e9',
  '#22c55e',
]

function toNumber(v) {
  if (typeof v === 'number') return v
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

export function TrafficChart({ data }) {
  const { labels, datasets } = useMemo(() => {
    const rows = Array.isArray(data) ? data : []
    const labelsSet = new Set()
    const locationsSet = new Set()
    for (const r of rows) {
      if (r?.timestamp) labelsSet.add(String(r.timestamp))
      if (r?.location_id) locationsSet.add(String(r.location_id))
    }

    const labelsArr = Array.from(labelsSet).sort()
    const locationsArr = Array.from(locationsSet).sort()

    const byLoc = new Map()
    for (const loc of locationsArr) byLoc.set(loc, new Map())
    for (const r of rows) {
      const ts = r?.timestamp ? String(r.timestamp) : null
      const loc = r?.location_id ? String(r.location_id) : null
      if (!ts || !loc || !byLoc.has(loc)) continue
      const map = byLoc.get(loc)
      map.set(ts, {
        y: toNumber(r?.vehicle_count),
        isAnomaly: Boolean(r?.is_anomaly),
      })
    }

    const ds = locationsArr.map((loc, idx) => {
      const color = LOCATION_COLORS[idx % LOCATION_COLORS.length]
      const map = byLoc.get(loc)
      const points = labelsArr.map((ts) => {
        const p = map?.get(ts)
        return p?.y == null ? null : { x: ts, y: p.y, isAnomaly: p.isAnomaly }
      })

      return {
        label: loc,
        data: points,
        borderColor: color,
        backgroundColor: color,
        tension: 0.25,
        spanGaps: true,
        pointRadius: (ctx) => (ctx?.raw?.isAnomaly ? 5 : 2),
        pointHoverRadius: (ctx) => (ctx?.raw?.isAnomaly ? 7 : 4),
        pointBackgroundColor: (ctx) => (ctx?.raw?.isAnomaly ? '#ef4444' : color),
        pointBorderColor: (ctx) => (ctx?.raw?.isAnomaly ? '#ef4444' : color),
        pointBorderWidth: (ctx) => (ctx?.raw?.isAnomaly ? 2 : 1),
      }
    })

    return { labels: labelsArr, datasets: ds }
  }, [data])

  const chartData = useMemo(
    () => ({
      labels,
      datasets,
    }),
    [labels, datasets],
  )

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'nearest', intersect: false },
      plugins: {
        legend: {
          position: 'bottom',
          labels: { boxWidth: 10, boxHeight: 10, usePointStyle: true },
        },
        title: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const y = ctx?.parsed?.y
              const anomaly = ctx?.raw?.isAnomaly ? ' (anomaly)' : ''
              return `${ctx.dataset.label}: ${y ?? '—'}${anomaly}`
            },
          },
        },
      },
      scales: {
        x: {
          ticks: { maxRotation: 0, autoSkip: true, color: '#64748b' },
          grid: { color: 'rgba(148,163,184,0.18)' },
        },
        y: {
          ticks: { color: '#64748b' },
          grid: { color: 'rgba(148,163,184,0.18)' },
          title: { display: true, text: 'Vehicle Count', color: '#64748b' },
        },
      },
    }),
    [],
  )

  return (
    <div className="chart-container">
      <div className="chart-titleRow">
        <div className="chart-title">Traffic Volume Over Time</div>
        <div className="chart-subtitle">Vehicle count by location (red points indicate anomalies)</div>
      </div>
      <div className="chart-wrapper">
        <Line data={chartData} options={options} />
      </div>
    </div>
  )
}


