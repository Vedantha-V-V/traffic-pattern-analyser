import requests
import os
import time
from typing import Dict, Any
import json
import re

LANGFLOW_API_URL = os.getenv('LANGFLOW_API_URL', 'http://localhost:7860/api/v1/run')
LANGFLOW_API_KEY = os.getenv('LANGFLOW_API_KEY', '')
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
    
    base_url = _base_langflow_url()
    
    try:
        print(f"🏥 Checking LangFlow health at: {base_url}/health")
        
        headers = {}
        if LANGFLOW_API_KEY:
            headers['Authorization'] = f'Bearer {LANGFLOW_API_KEY}'
        
        response = requests.get(f"{base_url}/health", headers=headers, timeout=5)
        
        if response.status_code == 200:
            print("✅ LangFlow is healthy!")
            return "healthy"
        elif response.status_code == 403:
            print("⚠️  LangFlow returned 403 - Check API key")
            return "forbidden (check API key)"
        else:
            print(f"⚠️  LangFlow returned status {response.status_code}")
            return f"unhealthy (status: {response.status_code})"
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot reach LangFlow at {base_url}")
        print("   Is LangFlow running? Check the URL!")
        return "unreachable"
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return "unreachable"

def send_to_langflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send preprocessed data to LangFlow agents
    Implements retry logic and fallback to mock response
    """
    if USE_MOCK_LANGFLOW:
        print("⚠️  Using MOCK mode (USE_MOCK_LANGFLOW=true)")
        return generate_mock_response(payload)
    
    print(f"🚀 Sending to LangFlow: {LANGFLOW_API_URL}")
    if LANGFLOW_API_KEY:
        print(f"🔑 Using API key: {LANGFLOW_API_KEY[:15]}...")
    else:
        print("⚠️  No API key configured (LANGFLOW_API_KEY not set)")
    
    # First, detect anomalies using backend logic
    anomalies = []
    raw_data = payload.get('raw_data', [])
    baselines = payload.get('baselines', {})
    
    for record in raw_data[:20]:  # Check first 20 records
        location = record['location']
        hour = str(record['hour'])
        vehicle_count = record['vehicle_count']
        
        if location in baselines and hour in baselines[location]['vehicle_count']:
            baseline_mean = baselines[location]['vehicle_count'][hour]['mean']
            
            if baseline_mean > 0:
                deviation_pct = ((vehicle_count - baseline_mean) / baseline_mean) * 100
                
                if abs(deviation_pct) > 30:
                    severity = "high" if abs(deviation_pct) > 50 else "medium"
                    anomalies.append({
                        'timestamp': record['timestamp'],
                        'location': location,
                        'severity': severity,
                        'vehicle_count': vehicle_count,
                        'baseline': round(baseline_mean, 1),
                        'deviation_pct': round(deviation_pct, 1),
                        'description': f"Traffic {'spike' if deviation_pct > 0 else 'drop'} of {abs(round(deviation_pct))}% detected"
                    })
    
    # Format input for LangFlow
    summary_stats = payload.get('summary_stats', {})
    locations = payload.get('locations', [])
    
    langflow_input_text = f"""
TRAFFIC ANALYSIS DATA

Dataset Summary:
- Total Records: {summary_stats.get('total_records', 0)}
- Locations: {', '.join(locations)}
- Average Vehicle Count: {summary_stats.get('avg_vehicle_count', 0):.0f}
- Average Speed: {summary_stats.get('avg_speed', 0):.1f} km/h
- Peak Traffic Hour: {summary_stats.get('peak_hour_traffic', 'N/A')}

