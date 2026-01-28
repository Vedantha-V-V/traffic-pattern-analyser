from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import io
import os
from dotenv import load_dotenv

from preprocessing import validate_csv, clean_data, calculate_baselines, prepare_langflow_payload
from langflow_client import send_to_langflow, check_langflow_health

load_dotenv()

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
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Validate CSV format
        validation_result = validate_csv(df)
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid CSV format",
                    "details": validation_result["errors"]
                }
            )
        
        # Clean data
        cleaned_df = clean_data(df)
        
        # Calculate baselines
        baselines = calculate_baselines(cleaned_df)
        
        # Prepare payload for LangFlow
        langflow_payload = prepare_langflow_payload(cleaned_df, baselines)
        
        # Send to LangFlow agents
        langflow_response = send_to_langflow(langflow_payload)
        
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
                "hourly_data": cleaned_df.to_dict(orient='records')
            },
            "baselines": baselines,
            "langflow_analysis": langflow_response
        }
        
        return JSONResponse(content=response_data)
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail={"error": "Empty CSV file", "details": "The uploaded file contains no data"}
        )
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "CSV parsing error", "details": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "details": str(e)}
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