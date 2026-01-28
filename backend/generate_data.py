import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_traffic_data(
    start_date='2024-01-22',
    num_days=7,
    locations=['LOC_01', 'LOC_02', 'LOC_03'],
    anomaly_rate=0.08
):
    """
    Generate realistic synthetic traffic data with anomalies
    
    Parameters:
    - start_date: Starting date for data generation
    - num_days: Number of days to generate
    - locations: List of location IDs
    - anomaly_rate: Probability of anomaly occurrence (0.08 = 8%)
    """
    
    np.random.seed(42)
    random.seed(42)
    
    # Generate hourly timestamps
    # NOTE: Pandas 3.x uses lowercase offset aliases (use 'h' instead of deprecated/invalid 'H')
    dates = pd.date_range(start_date, periods=num_days * 24, freq='h')
    
    data = []
    
    for loc in locations:
        # Each location has slightly different baseline patterns
        location_factor = random.uniform(0.8, 1.2)
        
        for date in dates:
            hour = date.hour
            day_of_week = date.weekday()
            
            # Define traffic patterns by hour
            if 7 <= hour <= 9:  # Morning peak
                base_count = int(420 * location_factor)
                base_speed = 24
            elif 12 <= hour <= 13:  # Lunch hour
                base_count = int(280 * location_factor)
                base_speed = 38
            elif 17 <= hour <= 19:  # Evening peak
                base_count = int(480 * location_factor)
                base_speed = 20
            elif 0 <= hour <= 5:  # Late night
                base_count = int(60 * location_factor)
                base_speed = 65
            else:  # Off-peak
                base_count = int(180 * location_factor)
                base_speed = 52
            
            # Weekend adjustment (less traffic)
            if day_of_week >= 5:  # Saturday, Sunday
                base_count = int(base_count * 0.6)
                base_speed = int(base_speed * 1.15)
            
            # Add natural variation
            count_variation = np.random.randint(-40, 50)
            speed_variation = np.random.randint(-6, 8)
            
            vehicle_count = base_count + count_variation
            avg_speed = base_speed + speed_variation
            
            # Inject anomalies
            is_anomaly = np.random.random() < anomaly_rate
            anomaly_type = None
            
            if is_anomaly:
                anomaly_type = random.choice(['incident', 'event', 'weather'])
                
                if anomaly_type == 'incident':
                    # Traffic incident: high count, low speed
                    vehicle_count = int(vehicle_count * random.uniform(1.4, 1.8))
                    avg_speed = int(avg_speed * random.uniform(0.4, 0.6))
                    
                elif anomaly_type == 'event':
                    # Special event: very high count, moderate speed
                    vehicle_count = int(vehicle_count * random.uniform(1.6, 2.0))
                    avg_speed = int(avg_speed * random.uniform(0.7, 0.85))
                    
                elif anomaly_type == 'weather':
                    # Bad weather: moderate increase, slow speed
                    vehicle_count = int(vehicle_count * random.uniform(1.2, 1.4))
                    avg_speed = int(avg_speed * random.uniform(0.6, 0.75))
            
            # Ensure realistic bounds
            vehicle_count = max(10, min(vehicle_count, 1000))
            avg_speed = max(5, min(avg_speed, 80))
            
            data.append({
                'timestamp': date.strftime('%Y-%m-%d %H:%M:%S'),
                'location_id': loc,
                'vehicle_count': int(vehicle_count),
                'avg_speed_kmh': int(avg_speed)
            })
    
    df = pd.DataFrame(data)
    return df

def generate_multiple_scenarios():
    """Generate different traffic scenarios for comprehensive testing"""
    
    scenarios = {
        'normal_week': {
            'num_days': 7,
            'anomaly_rate': 0.05,
            'description': 'Normal week with few anomalies'
        },
        'high_congestion': {
            'num_days': 3,
            'anomaly_rate': 0.15,
            'description': 'High congestion period with many incidents'
        },
        'extended_period': {
            'num_days': 14,
            'anomaly_rate': 0.08,
            'description': 'Two weeks of data for pattern analysis'
        }
    }
    
    for scenario_name, config in scenarios.items():
        df = generate_traffic_data(
            num_days=config['num_days'],
            anomaly_rate=config['anomaly_rate']
        )
        
        filename = f"sample_data_{scenario_name}.csv"
        df.to_csv(filename, index=False)
        
        print(f"Generated: {filename}")
        print(f"Description: {config['description']}")
        print(f"Records: {len(df)}")
        print(f"Locations: {df['location_id'].nunique()}")
        print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print()

def print_data_summary(filename):
    """Print summary statistics of generated data"""
    df = pd.read_csv(filename)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    print(f"\nSummary for {filename}:")
    print("=" * 60)
    print(f"Total records: {len(df)}")
    print(f"Locations: {df['location_id'].unique().tolist()}")
    print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"\nVehicle Count Statistics:")
    print(df['vehicle_count'].describe())
    print(f"\nAverage Speed Statistics:")
    print(df['avg_speed_kmh'].describe())
    print("=" * 60)

if __name__ == "__main__":
    print("Traffic Pattern Detective - Data Generator")
    print("=" * 60)
    print()
    
    # Generate main sample data (default)
    print("Generating default sample data...")
    df_main = generate_traffic_data()
    df_main.to_csv('sample_data.csv', index=False)
    print("Generated: sample_data.csv")
    print(f"Records: {len(df_main)}")
    print(f"Locations: {df_main['location_id'].nunique()}")
    print()
    
    # Generate additional scenarios
    print("Generating additional test scenarios...")
    print()
    generate_multiple_scenarios()
    
    # Print summary
    print_data_summary('sample_data.csv')
    
    print("\nAll data files generated successfully!")
    print("\nFiles created:")
    print("  1. sample_data.csv - Default 7-day dataset")
    print("  2. sample_data_normal_week.csv - Low anomaly rate")
    print("  3. sample_data_high_congestion.csv - High anomaly rate")
    print("  4. sample_data_extended_period.csv - 14 days of data")
    print("\nYou can now upload these files to test your application!")