import { useEffect, useRef, useState } from 'react'
import './FileUpload.css'

const MAX_BYTES = 5 * 1024 * 1024

function formatBytes(bytes) {
  if (!Number.isFinite(bytes)) return ''
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(2)} MB`
}

function isCsvFile(file) {
  const name = (file?.name || '').toLowerCase()
  return name.endsWith('.csv') || file?.type === 'text/csv'
}

export function FileUpload({ uploadedFile, onFileSelected, onAnalyze, isAnalyzing }) {
  const inputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)
  const [localError, setLocalError] = useState('')

  useEffect(() => {
    setLocalError('')
  }, [uploadedFile])

  function validateAndSelect(file) {
    setLocalError('')

    if (!file) {
      onFileSelected(null)
      return
    }
    if (!isCsvFile(file)) {
      setLocalError('Please upload a .csv file.')
      onFileSelected(null)
      return
    }
    if (file.size > MAX_BYTES) {
      setLocalError(`File too large (${formatBytes(file.size)}). Max is 5 MB.`)
      onFileSelected(null)
      return
    }

    onFileSelected(file)
  }

  function handleDrop(e) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    const file = e.dataTransfer?.files?.[0] || null
    validateAndSelect(file)
  }

  function handleBrowseClick() {
    setLocalError('')
    inputRef.current?.click()
  }

  function handleInputChange(e) {
    const file = e.target?.files?.[0] || null
    validateAndSelect(file)
  }

  return (
    <div className="file-upload-container">
      <div className="file-upload-header">
        <div>
          <div className="file-upload-title">Upload CSV</div>
          <div className="file-upload-subtitle">
            Drag and drop your traffic dataset, or browse your files.
          </div>
        </div>
      </div>

      <div
        className={`drag-drop-zone ${isDragging ? 'drag-drop-zone--active' : ''}`}
        onDragEnter={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setIsDragging(true)
        }}
        onDragOver={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setIsDragging(true)
        }}
        onDragLeave={(e) => {
          e.preventDefault()
          e.stopPropagation()
          setIsDragging(false)
        }}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') handleBrowseClick()
        }}
        onClick={handleBrowseClick}
        aria-label="Upload CSV"
      >
        {/* <div className="drag-drop-zone__icon" aria-hidden="true">
          ⬆
        </div> */}
        <div className="drag-drop-zone__text">
          <span className="drag-drop-zone__strong">Drop your CSV here</span> or click
          to browse
        </div>
        <div className="drag-drop-zone__hint">Max size: 5MB • Format: .csv</div>
        <input
          ref={inputRef}
          className="file-upload-input"
          type="file"
          accept=".csv,text/csv"
          onChange={handleInputChange}
          disabled={isAnalyzing}
        />
      </div>

      <div className="file-upload-footer">
        <div className="file-info">
          {uploadedFile ? (
            <div className="file-info__ok">
              <span className="file-info__check" aria-hidden="true">
                ✓
              </span>
              <span className="file-info__name">{uploadedFile.name}</span>
              <span className="file-info__size">({formatBytes(uploadedFile.size)})</span>
            </div>
          ) : (
            <div className="file-info__empty">No file selected</div>
          )}
          {localError ? <div className="file-upload-error">{localError}</div> : null}
        </div>

        <button
          type="button"
          className="upload-button"
          onClick={onAnalyze}
          disabled={isAnalyzing || !uploadedFile || Boolean(localError)}
        >
          {isAnalyzing ? 'Analyzing…' : 'Analyze Traffic Data'}
        </button>
      </div>
    </div>
  )
}


