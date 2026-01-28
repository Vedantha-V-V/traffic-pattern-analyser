import './InsightsPanel.css'

function safeString(v) {
  return typeof v === 'string' ? v : ''
}

function normalizeSeverity(v) {
  const s = safeString(v).toLowerCase()
  if (s === 'high' || s === 'critical') return 'high'
  if (s === 'medium' || s === 'med') return 'medium'
  return 'low'
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
                      <td className="anomalies-table__timestamp">{String(ts)}</td>
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
          {insights ? insights : 'No summary returned by LangFlow.'}
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