Detected Anomalies ({len(anomalies)} total):
"""
    
    if anomalies:
        for i, a in enumerate(anomalies[:10], 1):
            langflow_input_text += f"\n{i}. {a['timestamp']} at {a['location']}: {abs(a['deviation_pct'])}% deviation ({a['severity']} severity)"
    else:
        langflow_input_text += "\nNo significant anomalies detected. Traffic patterns within normal ranges."
    
    # Try different request formats for different LangFlow versions
    request_formats = [
        # Format 1: Standard LangFlow chat format
        {
            "input_value": langflow_input_text,
            "output_type": "chat",
            "input_type": "chat",
        },
        # Format 2: Simple message format
        {
            "message": langflow_input_text
        },
        # Format 3: Direct input format
        {
            "input": langflow_input_text
        },
        # Format 4: Inputs object format
        {
            "inputs": {
                "input": langflow_input_text
            }
        }
    ]
    
    for attempt in range(MAX_RETRIES):
        for format_idx, request_body in enumerate(request_formats, 1):
            try:
                print(f"📤 Attempt {attempt + 1}/{MAX_RETRIES}, Format {format_idx}/{len(request_formats)}")
                print(f"   Request keys: {list(request_body.keys())}")
                
                # Build headers with API key
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
                
                # Add API key to headers if available
                if LANGFLOW_API_KEY:
                    headers['Authorization'] = f'Bearer {LANGFLOW_API_KEY}'
                
                response = requests.post(
                    LANGFLOW_API_URL,
                    json=request_body,
                    timeout=TIMEOUT,
                    headers=headers
                )
                
                print(f"📥 Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ LangFlow SUCCESS! Response structure: {list(result.keys())}")
                    
                    # Parse response - try multiple extraction methods
                    output_text = None
                    
                    try:
                        # Method 1: Standard LangFlow outputs structure
                        if 'outputs' in result and isinstance(result['outputs'], list):
                            if len(result['outputs']) > 0:
                                first_output = result['outputs'][0]
                                if 'outputs' in first_output and isinstance(first_output['outputs'], list):
                                    if len(first_output['outputs']) > 0:
                                        output_obj = first_output['outputs'][0]
                                        if 'results' in output_obj:
                                            results = output_obj['results']
                                            if 'message' in results:
                                                output_text = results['message'].get('text', '')
                        
                        # Method 2: Direct result field
                        if not output_text and 'result' in result:
                            output_text = result['result']
                        
                        # Method 3: Direct output field
                        if not output_text and 'output' in result:
                            output_text = result['output']
                        
                        # Method 4: Direct text field
                        if not output_text and 'text' in result:
                            output_text = result['text']
                        
                        # Method 5: Message field
                        if not output_text and 'message' in result:
                            if isinstance(result['message'], dict):
                                output_text = result['message'].get('text', str(result['message']))
                            else:
                                output_text = str(result['message'])
                        
                        if output_text:
                            print(f"📝 LangFlow output extracted ({len(output_text)} chars)")
                            print(f"   Preview: {output_text[:150]}...")
                            
                            # Try to parse JSON from Granite response
                            json_match = re.search(r'\{[^{}]*"summary"[^{}]*"recommendations"[^{}]*\}', output_text, re.DOTALL)
                            if not json_match:
                                # Try broader JSON match
                                json_match = re.search(r'\{.*?\}', output_text, re.DOTALL)
                            
                            if json_match:
                                try:
                                    insights = json.loads(json_match.group(0))
                                    print(f"✅ Parsed JSON insights: {list(insights.keys())}")
                                    
                                    return {
                                        "status": "success",
                                        "agent_results": {
                                            "pattern_detection": {
                                                "total_patterns": len(anomalies),
                                                "locations_affected": len(set(a['location'] for a in anomalies))
                                            },
                                            "anomaly_detection": {
                                                "anomalies": anomalies[:10],
                                                "total_count": len(anomalies),
                                                "severity_breakdown": {
                                                    "high": sum(1 for a in anomalies if a['severity'] == 'high'),
                                                    "medium": sum(1 for a in anomalies if a['severity'] == 'medium')
                                                }
                                            },
                                            "insights_generation": {
                                                "summary": insights.get("summary", output_text[:500]),
                                                "recommendations": insights.get("recommendations", ["See summary for details"]),
                                                "confidence": "high"
                                            }
                                        },
                                        "processing_time_ms": 1500,
                                        "model_used": "ibm-granite-langflow"
                                    }
                                except json.JSONDecodeError as e:
                                    print(f"⚠️  JSON parse error: {e}")
                                    # Fall through to text-based response
                            
                            # If JSON parsing failed, use text directly
                            print("ℹ️  Using text output directly (no JSON found)")
                            return {
                                "status": "success",
                                "agent_results": {
                                    "pattern_detection": {
                                        "total_patterns": len(anomalies),
                                        "locations_affected": len(set(a['location'] for a in anomalies))
                                    },
                                    "anomaly_detection": {
                                        "anomalies": anomalies[:10],
                                        "total_count": len(anomalies),
                                        "severity_breakdown": {
                                            "high": sum(1 for a in anomalies if a['severity'] == 'high'),
                                            "medium": sum(1 for a in anomalies if a['severity'] == 'medium')
                                        }
                                    },
                                    "insights_generation": {
                                        "summary": output_text[:1000],
                                        "recommendations": [
                                            "Review the detailed analysis above",
                                            "Monitor high-severity anomaly locations",
                                            "Consider signal timing optimization"
                                        ],
                                        "confidence": "medium"
                                    }
                                },
                                "processing_time_ms": 1500,
                                "model_used": "ibm-granite-langflow"
                            }
                        else:
                            print(f"⚠️  Could not extract output from response")
                            print(f"   Response structure: {json.dumps(result, indent=2)[:500]}")
                    
                    except Exception as parse_error:
                        print(f"❌ Error parsing LangFlow response: {parse_error}")
                        print(f"   Raw response: {str(result)[:500]}")
                
                elif response.status_code == 403:
                    print(f"❌ 403 Forbidden - API key authentication failed")
                    print(f"   Check LANGFLOW_API_KEY in .env file")
                    if not LANGFLOW_API_KEY:
                        print(f"   ⚠️  No API key provided!")
                    # Don't retry other formats if auth failed
                    break
                
                elif response.status_code == 404:
                    print(f"❌ 404 Not Found - Check flow URL")
                    print(f"   URL: {LANGFLOW_API_URL}")
                    # Don't retry other formats if endpoint not found
                    break
                
                else:
                    print(f"❌ LangFlow error: Status {response.status_code}")
                    print(f"   Response: {response.text[:500]}")
                    
            except requests.exceptions.Timeout:
                print(f"⏱️  LangFlow timeout")
            except requests.exceptions.ConnectionError:
                print(f"🔌 Cannot connect to LangFlow")
                print(f"   URL: {LANGFLOW_API_URL}")
                print(f"   Make sure LangFlow is running!")
                # Don't retry formats if can't connect
                break
            except Exception as e:
                print(f"❌ LangFlow request error: {str(e)}")
        
        # Wait before retry
        if attempt < MAX_RETRIES - 1:
            print(f"⏳ Waiting {RETRY_DELAY}s before retry...")
            time.sleep(RETRY_DELAY)
    
    # All attempts failed, use mock
    print("=" * 60)
    print("⚠️  ALL LANGFLOW ATTEMPTS FAILED - Using mock response")
    print("=" * 60)
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
            
            if baseline_mean > 0:
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