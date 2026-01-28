import { useEffect, useMemo, useState } from 'react'
import './AnalysisStatus.css'

const PHASES = ['uploading', 'preprocessing', 'analyzing', 'complete']

function phaseLabel(phase) {
  switch (phase) {
    case 'uploading':
      return 'Uploading...'
    case 'preprocessing':
      return 'Preprocessing...'
    case 'analyzing':
      return 'Analyzing...'
    case 'complete':
      return 'Complete!'
    default:
      return 'Working...'
  }
}

export function AnalysisStatus({ isAnalyzing, phase }) {
  const [internalPhase, setInternalPhase] = useState('uploading')

  useEffect(() => {
    if (!isAnalyzing) return
    setInternalPhase('uploading')

    const t1 = setTimeout(() => setInternalPhase('preprocessing'), 700)
    const t2 = setTimeout(() => setInternalPhase('analyzing'), 1700)

    return () => {
      clearTimeout(t1)
      clearTimeout(t2)
    }
  }, [isAnalyzing])

  const effectivePhase = useMemo(() => {
    if (!isAnalyzing && phase === 'complete') return 'complete'
    if (isAnalyzing) return internalPhase
    return null
  }, [internalPhase, isAnalyzing, phase])

  if (!isAnalyzing && phase !== 'complete') return null

  const currentIndex = PHASES.indexOf(effectivePhase || 'uploading')

  return (
    <section className="status-container" aria-live="polite">
      <div className="status-card">
        <div className="status-header">
          <div>
            <div className="status-title">Analysis Status</div>
            <div className="status-subtitle">{phaseLabel(effectivePhase)}</div>
          </div>
          <div className={`status-spinner ${effectivePhase === 'complete' ? 'status-spinner--done' : ''}`}>
            <div className="status-spinner__ring" />
          </div>
        </div>

        <div className="progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100}>
          <div
            className={`progress-bar progress-bar--${effectivePhase}`}
            data-phase={effectivePhase}
          />
        </div>

        <div className="status-steps">
          {PHASES.map((p, idx) => {
            const isDone = idx < currentIndex || effectivePhase === 'complete'
            const isActive = idx === currentIndex && effectivePhase !== 'complete'
            return (
              <div
                key={p}
                className={`status-step ${isDone ? 'status-step--done' : ''} ${isActive ? 'status-step--active' : ''}`}
              >
                <div className="status-step__dot" aria-hidden="true" />
                <div className="status-step__label">{phaseLabel(p).replace('...', '').replace('!', '')}</div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}


