import { useMemo, useState } from 'react'
import axios from 'axios'
import './App.css'

import { FileUpload } from './components/FileUpload.jsx'
import { AnalysisStatus } from './components/AnalysisStatus.jsx'
import { TrafficChart } from './components/TrafficChart.jsx'
import { InsightsPanel } from './components/InsightsPanel.jsx'

const ANALYZE_URL = 'http://localhost:8000/analyze'

function normalizeRecommendations(recommendations) {
  if (Array.isArray(recommendations)) return recommendations.filter(Boolean)
  if (typeof recommendations === 'string') {
    return recommendations
      .split(/\r?\n|•|\u2022/g)
      .map((s) => s.trim())
      .filter(Boolean)
  }
  return []
}

function App() {
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResults, setAnalysisResults] = useState(null)
  const [error, setError] = useState('')
  const [phase, setPhase] = useState('uploading')

  const processedRecords = useMemo(() => {
    if (!analysisResults) return []

    const processed =
      analysisResults?.processed_data?.raw_data ??
      analysisResults?.processed_data?.records ??
      analysisResults?.processed_data ??
      []

    return Array.isArray(processed) ? processed : []
  }, [analysisResults])

  const langflowAnalysis = analysisResults?.langflow_analysis ?? {}
  const anomalies = Array.isArray(langflowAnalysis?.anomalies)
    ? langflowAnalysis.anomalies
    : []
  const insights =
    typeof langflowAnalysis?.insights === "string" ? langflowAnalysis.insights : ''
  const recommendations = normalizeRecommendations(langflowAnalysis?.recommendations)

  const chartData = useMemo(() => {
    if (!processedRecords.length) return []

    const anomalyKey = new Map()
    for (const a of anomalies) {
      const ts = a?.timestamp ?? a?.time ?? a?.datetime
      const loc = a?.location ?? a?.location_id ?? a?.locationId
      if (!ts || !loc) continue
      anomalyKey.set(`${String(ts)}__${String(loc)}`, {
        severity: String(a?.severity ?? 'medium').toLowerCase(),
      })
    }

    return processedRecords.map((r) => {
      const ts = r?.timestamp ?? r?.time ?? r?.datetime
      const loc = r?.location_id ?? r?.location ?? r?.locationId
      const key = `${String(ts)}__${String(loc)}`
      const meta = anomalyKey.get(key)
      return {
        ...r,
        timestamp: ts,
        location_id: loc,
        vehicle_count: r?.vehicle_count ?? r?.vehicleCount ?? r?.count,
        is_anomaly: Boolean(meta),
        anomaly_severity: meta?.severity ?? null,
      }
    })
  }, [processedRecords, anomalies])

  async function handleAnalyze() {
    setError('')
    setAnalysisResults(null)

    if (!uploadedFile) {
      setError('Please select a CSV file to analyze.')
      return
    }

    const formData = new FormData()
    formData.append('file', uploadedFile)

    try {
      setIsAnalyzing(true)
      setPhase('uploading')

      const res = await axios.post(ANALYZE_URL, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      })

      setPhase('analyzing')

      if (res?.data?.success === false) {
        setError(res?.data?.error || 'Analysis failed. Please try again.')
        setIsAnalyzing(false)
        return
      }

      setAnalysisResults(res?.data ?? null)
      setPhase('complete')
    } catch (e) {
      const msg =
        e?.response?.data?.error ||
        e?.response?.data?.detail ||
        e?.message ||
        'Unexpected error. Please try again.'
      setError(String(msg))
    } finally {
      setIsAnalyzing(false)
    }
  }

  const showResults = Boolean(analysisResults && !error)

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__headerInner">
          <div className="app__brand">
            <div>
              <div className="app__title">Traffic Pattern Detective</div>
              <div className="app__subtitle">
                Upload a traffic CSV to visualize trends and review AI-generated
                insights.
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="app__container">
        <div className="app__card">
          <FileUpload
            uploadedFile={uploadedFile}
            onFileSelected={setUploadedFile}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
          />
          {error ? <div className="app__error">{error}</div> : null}
        </div>

        <AnalysisStatus isAnalyzing={isAnalyzing} phase={phase} />

        {showResults ? (
          <section className="app__results app__fadeIn">
            <div className="app__resultsGrid">
              <TrafficChart data={chartData} />
              <InsightsPanel
                anomalies={anomalies}
                insights={insights}
                recommendations={recommendations}
              />
            </div>
          </section>
        ) : (
          <section className="app__empty">
            <div className="app__emptyCard">
              <div className="app__emptyTitle">Ready when you are</div>
              <div className="app__emptyText">
                Upload a CSV to generate baselines, visualize vehicle counts, and
                surface anomalies and recommendations.
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
