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
from src.model.knn import KnnModel


class PoC:
    @staticmethod
    def run():
        # Set position to Grenoble
        lat, lon = 45.185992, 5.734384
        training_days = 28
        start_date = 1637624400
        end_date = start_date + (training_days + 1) * 24 * 3600
        appid = "3f4dd805354d2b0a8aaf79250d2b44fe"

        # Init APIs
        pollution_api = PollutionApi()
        weather_api = WeatherApi()

        # Get weather data at position
        weather_df = weather_api.get_dataframe({
            "latitude": lat, "longitude": lon,
            "start_date": datetime.utcfromtimestamp(start_date + 3600).strftime('%Y-%m-%d'),
            "end_date": datetime.utcfromtimestamp(end_date).strftime('%Y-%m-%d'),
            "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "dewpoint_2m", "wind_speed_10m", "wind_direction_10m"],
        })

        # Get pollution data at position
        pollution_df = pollution_api.get_dataframe({
            "lat": lat, "lon": lon, "start":
            start_date, "end": end_date,
            "appid": appid
        })['aqi']

        # Combine the data
        df = pd.concat([weather_df, pollution_df], axis=1)

        # Get pollution data for offsetted wind position 24h before
        wind_df = weather_api.get_dataframe({
            "latitude": lat, "longitude": lon,
            "start_date": datetime.utcfromtimestamp(start_date - 86400).strftime('%Y-%m-%d'),
            "end_date": datetime.utcfromtimestamp(end_date - 86400).strftime('%Y-%m-%d'),
            "hourly": ["wind_speed_100m", "wind_direction_100m"],
        })
        wind_speed = wind_df['wind_speed_100m'][0]
        wind_direction = wind_df['wind_direction_100m'][0]

        offsetter = PositionOffsetter(lat, lon)
        offsetter.offset(wind_speed, wind_direction, .5)
        offsetted_lat, offsetted_lon = offsetter.lat, offsetter.lon

        offsetted_df = pollution_api.get_dataframe({
            "lat": offsetted_lat, "lon": offsetted_lon,
            "start": start_date, "end": end_date,
            "appid": appid
        })
        offsetted_df = offsetted_df.rename(columns=lambda a: f'24h-{a}')

        # Combine the data at position with the data at offsetted position
        combined_df = pd.concat([df, offsetted_df], axis=1)

        # Feed data and train KNN model
        knn_model = KnnModel(n_neighbors=5)
        knn = knn_model.train(combined_df)

        # Predict AQI for the next 24h
        future_df = weather_api.get_dataframe({
            "latitude": lat, "longitude": lon,
            "start_date": datetime.utcfromtimestamp(end_date + 3600).strftime('%Y-%m-%d'),
            "end_date": datetime.utcfromtimestamp(end_date + 86400).strftime('%Y-%m-%d'),
            "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "dewpoint_2m", "wind_speed_10m", "wind_direction_10m"]
        })

        future_wind_df = weather_api.get_dataframe({
            "latitude": lat, "longitude": lon,
            "start_date": datetime.utcfromtimestamp(start_date - 86400).strftime('%Y-%m-%d'),
            "end_date": datetime.utcfromtimestamp(end_date - 86400).strftime('%Y-%m-%d'),
            "hourly": ["wind_speed_100m", "wind_direction_100m"],
        })
        future_ws = future_wind_df['wind_speed_100m'][0]
        future_wd = future_wind_df['wind_direction_100m'][0]

        future_offsetter = PositionOffsetter(lat, lon)
        future_offsetter.offset(future_ws, future_wd, .5)
        future_offsetted_lat, future_offsetted_lon = future_offsetter.lat, future_offsetter.lon

        future_offsetted_df = pollution_api.get_dataframe({
            "lat": offsetted_lat, "lon": offsetted_lon,
            "start": end_date, "end": end_date + 86400,
            "appid": appid
        })
        future_offsetted_df = future_offsetted_df.rename(columns=lambda a: f'24h-{a}')

        future_combined_df = pd.concat([future_df, future_offsetted_df], axis=1)

        future_y = knn.predict(future_combined_df)
        actual_y = pollution_api.get_dataframe({
            "lat": offsetted_lat, "lon": offsetted_lon,
            "start": end_date, "end": end_date + 86400,
            "appid": appid
        })['aqi'].to_numpy()

        print("timestamp", "prediction", "actual", sep="\t")
        for i in range(24):
            print(future_df.index[i], future_y[i], actual_y[i], sep="\t")


if __name__ == '__main__':
    PoC.run()
