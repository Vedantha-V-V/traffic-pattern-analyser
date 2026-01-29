# Traffic Pattern Detective

A full-stack application for analyzing traffic patterns, detecting anomalies, and generating AI-powered insights. Upload traffic data CSVs to visualize trends, identify congestion patterns, and receive actionable recommendations.

## Features

- **CSV Upload & Validation**: Drag-and-drop or browse to upload traffic datasets (max 5MB)
- **Data Processing**: Automatic cleaning, outlier detection, and baseline calculation
- **Traffic Visualization**: Interactive line charts showing vehicle counts across multiple locations
- **Anomaly Detection**: AI-powered detection of traffic spikes, incidents, and unusual patterns
- **Insights & Recommendations**: LangFlow-based analysis with actionable recommendations
- **Real-time Status**: Live progress tracking during analysis
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Tech Stack

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Chart.js** - Interactive traffic visualization
- **Axios** - HTTP client
- **CSS3** - Styling with CSS variables for theming

### Backend
- **FastAPI** - Modern Python web framework
- **Pandas** - Data processing and analysis
- **LangFlow** - AI agent orchestration
- **Python 3.8+** - Runtime

## Project Structure

```
.
├── frontend/                 # React + Vite application
│   ├── src/
│   │   ├── components/      # Reusable React components
│   │   │   ├── FileUpload.jsx
│   │   │   ├── AnalysisStatus.jsx
│   │   │   ├── TrafficChart.jsx
│   │   │   └── InsightsPanel.jsx
│   │   ├── App.jsx          # Main app component
│   │   ├── main.jsx         # Entry point
│   │   └── index.css        # Global styles & CSS variables
│   ├── package.json
│   └── vite.config.js
├── backend/                  # FastAPI application
│   ├── main.py              # API endpoints
│   ├── preprocessing.py     # Data cleaning & validation
│   ├── langflow_client.py   # LangFlow integration
│   ├── generate_data.py     # Test data generation
│   ├── sample_data*.csv     # Example datasets
│   └── .env                 # Environment variables
└── README.md                # This file
```

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Python 3.8+ and pip
- Git

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   venv/Scripts/activate 
   ```

3. **Install dependencies**:
   ```bash
   pip install fastapi uvicorn pandas numpy python-dotenv requests
   ```

4. **Configure environment** (optional):
   ```bash
   touch .env
   # Edit .env to set LangFlow API URL and other configs
   ```

5. **Generate test data** (optional):
   ```bash
   python generate_data.py
   ```

6. **Start the server**:
   ```bash
   uvicorn main:app --reload --port 8000
   # Server runs on http://localhost:8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm run dev
   # Application runs on http://localhost:5173
   ```

4. **Build for production**:
   ```bash
   npm run build
   ```

## API Endpoints

### `GET /health`
Check backend and LangFlow connectivity status.

**Response**:
```json
{
  "backend": "healthy",
  "langflow": "healthy|unhealthy|unreachable|mock_mode",
  "timestamp": "2024-01-22T10:30:00"
}
```

### `POST /analyze`
Upload and analyze a traffic CSV file.

**Request**:
- Content-Type: `multipart/form-data`
- File parameter: `file` (CSV format)

**Response**:
```json
{
  "success": true,
  "processed_data": {
    "total_records": 168,
    "locations": ["LOC_01", "LOC_02", "LOC_03"],
    "time_range": {
      "start": "2024-01-22T00:00:00",
      "end": "2024-01-28T23:00:00"
    },
    "raw_data": [...]
  },
  "baselines": {...},
  "langflow_analysis": {
    "anomalies": [...],
    "insights": "...",
    "recommendations": [...]
  }
}
```

## CSV Format

Required columns:
- `timestamp` - ISO format datetime (e.g., "2024-01-22 08:00:00")
- `location_id` - Location identifier (e.g., "LOC_01")
- `vehicle_count` - Numeric vehicle count
- `avg_speed_kmh` - Numeric average speed in km/h


## Data Processing Pipeline

1. **Validation**: Check CSV format and required columns
2. **Cleaning**: 
   - Convert timestamps
   - Handle missing values (forward fill + median imputation)
   - Remove outliers using IQR method
   - Sort by timestamp and location
3. **Feature Engineering**:
   - Extract hour and day-of-week
   - Create date column
4. **Baseline Calculation**: Compute hourly statistics per location
5. **LangFlow Analysis**: Send to AI agents for anomaly detection and insights
6. **Response**: Return processed data, baselines, and AI analysis

## Anomaly Detection

Anomalies are detected by comparing vehicle counts against hourly baselines:

- **High Severity**: >50% deviation from baseline
- **Medium Severity**: 30-50% deviation from baseline
- **Low Severity**: <30% deviation from baseline

Visual indicators on the chart:
- Red points = Detected anomalies
- Line color varies by location

## Testing

### Generate Test Data

```bash
cd backend
python generate_data.py
```

This creates:
- `sample_data.csv` - 7-day default dataset
- `sample_data_normal_week.csv` - Low anomaly rate
- `sample_data_high_congestion.csv` - High anomaly rate (15%)
- `sample_data_extended_period.csv` - 14-day dataset

### Using the Application

1. Start both backend and frontend servers
2. Open http://localhost:5173
3. Drag and drop a CSV file or click to browse
4. Click "Analyze Traffic Data"
5. View results with visualization and AI insights

## Frontend

### [FileUpload.jsx](frontend/src/components/FileUpload.jsx)
Handles CSV file selection with drag-and-drop, validation, and error messages.

### [AnalysisStatus.jsx](frontend/src/components/AnalysisStatus.jsx)
Shows real-time analysis progress with phase indicators (uploading → preprocessing → analyzing → complete).

### [TrafficChart.jsx](frontend/src/components/TrafficChart.jsx)
Interactive line chart displaying vehicle counts over time with anomaly highlights.

### [InsightsPanel.jsx](frontend/src/components/InsightsPanel.jsx)
Displays three sections:
- **Anomalies**: Table of detected traffic anomalies with severity badges
- **Summary**: AI-generated insights about traffic patterns
- **Recommendations**: Actionable suggestions for traffic management

## Backend

### [preprocessing.py](backend/preprocessing.py)
- `validate_csv()` - Validates CSV format and required columns
- `clean_data()` - Cleans and prepares data for analysis
- `calculate_baselines()` - Computes hourly statistics per location
- `prepare_langflow_payload()` - Structures data for LangFlow

### [langflow_client.py](backend/langflow_client.py)
- `check_langflow_health()` - Checks LangFlow API connectivity
- `generate_mock_response()` - Creates mock analysis (fallback)
- `send_to_langflow()` - Sends data to LangFlow agents with retry logic

### [main.py](backend/main.py)
- `GET /health` - Health check endpoint
- `POST /analyze` - Main analysis endpoint
- `GET /` - API info endpoint

## Styling

The application uses CSS variables for consistent theming:

```css
--primary: #2563eb          /* Blue */
--success: #10b981          /* Green */
--danger: #ef4444           /* Red */
--background: #f8fafc       /* Light gray */
--card-bg: #ffffff          /* White */
--text: #1e293b             /* Dark blue-gray */
--border: #e2e8f0           /* Light border */
```

All components are responsive and work on mobile (min 320px width).

## Error Handling

- **Invalid CSV**: File validation with specific error messages
- **Empty File**: Requires minimum 10 records
- **Missing Columns**: Lists required columns
- **File Size**: Max 5MB limit with formatted error message
- **API Errors**: Graceful fallback to mock responses
- **Network Issues**: Retry logic with exponential backoff

## Performance Considerations

- **Frontend**: Memoized components and data transformations reduce unnecessary re-renders
- **Backend**: Pandas operations optimized for data processing; limit LangFlow input to 100 records
- **Chart**: Only renders anomalies visually; handles up to 1000+ data points

## Future Enhancements

- [ ] Real-time streaming data support
- [ ] Custom anomaly thresholds
- [ ] Export analysis reports (PDF/CSV)
- [ ] Historical comparison and trend analysis
- [ ] Multi-user authentication
- [ ] Advanced filtering and date range selection
- [ ] Integration with additional data sources

## Contribution

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request