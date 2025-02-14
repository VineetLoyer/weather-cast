import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime, timedelta
import os
import pickle

# Set directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
PROCESSED_DIR = os.path.join(DATASET_DIR, "processed")

TIME_STEPS = 30

cities = ["Chicago", "Los Angeles", "New York", "Houston", "Phoenix",
          "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]

def load_model_and_scaler(city):
    """Load trained LSTM model and corresponding scaler."""
    try:
        model_path = os.path.join(MODELS_DIR, f"{city}_lstm.h5")
        scaler_path = os.path.join(PROCESSED_DIR, f"{city}_scaler.pkl")

        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            print(f"🚨 Missing model or scaler for {city}. Skipping.")
            return None, None

        # Load model
        model = tf.keras.models.load_model(model_path, 
            custom_objects={"mse": tf.keras.losses.MeanSquaredError()})
        
        # Load scaler
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
            
        print(f"✅ Successfully loaded model and scaler for {city}")
        return model, scaler
    except Exception as e:
        print(f"❌ Error loading model or scaler for {city}: {e}")
        return None, None

def forecast_next_30_days(city):
    """Generate future forecasts for the next 30 days using LSTM."""
    try:
        model, scaler = load_model_and_scaler(city)
        if model is None or scaler is None:
            return None

        # Load training data
        train_file = os.path.join(PROCESSED_DIR, f"{city}_train.csv")
        if not os.path.exists(train_file):
            print(f"🚨 Missing training data for {city}: {train_file}")
            return None

        # Read and prepare data
        df = pd.read_csv(train_file)
        last_sequence = df["normalized_temp"].values[-TIME_STEPS:]
        
        # Generate predictions
        current_sequence = last_sequence.reshape(1, TIME_STEPS, 1)
        predictions = []

        for _ in range(30):
            # Get the prediction
            next_pred = model.predict(current_sequence, verbose=0)
            predictions.append(next_pred[0, 0])
            
            # Update the sequence
            current_sequence = np.roll(current_sequence, -1)
            current_sequence[0, -1, 0] = next_pred[0, 0]

        # Convert predictions back to original scale
        predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1))

        # Generate future dates
        start_date = datetime.now()
        dates = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') 
                for i in range(1, 31)]

        # Create and save forecast DataFrame
        forecast_df = pd.DataFrame({
            'date': dates,
            'forecast_temp': predictions.flatten()
        })
        
        # Save forecast
        forecast_file = os.path.join(PROCESSED_DIR, f"{city}_forecast.csv")
        forecast_df.to_csv(forecast_file, index=False)
        print(f"✅ Generated and saved forecast for {city}")
        
        # Print first few predictions to verify
        print(f"First 5 predictions for {city}:")
        print(forecast_df.head())
        
        return forecast_df

    except Exception as e:
        print(f"❌ Error generating forecast for {city}: {e}")
        print(f"Stack trace:", e.__traceback__)
        return None

def main():
    print("🚀 Starting forecast generation...")
    for city in cities:
        print(f"\n🔮 Forecasting for {city}...")
        forecast_next_30_days(city)

if __name__ == "__main__":
    main()