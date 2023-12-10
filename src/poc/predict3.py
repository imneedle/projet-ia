#!/usr/bin/env python3
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


def get_weather_data(latitude, longitude, start_date, end_date):
    api = WeatherApi()
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": datetime.utcfromtimestamp(int(start_date)+3600).strftime('%Y-%m-%d'),
        "end_date": datetime.utcfromtimestamp(int(end_date)).strftime('%Y-%m-%d'),
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "dewpoint_2m", "wind_speed_10m", "wind_direction_10m"]
    }
    data = api.fetch(params)
    df = pd.DataFrame(data["hourly"])
    # df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%d")
    df["time"] = pd.to_datetime(df["time"], format="ISO8601")
    df.set_index("time", inplace=True)
    return df


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
    y = df["aqi"]
    X = df.drop(["aqi"], axis=1)
    X.to_csv("X.csv")
    knn = KNeighborsRegressor(n_neighbors=n_neighbors)
    knn.fit(X, y)
    return knn


if __name__ == "__main__":
    lat = 45.185992
    lon = 5.734384
    start = "1637624400"
    end = "1640130000"
    appid = "3f4dd805354d2b0a8aaf79250d2b44fe"
    n_neighbors = 5

    # Get pollution data
    df = get_weather_data(lat, lon, start, end)

    poll_df = get_data(lat, lon, start, end, appid)
    poll_df = poll_df["aqi"]
    df = pd.concat([df, poll_df], axis=1)
    print(df)

    # Get wind data
    wind_speed, wind_direction = get_wind_data(lat, lon, start, end)

    # Get offsetted position
    offsetter = PositionOffsetter(lat, lon)
    offsetter.offset(wind_speed[0], wind_direction[0], 0.5)
    offsetted_latitude, offsetted_longitude = offsetter.lat, offsetter.lon

    # Get pollution data for offsetted position
    offsetted_df = get_data(offsetted_latitude, offsetted_longitude, start, end, appid)
    offsetted_df = offsetted_df.rename(columns=(lambda a: "24h-" + a))

    # Combine pollution data for both positions
    combined_df = pd.concat([df, offsetted_df], axis=1)
    combined_df.to_csv("combined.csv")

    # Train KNN model
    knn = train_knn_model(combined_df, n_neighbors)

    # Use the trained model to predict air quality at the given position
    # for the next 24 hours
    future_df = get_weather_data(lat, lon, end, str(int(end) + 86400))

    future_ws, future_wd = get_wind_data(lat, lon, end, str(int(end) + 86400))
    future_offsetter = PositionOffsetter(lat, lon)
    future_offsetter.offset(future_ws[0], future_wd[0], 0.5)
    future_offsetted_latitude, future_offsetted_longitude = future_offsetter.lat, future_offsetter.lon
    future_offsetted_df = get_data(future_offsetted_latitude, future_offsetted_longitude, end, str(int(end) + 86400), appid)
    future_offsetted_df = future_offsetted_df.rename(columns=(lambda a: "24h-" + a))

    future_combined_df = pd.concat([future_df, future_offsetted_df], axis=1)

    future_y = knn.predict(future_combined_df)
    actual_y = get_data(lat, lon, end, str(int(end) + 86400), appid)["aqi"].to_numpy()

    print("timestamp", "prediction", "actual", sep="\t")
    for i in range(24):
        print(future_df.index[i], future_y[i], actual_y[i], sep="\t")
