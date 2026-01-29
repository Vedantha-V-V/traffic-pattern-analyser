from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import pandas as pd
import io
import os
import logging
from dotenv import load_dotenv

# Load env BEFORE importing modules that read env vars at import-time (e.g. langflow_client.py)
_ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=_ENV_PATH, override=True)

from preprocessing import validate_csv, clean_data, calculate_baselines, prepare_langflow_payload
from langflow_client import send_to_langflow, check_langflow_health

print("[ENV] USE_MOCK_LANGFLOW =", os.getenv("USE_MOCK_LANGFLOW"))
print("[ENV] LANGFLOW_API_URL  =", os.getenv("LANGFLOW_API_URL"))
print("[ENV] LANGFLOW_API_KEY  =", (os.getenv("LANGFLOW_API_KEY") or "")[:8] + "..." if os.getenv("LANGFLOW_API_KEY") else "")

logger = logging.getLogger("traffic_pattern_detective")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Traffic Pattern Detective API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Check backend and LangFlow connectivity"""
    langflow_status = check_langflow_health()
    return {
        "backend": "healthy",
        "langflow": langflow_status,
        "timestamp": pd.Timestamp.now().isoformat()
    }

@app.post("/analyze")
async def analyze_traffic(file: UploadFile = File(...)):
    """
    Main analysis endpoint
    1. Validate CSV
    2. Preprocess data
    3. Calculate baselines
    4. Send to LangFlow
    5. Return results
    """
    try:
        # Read CSV file
        contents = await file.read()

        # Decode bytes safely (handles UTF-8 BOM and falls back for non-UTF8 CSVs)
        try:
            text = contents.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = contents.decode("latin-1")

        df = pd.read_csv(io.StringIO(text))
        
        # Validate CSV format
        validation_result = validate_csv(df)
        if not validation_result["valid"]:
            return JSONResponse(
                status_code=400,
                content=jsonable_encoder(
                    {
                        "success": False,
                        "error": "Invalid CSV format",
                        "details": validation_result["errors"],
                    }
                ),
            )
        
        # Clean data
        cleaned_df = clean_data(df)

        # Prepare JSON-safe hourly data for the frontend
        cleaned_for_json = cleaned_df.copy()
        if 'timestamp' in cleaned_for_json.columns:
            cleaned_for_json['timestamp'] = cleaned_for_json['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'date' in cleaned_for_json.columns:
            cleaned_for_json['date'] = cleaned_for_json['date'].astype(str)
        hourly_records = cleaned_for_json.to_dict(orient='records')
        
        # Calculate baselines
        baselines = calculate_baselines(cleaned_df)
        
        # Prepare payload for LangFlow
        langflow_payload = prepare_langflow_payload(cleaned_df, baselines)
        
        # Send to LangFlow agents
        langflow_response = send_to_langflow(langflow_payload)

        # Normalize LangFlow response shape for frontend consumption
        langflow_analysis = {}
        if isinstance(langflow_response, dict) and 'agent_results' in langflow_response:
            agent_results = langflow_response.get('agent_results', {}) or {}
            anomaly_detection = agent_results.get('anomaly_detection', {}) or {}
            insights_generation = agent_results.get('insights_generation', {}) or {}
            langflow_analysis = {
                "anomalies": anomaly_detection.get("anomalies", []) or [],
                "insights": insights_generation.get("summary", "") or "",
                "recommendations": insights_generation.get("recommendations", []) or []
            }
        else:
            # If LangFlow already returns the expected shape, pass-through
            langflow_analysis = langflow_response
        
        # Prepare response
        response_data = {
            "success": True,
            "processed_data": {
                "total_records": len(cleaned_df),
                "locations": cleaned_df['location_id'].unique().tolist(),
                "time_range": {
                    "start": cleaned_df['timestamp'].min().isoformat(),
                    "end": cleaned_df['timestamp'].max().isoformat()
                },
                "raw_data": hourly_records,
                "hourly_data": hourly_records
            },
            "baselines": baselines,
            "langflow_analysis": langflow_analysis
        }
        
        return JSONResponse(content=jsonable_encoder(response_data))
        
    except pd.errors.EmptyDataError:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "Empty CSV file",
                "details": "The uploaded file contains no data",
            },
        )
    except pd.errors.ParserError as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": "CSV parsing error",
                "details": str(e),
            },
        )
    except Exception as e:
        logger.exception("Unhandled error in /analyze")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "details": str(e),
            },
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Traffic Pattern Detective API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "analyze": "/analyze (POST)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)