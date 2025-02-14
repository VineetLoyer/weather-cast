import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os
import pickle  # Changed from joblib to pickle
from datetime import datetime
# Set directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
PROCESSED_DIR = os.path.join(DATASET_DIR, "processed")
HISTORICAL_DIR = os.path.join(BASE_DIR, "historical_data")

# Create processed directory if it doesn't exist
os.makedirs(PROCESSED_DIR, exist_ok=True)

cities = ["Chicago", "Los Angeles", "New York", "Houston", "Phoenix",
          "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]

def convert_date(date_str):
    """Convert YYYYMMDD to YYYY-MM-DD format"""
    return datetime.strptime(str(int(date_str)), '%Y%m%d').strftime('%Y-%m-%d')

def create_scalers():
    """Create and save scalers for each city using historical data"""
    for city in cities:
        try:
            print(f"Creating scaler for {city}...")
            
            # Load historical data
            csv_path = os.path.join(HISTORICAL_DIR, f"{city}.csv")
            df = pd.read_csv(csv_path)
            
            if not df.empty:
                # Convert date format
                df['date'] = df['date'].apply(convert_date)
                
                # Calculate average temperature from min and max
                df['temperature'] = (df['min'] + df['max']) / 2
                
                # Sort by date
                df = df.sort_values('date')
                
                # Create and fit scaler on temperature data
                scaler = MinMaxScaler(feature_range=(0, 1))
                scaler.fit(df[['temperature']].values.reshape(-1, 1))
                
                # Save scaler using pickle
                scaler_path = os.path.join(PROCESSED_DIR, f"{city}_scaler.pkl")
                with open(scaler_path, 'wb') as f:
                    pickle.dump(scaler, f)
                print(f"✅ Saved scaler for {city}")
                
                # Create and save normalized training data
                normalized_temp = scaler.transform(df[['temperature']].values.reshape(-1, 1))
                train_df = pd.DataFrame({
                    'date': df['date'],
                    'temperature': df['temperature'],
                    'normalized_temp': normalized_temp.flatten()
                })
                train_path = os.path.join(PROCESSED_DIR, f"{city}_train.csv")
                train_df.to_csv(train_path, index=False)
                print(f"✅ Saved training data for {city}")
                print(f"Data range: {df['date'].min()} to {df['date'].max()}")
            else:
                print(f"⚠️ No data found for {city}")

        except Exception as e:
            print(f"❌ Error processing {city}: {e}")
            print(f"File path attempted: {csv_path}")

if __name__ == "__main__":
    print(f"Looking for historical data in: {HISTORICAL_DIR}")
    print(f"Saving processed files to: {PROCESSED_DIR}")
    create_scalers()