#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

import requests
import pandas as pd

from src.api.api import Api


class WeatherApi(Api):
    url = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self):
        ...

    def fetch(self, params):
        r = requests.get(self.url, params)
        return r.json()

    def get_dataframe(self, params):
        data = self.fetch(params)
        df = pd.DataFrame(data["hourly"])
        # df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%d")
        df["time"] = pd.to_datetime(df["time"], format="ISO8601")
        df.set_index("time", inplace=True)
        return df


if __name__ == "__main__":
    api: Api = WeatherApi()  # Don't forget to add src/ directory to $PYTHONPATH
    params = {
        "latitude": 52.52,
        "longitude": 13.41,
        "start_date": "2023-11-23",
        "end_date": "2023-11-24",
        "hourly": ["wind_speed_100m", "wind_direction_100m"]
    }
    data = api.fetch(params)
    print(data)
