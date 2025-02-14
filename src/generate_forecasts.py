import numpy as np
import pandas as pd
import tensorflow as tf
import os
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
from config import DATASET_DIR, MODELS_DIR  # Ensure these point to correct locations
import tensorflow.keras.losses
# Set directories
PROCESSED_DIR = os.path.join(DATASET_DIR, "processed")  # Updated path
MODELS_DIR = os.path.join("src", "models")  # Updated path

# Load trained models & scalers
cities = ["Chicago", "Los Angeles", "New York", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]
TIME_STEPS = 30  # Number of previous days used for prediction

def load_model_and_scaler(city):
    """Load trained LSTM model and corresponding scaler."""
    model_path = os.path.join(MODELS_DIR, f"{city}_lstm.h5")
    scaler_path = os.path.join(PROCESSED_DIR, f"{city}_scaler.pkl")

    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        print(f"🚨 Missing model or scaler for {city}. Skipping.")
        return None, None

    # ✅ Load model with custom loss function mapping
    model = tf.keras.models.load_model(model_path, custom_objects={"mse": tensorflow.keras.losses.MeanSquaredError()})
    
    # ✅ Load corresponding scaler
    scaler = pd.read_pickle(scaler_path)

    return model, scaler

def forecast_next_30_days(city):
    """Generate future forecasts for the next 30 days using LSTM."""
    model, scaler = load_model_and_scaler(city)
    if model is None or scaler is None:
        return None

    # Load latest training data
    train_file = os.path.join(PROCESSED_DIR, f"{city}_train.csv")
    if not os.path.exists(train_file):
        print(f"🚨 Missing training data for {city}. Skipping.")
        return None

    df = pd.read_csv(train_file)
    last_30_days = df["normalized_temp"].values[-TIME_STEPS:]  # Get last 30 normalized values

    # Prepare input for prediction
    input_seq = np.array(last_30_days).reshape(1, TIME_STEPS, 1)

    # Generate predictions
    predictions = []
    for _ in range(30):  # Predict next 30 days
        next_pred = model.predict(input_seq)
        predictions.append(next_pred[0, 0])

        # Update sequence with the new prediction
        input_seq = np.roll(input_seq, -1, axis=1)
        input_seq[0, -1, 0] = next_pred

    # Convert back to actual temperature values
    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

    # Generate future dates
    start_date = datetime.today()
    forecast_dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 31)]

    # Save results
    forecast_df = pd.DataFrame({"date": forecast_dates, "forecast_temp": predictions})
    forecast_file = os.path.join(PROCESSED_DIR, f"{city}_forecast.csv")
    forecast_df.to_csv(forecast_file, index=False)
    print(f"✅ Forecast saved for {city}: {forecast_file}")

    return forecast_df

# Run for all cities
for city in cities:
    print(f"🔮 Forecasting for {city}...")
    forecast_next_30_days(city)
