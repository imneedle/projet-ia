#! /usr/bin/python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

import requests
import pandas as pd

from src.api.api import Api


class PollutionApi(Api):
    url = "http://api.openweathermap.org/data/2.5/air_pollution/history"

    def __init__(self):
        ...

    def fetch(self, params):
        r = requests.get(self.url, params)
        return r.json()

    def get_dataframe(self, params):
        data = self.fetch(params)
        df = pd.DataFrame(data["list"])
        df["dt"] = pd.to_datetime(df["dt"], unit="s")
        df.set_index("dt", inplace=True)
        df = df[["main", "components"]]
        df = pd.concat([df.drop(["main"], axis=1), df["main"].apply(pd.Series)], axis=1)
        df = pd.concat([df.drop(["components"], axis=1), df["components"].apply(pd.Series)], axis=1)
        return df


if __name__ == "__main__":
    api: Api = PollutionApi()  # Don't forget to add src/ directory to $PYTHONPATH
    params = {
        "lat": "45.1",
        "lon": "5.6",
        "start": "1606488670",
        "end": "1606747870",
        "appid": "3f4dd805354d2b0a8aaf79250d2b44fe",
    }
    data = api.fetch(params)
    print(data)
