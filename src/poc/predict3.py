#! /usr/bin/python3
import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

import requests
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor

from src.api.api import Api
from src.api.pollution_api import PollutionApi
from src.api.weather_api import WeatherApi
from src.util.position_offsetter import PositionOffsetter


def get_wind_data(latitude, longitude, start_date, end_date):
    api = WeatherApi()
    start_date = datetime.utcfromtimestamp(int(start_date) - 86400).strftime('%Y-%m-%d')
    end_date = datetime.utcfromtimestamp(int(end_date) - 86400).strftime('%Y-%m-%d')
    print(start_date, end_date)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": start_date,
        "hourly": ["wind_speed_100m", "wind_direction_100m"]
    }
    data = api.fetch(params)
    print(data)
    wind_data = data["hourly"]
    wind_speed = wind_data["wind_speed_100m"]
    wind_direction = wind_data["wind_direction_100m"]
    return wind_speed, wind_direction


def get_data(lat, lon, start, end, appid):
    api = PollutionApi()
    params = {
        "lat": lat,
        "lon": lon,
        "start": start,
        "end": end,
        "appid": appid,
    }
    data = api.fetch(params)
    df = pd.DataFrame(data["list"])
    df["dt"] = pd.to_datetime(df["dt"], unit="s")
    df.set_index("dt", inplace=True)
    df = df[["main", "components"]]
    df = pd.concat([df.drop(["main"], axis=1), df["main"].apply(pd.Series)], axis=1)
    df = pd.concat([df.drop(["components"], axis=1), df["components"].apply(pd.Series)], axis=1)
    return df


def train_knn_model(df, n_neighbors):
    X = df.drop(["aqi"], axis=1)
    y = df["aqi"]
    knn = KNeighborsRegressor(n_neighbors=n_neighbors)
    knn.fit(X, y)
    return knn


if __name__ == "__main__":
    lat = 45.185992
    lon = 5.734384
    start = "1637664000"
    end = "1637750400"
    appid = "3f4dd805354d2b0a8aaf79250d2b44fe"
    n_neighbors = 5

    # Get pollution data
    df = get_data(lat, lon, start, end, appid)

    # Get wind data
    wind_speed, wind_direction = get_wind_data(lat, lon, start, end)

    # Get offsetted position
    offsetter = PositionOffsetter(lat, lon)
    offsetter.offset(wind_speed[0], wind_direction[0], 1)
    offsetted_latitude, offsetted_longitude = offsetter.lat, offsetter.lon
    print(wind_speed[0], wind_direction[0])
    print(offsetted_latitude, offsetted_longitude)

    # Get pollution data for offsetted position
    offsetted_df = get_data(offsetted_latitude, offsetted_longitude, start, end, appid)

    # Combine pollution data for both positions
    combined_df = pd.concat([df, offsetted_df])

    # Train KNN model
    knn = train_knn_model(combined_df, n_neighbors)

    # Use the trained model to predict air quality at the given position
    # for the next 24 hours
    api = PollutionApi()
    params = {
        "lat": lat,
        "lon": lon,
        "start": end,
        "end": str(int(end) + 86400),
        "appid": appid,
    }
    future_data = api.fetch(params)
    future_df = pd.DataFrame(future_data["list"])
    future_df["dt"] = pd.to_datetime(future_df["dt"], unit="s")
    future_df.set_index("dt", inplace=True)
    future_df = future_df[["main", "components"]]
    future_df = pd.concat([future_df.drop(["main"], axis=1), future_df["main"].apply(pd.Series)], axis=1)
    future_df = pd.concat([future_df.drop(["components"], axis=1), future_df["components"].apply(pd.Series)], axis=1)
    future_X = future_df.drop(["aqi"], axis=1)
    future_y = knn.predict(future_X)

    print("timestamp", "prediction", "actual", sep="\t")
    for i in range(24):
        print(future_df.index[i], future_y[i], future_df["aqi"][i], sep="\t")
