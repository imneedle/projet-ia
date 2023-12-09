#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

import requests

from src.api.api import Api


class WeatherApi(Api):
    url = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self):
        ...

    def fetch(self, params):
        r = requests.get(self.url, params)
        return r.json()


if __name__ == "__main__":
    api: Api = WeatherApi()  # Don't forget to add src/ directory to $PYTHONPATH
    params = {
        "latitude": "45.18857814633678",
        "longitude": "5.718267792253707",
        "hourly": "relativehumidity_2m,dewpoint_2m,cloudcover_mid,windspeed_80m,winddirection_80m,temperature_80m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "Europe/London",
        "forecast_days": "1"
    }
    data = api.fetch(params)
    print(data)
