import './InsightsPanel.css'
import { formatTimestamp } from '../utils/formatTimestamp'

function safeString(v) {
  return typeof v === 'string' ? v : ''
}

function normalizeSeverity(v) {
  const s = safeString(v).toLowerCase()
  if (s === 'high' || s === 'critical') return 'high'
  if (s === 'medium' || s === 'med') return 'medium'
  return 'low'
}

function formatSummary(text) {
  if (!text || typeof text !== 'string') return text

  // Split by major sections using **Section:**
  const parts = []
  let currentText = text

  // Parse Risk Level
  const riskMatch = currentText.match(/\*\*Risk Level:\*\*\s*([^*]+)/)
  if (riskMatch) {
    parts.push(
      <div key="risk-level" className="summary-section">
        <div className="summary-label">Risk Level</div>
        <div className="summary-value">{riskMatch[1].trim()}</div>
      </div>
    )
  }

  // Parse Key Concerns
  const concernsMatch = currentText.match(/\*\*Key Concerns:\*\*\s*([^*]+?)(?=\*\*|$)/s)
  if (concernsMatch) {
    parts.push(
      <div key="key-concerns" className="summary-section">
        <div className="summary-label">Key Concerns</div>
        <div className="summary-content">{concernsMatch[1].trim()}</div>
      </div>
    )
  }

  // Parse Recommended Actions
  const actionsMatch = currentText.match(/\*\*Recommended Actions:\*\*\s*(.+)/s)
  if (actionsMatch) {
    const actionsText = actionsMatch[1]
    const actionItems = []
    
    // Split by **Item:** pattern
    const itemMatches = actionsText.matchAll(/\*\*([^*]+?):\*\*\s*([^*]+?)(?=\s*-\s*\*\*|$)/gs)
    for (const match of itemMatches) {
      actionItems.push(
        <div key={`action-${actionItems.length}`} className="summary-action-item">
          <div className="summary-action-title">{match[1].trim()}</div>
          <div className="summary-action-desc">{match[2].trim()}</div>
        </div>
      )
    }

    if (actionItems.length > 0) {
      parts.push(
        <div key="recommended-actions" className="summary-section">
          <div className="summary-label">Recommended Actions</div>
          <div className="summary-actions">{actionItems}</div>
        </div>
      )
    }
  }

  // If no structured parts found, return original text
  if (parts.length === 0) {
    return text
  }

  return <div className="summary-formatted">{parts}</div>
}

export function InsightsPanel({ anomalies, insights, recommendations }) {
  const list = Array.isArray(anomalies) ? anomalies : []
  const recs = Array.isArray(recommendations) ? recommendations : []

  return (
    <div className="insights-panel">
      <div className="insights-panel__section anomaly-card">
        <div className="insights-panel__headerRow">
          <div className="insights-panel__title">Anomalies</div>
          <div className="insights-panel__meta">
            {list.length} detected
          </div>
        </div>

        <div className="anomalies-tableWrap">
          <table className="anomalies-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Location</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {list.length ? (
                list.map((a, idx) => {
                  const ts = a?.timestamp ?? a?.time ?? a?.datetime ?? '—'
                  const loc = a?.location ?? a?.location_id ?? a?.locationId ?? '—'
                  const sev = normalizeSeverity(a?.severity)
                  return (
                    <tr key={`${String(ts)}-${String(loc)}-${idx}`}>
                      <td className="anomalies-table__timestamp">{formatTimestamp(ts)}</td>
                      <td className="anomalies-table__location">{String(loc)}</td>
                      <td>
                        <span className={`severity-badge severity-badge--${sev}`}>
                          {sev}
                        </span>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={3} className="anomalies-table__empty">
                    No anomalies returned by LangFlow.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="insights-panel__section summary-card">
        <div className="insights-panel__title">Summary</div>
        <div className="summary-text">
          {insights ? formatSummary(insights) : 'No summary returned by LangFlow.'}
        </div>
      </div>

      <div className="insights-panel__section recommendations-card">
        <div className="insights-panel__title">Recommendations</div>
        {recs.length ? (
          <ul className="recommendations-list">
            {recs.map((r, idx) => (
              <li key={`${idx}-${r}`} className="recommendations-list__item">
                {String(r)}
              </li>
            ))}
          </ul>
        ) : (
          <div className="recommendations-empty">
            No recommendations returned by LangFlow.
          </div>
        )}
      </div>
    </div>
  )
}


