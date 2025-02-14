import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

# Directory paths
DATASET_DIR = "dataset/processed"
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# Define hyperparameters
TIME_STEPS = 30  # Number of past days to use for prediction
EPOCHS = 50
BATCH_SIZE = 32

# ✅ Function to Load Data
def load_data(city):
    train_file = os.path.join(DATASET_DIR, f"{city}_train.csv")
    val_file = os.path.join(DATASET_DIR, f"{city}_val.csv")
    scaler_file = os.path.join(DATASET_DIR, f"{city}_scaler.pkl")

    if not os.path.exists(train_file) or not os.path.exists(val_file):
        print(f"🚨 Missing data for {city}. Skipping training.")
        return None, None, None, None, None

    # Load train and validation data
    train_df = pd.read_csv(train_file)
    val_df = pd.read_csv(val_file)

    # Load pre-fitted scaler
    scaler = joblib.load(scaler_file)

    return train_df, val_df, scaler

# ✅ Function to Prepare Data for LSTM
def prepare_data(df, scaler):
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")  # Ensure sorted order
    data = df["normalized_temp"].values.reshape(-1, 1)

    # Create sequences
    X, y = [], []
    for i in range(TIME_STEPS, len(data)):
        X.append(data[i - TIME_STEPS : i])  # Use past TIME_STEPS days
        y.append(data[i])  # Predict next day's temp

    X, y = np.array(X), np.array(y)

    # Debug: Check for NaNs
    if np.isnan(X).sum() > 0 or np.isnan(y).sum() > 0:
        print(f"🚨 NaN values detected! Fixing NaNs...")
        X = np.nan_to_num(X)
        y = np.nan_to_num(y)

    print(f"✅ Data prepared: {X.shape}, {y.shape}")
    return X, y

# ✅ Function to Build LSTM Model
def build_model():
    model = Sequential([
        LSTM(50, return_sequences=True, input_shape=(TIME_STEPS, 1)),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25, activation="relu"),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")
    return model

# ✅ Train and Evaluate Model for Each City
cities = ["Chicago", "Los Angeles", "New York", "Houston", "Phoenix",
          "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]

for city in cities:
    print(f"\n🚀 Training model for {city}...")

    # Load and prepare data
    train_df, val_df, scaler = load_data(city)
    if train_df is None:
        continue

    X_train, y_train = prepare_data(train_df, scaler)
    X_val, y_val = prepare_data(val_df, scaler)

    # Ensure 3D shape for LSTM
    X_train = X_train.reshape(X_train.shape[0], X_train.shape[1], 1)
    X_val = X_val.reshape(X_val.shape[0], X_val.shape[1], 1)

    # Debug: Check shape
    print(f"📊 X_train shape: {X_train.shape}, X_val shape: {X_val.shape}")

    # Ensure validation data is available
    if X_val.shape[0] == 0 or y_val.shape[0] == 0:
        print(f"⚠️ No validation data available for {city}. Skipping validation.")
        validation_data = None
    else:
        validation_data = (X_val, y_val)

    # Build model
    model = build_model()

    # Train model
    history = model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=validation_data if validation_data else None,
        verbose=1
    )

    # Save trained model
    model_path = os.path.join(MODEL_DIR, f"{city}_lstm.h5")
    model.save(model_path)
    print(f"✅ Model saved for {city}: {model_path}")

print("\n🎯 Training Completed for All Cities!")
