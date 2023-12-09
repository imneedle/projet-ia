#! /usr/bin/python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

import requests
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error
from datetime import datetime, timedelta

from src.api.api import Api
from src.api.pollution_api import PollutionApi


def process_data(data):
    features = ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']
    X = [[entry['components'][feature] for feature in features]
         for entry in data['list']]
    y = [entry['main']['aqi'] for entry in data['list']]
    return X, y


def train_knn_model(X_train, y_train):
    # Normalize the data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # Create and train the KNN model
    knn_model = KNeighborsRegressor(n_neighbors=5)
    knn_model.fit(X_train_scaled, y_train)

    return knn_model, scaler


def predict_future_air_quality(model, scaler, current_data_point, time_intervals):
    current_features = [current_data_point['components'][feature]
                        for feature in ['co', 'no', 'no2', 'o3', 'so2', 'pm2_5', 'pm10', 'nh3']]
    normalized_features = scaler.transform([current_features])

    predictions = []
    for interval in time_intervals:
        future_timestamp = current_data_point['dt'] + interval * 3600  # Convert hours to seconds
        future_data_point = {'dt': future_timestamp, 'components': {'co': 0, 'no': 0, 'no2': 0, 'o3': 0, 'so2': 0, 'pm2_5': 0, 'pm10': 0, 'nh3': 0}}

        # Predict air quality for the future timestamp
        future_prediction = model.predict(normalized_features)[0]
        predictions.append({'timestamp': future_timestamp, 'prediction': future_prediction})

    return predictions


if __name__ == "__main__":
    api: Api = PollutionApi()
    params = {
        "lat": "45.19",
        "lon": "5.71",
        "start": "1606488670",
        "end": "1607093470",
        "appid": "3f4dd805354d2b0a8aaf79250d2b44fe",
    }
    data = api.fetch(params)

    # Process the data
    X, y = process_data(data)

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the KNN model
    knn_model, scaler = train_knn_model(X_train, y_train)

    # Make predictions for future air quality
    current_data_point = data['list'][0]  # Assuming the first data point in the list
    time_intervals = [1, 4, 8, 16, 24]  # Predictions for 1h, 4h, 8h, 16h, and 24h in the future
    future_predictions = predict_future_air_quality(knn_model, scaler, current_data_point, time_intervals)

    # Print future predictions
    for prediction in future_predictions:
        timestamp = datetime.utcfromtimestamp(prediction['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Prediction for {timestamp}: {prediction['prediction']}")
