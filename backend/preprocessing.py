import pandas as pd
import numpy as np
from typing import Dict, List, Any

REQUIRED_COLUMNS = ['timestamp', 'location_id', 'vehicle_count', 'avg_speed_kmh']

def validate_csv(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate CSV format and required columns
    """
    errors = []
    
    # Check if DataFrame is empty
    if df.empty:
        errors.append("CSV file is empty")
        return {"valid": False, "errors": errors}
    
    # Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
    
    # Check data types
    if 'vehicle_count' in df.columns:
        if not pd.api.types.is_numeric_dtype(df['vehicle_count']):
            errors.append("Column 'vehicle_count' must be numeric")
    
    if 'avg_speed_kmh' in df.columns:
        if not pd.api.types.is_numeric_dtype(df['avg_speed_kmh']):
            errors.append("Column 'avg_speed_kmh' must be numeric")
    
    # Check for minimum records
    if len(df) < 10:
        errors.append("CSV must contain at least 10 records for analysis")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors if errors else None
    }

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare data for analysis
    - Convert timestamps
    - Handle missing values
    - Remove outliers
    - Sort by timestamp
    """
    cleaned_df = df.copy()
    
    # Convert timestamp to datetime
    cleaned_df['timestamp'] = pd.to_datetime(cleaned_df['timestamp'])
    
    # Sort by timestamp and location
    cleaned_df = cleaned_df.sort_values(['location_id', 'timestamp'])
    
    # Handle missing values
    cleaned_df['vehicle_count'] = cleaned_df.groupby('location_id')['vehicle_count'].fillna(method='ffill')
    cleaned_df['avg_speed_kmh'] = cleaned_df.groupby('location_id')['avg_speed_kmh'].fillna(method='ffill')
    
    # Fill any remaining NaNs with location median
    for col in ['vehicle_count', 'avg_speed_kmh']:
        cleaned_df[col] = cleaned_df.groupby('location_id')[col].transform(
            lambda x: x.fillna(x.median())
        )
    
    # Remove extreme outliers using IQR method
    for location in cleaned_df['location_id'].unique():
        mask = cleaned_df['location_id'] == location
        
        for col in ['vehicle_count', 'avg_speed_kmh']:
            Q1 = cleaned_df.loc[mask, col].quantile(0.25)
            Q3 = cleaned_df.loc[mask, col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR
            
            # Cap outliers instead of removing
            cleaned_df.loc[mask, col] = cleaned_df.loc[mask, col].clip(lower_bound, upper_bound)
    
    # Add derived features
    cleaned_df['hour'] = cleaned_df['timestamp'].dt.hour
    cleaned_df['day_of_week'] = cleaned_df['timestamp'].dt.dayofweek
    cleaned_df['date'] = cleaned_df['timestamp'].dt.date
    
    return cleaned_df

def calculate_baselines(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate hourly baselines per location
    Returns mean, std dev, min, max for each location-hour combination
    """
    baselines = {}
    
    for location in df['location_id'].unique():
        location_data = df[df['location_id'] == location]
        
        hourly_stats = location_data.groupby('hour').agg({
            'vehicle_count': ['mean', 'std', 'min', 'max'],
            'avg_speed_kmh': ['mean', 'std', 'min', 'max']
        }).round(2)
        
        baselines[location] = {
            'vehicle_count': {
                str(hour): {
                    'mean': float(hourly_stats.loc[hour, ('vehicle_count', 'mean')]),
                    'std': float(hourly_stats.loc[hour, ('vehicle_count', 'std')]) if not pd.isna(hourly_stats.loc[hour, ('vehicle_count', 'std')]) else 0,
                    'min': float(hourly_stats.loc[hour, ('vehicle_count', 'min')]),
                    'max': float(hourly_stats.loc[hour, ('vehicle_count', 'max')])
                }
                for hour in hourly_stats.index
            },
            'avg_speed': {
                str(hour): {
                    'mean': float(hourly_stats.loc[hour, ('avg_speed_kmh', 'mean')]),
                    'std': float(hourly_stats.loc[hour, ('avg_speed_kmh', 'std')]) if not pd.isna(hourly_stats.loc[hour, ('avg_speed_kmh', 'std')]) else 0,
                    'min': float(hourly_stats.loc[hour, ('avg_speed_kmh', 'min')]),
                    'max': float(hourly_stats.loc[hour, ('avg_speed_kmh', 'max')])
                }
                for hour in hourly_stats.index
            }
        }
    
    return baselines

def prepare_langflow_payload(df: pd.DataFrame, baselines: Dict) -> Dict[str, Any]:
    """
    Prepare structured payload for LangFlow agents
    """
    # Get summary statistics
    summary_stats = {
        'total_records': len(df),
        'unique_locations': df['location_id'].nunique(),
        'time_span_hours': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600,
        'avg_vehicle_count': float(df['vehicle_count'].mean()),
        'avg_speed': float(df['avg_speed_kmh'].mean()),
        'peak_hour_traffic': int(df.groupby('hour')['vehicle_count'].mean().idxmax()),
        'lowest_hour_traffic': int(df.groupby('hour')['vehicle_count'].mean().idxmin())
    }
    
    # Prepare time series data
    time_series = []
    for _, row in df.iterrows():
        time_series.append({
            'timestamp': row['timestamp'].isoformat(),
            'location': row['location_id'],
            'vehicle_count': int(row['vehicle_count']),
            'avg_speed': float(row['avg_speed_kmh']),
            'hour': int(row['hour']),
            'day_of_week': int(row['day_of_week'])
        })
    
    payload = {
        'raw_data': time_series[:100],  # Limit to first 100 for LangFlow processing
        'baselines': baselines,
        'summary_stats': summary_stats,
        'time_range': {
            'start': df['timestamp'].min().isoformat(),
            'end': df['timestamp'].max().isoformat()
        },
        'locations': df['location_id'].unique().tolist(),
        'analysis_request': 'Detect traffic anomalies and provide insights'
    }
    
    return payload