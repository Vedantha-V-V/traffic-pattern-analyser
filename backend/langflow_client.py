import requests
import os
import time
from typing import Dict, Any

LANGFLOW_API_URL = os.getenv('LANGFLOW_API_URL', 'http://localhost:7860/api/v1/run')
USE_MOCK_LANGFLOW = os.getenv('USE_MOCK_LANGFLOW', 'true').lower() == 'true'
TIMEOUT = 45
MAX_RETRIES = 2
RETRY_DELAY = 5

def _base_langflow_url() -> str:
    """
    Derive a base LangFlow host URL for health checks.
    Examples:
      - http://localhost:7860/api/v1/run/flow_id -> http://localhost:7860
      - http://localhost:7860/api/v1/run        -> http://localhost:7860
    """
    if "/api/" in LANGFLOW_API_URL:
        return LANGFLOW_API_URL.split("/api/")[0]
    return LANGFLOW_API_URL.rstrip("/")

def check_langflow_health() -> str:
    """Check if LangFlow API is accessible"""
    if USE_MOCK_LANGFLOW:
        return "mock_mode"
    
    try:
        response = requests.get(f"{_base_langflow_url()}/health", timeout=5)
        if response.status_code == 200:
            return "healthy"
        return f"unhealthy (status: {response.status_code})"
    except requests.exceptions.RequestException:
        return "unreachable"

def send_to_langflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send preprocessed data to LangFlow agents
    Implements retry logic and fallback to mock response
    """
    if USE_MOCK_LANGFLOW:
        return generate_mock_response(payload)
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                LANGFLOW_API_URL,
                json=payload,
                timeout=TIMEOUT,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"LangFlow endpoint not found: {LANGFLOW_API_URL}")
                return generate_mock_response(payload)
            else:
                print(f"LangFlow returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"LangFlow request timeout (attempt {attempt + 1}/{MAX_RETRIES})")
        except requests.exceptions.ConnectionError:
            print(f"Cannot connect to LangFlow (attempt {attempt + 1}/{MAX_RETRIES})")
        except Exception as e:
            print(f"LangFlow error: {str(e)}")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
    
    # Fallback to mock response
    print("Falling back to mock response")
    return generate_mock_response(payload)

def generate_mock_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate mock response for testing without LangFlow
    Simulates agent analysis based on baselines
    """
    anomalies = []
    locations = payload.get('locations', [])
    baselines = payload.get('baselines', {})
    raw_data = payload.get('raw_data', [])
    
    # Detect simple anomalies (>30% above baseline)
    for record in raw_data[:20]:  # Check first 20 records
        location = record['location']
        hour = str(record['hour'])
        vehicle_count = record['vehicle_count']
        
        if location in baselines and hour in baselines[location]['vehicle_count']:
            baseline_mean = baselines[location]['vehicle_count'][hour]['mean']
            deviation_pct = ((vehicle_count - baseline_mean) / baseline_mean) * 100
            
            if abs(deviation_pct) > 30:
                severity = "high" if abs(deviation_pct) > 50 else "medium"
                anomalies.append({
                    'timestamp': record['timestamp'],
                    'location': location,
                    'severity': severity,
                    'vehicle_count': vehicle_count,
                    'baseline': baseline_mean,
                    'deviation_pct': round(deviation_pct, 1),
                    'description': f"Traffic {'spike' if deviation_pct > 0 else 'drop'} of {abs(round(deviation_pct))}% detected"
                })
    
    # Generate insights
    if anomalies:
        high_severity_count = sum(1 for a in anomalies if a['severity'] == 'high')
        insights = f"Analysis detected {len(anomalies)} traffic anomalies across {len(locations)} locations. "
        
        if high_severity_count > 0:
            insights += f"{high_severity_count} high-severity incidents require immediate attention. "
        
        peak_anomaly = max(anomalies, key=lambda x: abs(x['deviation_pct']))
        insights += f"Most significant anomaly: {peak_anomaly['location']} at {peak_anomaly['timestamp'][:16]} with {abs(peak_anomaly['deviation_pct'])}% deviation from baseline."
    else:
        insights = "No significant traffic anomalies detected. Traffic patterns are within normal operating ranges across all monitored locations."
    
    # Generate recommendations
    recommendations = []
    if len(anomalies) > 3:
        recommendations.append("Consider deploying additional traffic monitoring resources during peak anomaly hours")
        recommendations.append("Review signal timing optimization for affected corridors")
    
    if any(a['severity'] == 'high' for a in anomalies):
        recommendations.append("Implement incident response protocols for high-severity congestion events")
        recommendations.append("Evaluate alternative route suggestions for navigation systems")
    
    if not recommendations:
        recommendations.append("Maintain current traffic management strategies")
        recommendations.append("Continue monitoring for emerging patterns")
    
    return {
        "status": "success",
        "agent_results": {
            "pattern_detection": {
                "total_patterns": len(anomalies),
                "locations_affected": len(set(a['location'] for a in anomalies))
            },
            "anomaly_detection": {
                "anomalies": anomalies[:10],  # Return top 10
                "total_count": len(anomalies),
                "severity_breakdown": {
                    "high": sum(1 for a in anomalies if a['severity'] == 'high'),
                    "medium": sum(1 for a in anomalies if a['severity'] == 'medium')
                }
            },
            "insights_generation": {
                "summary": insights,
                "recommendations": recommendations,
                "confidence": "high" if len(raw_data) > 50 else "medium"
            }
        },
        "processing_time_ms": 1250,
        "model_used": "ibm-granite-mock"
    }