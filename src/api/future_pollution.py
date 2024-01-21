#! /usr/bin/python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

import requests
import pandas as pd

from src.api.api import Api


class FuturePollutionApi(Api):
    url = "http://api.openweathermap.org/data/2.5/air_pollution/forecast"

    def __init__(self):
        ...

    def fetch(self, params):
        r = requests.get(self.url, params)
        return r.json()

    def get_dataframe(self, params):
        data = self.fetch(params)
        print(f"Data: {data}")
        df = pd.DataFrame(data["list"])
        df["dt"] = pd.to_datetime(df["dt"], unit="s")
        df.set_index("dt", inplace=True)
        df = df[["main", "components"]]
        df = pd.concat([df.drop(["main"], axis=1), df["main"].apply(pd.Series)], axis=1)
        df = pd.concat([df.drop(["components"], axis=1), df["components"].apply(pd.Series)], axis=1)
        return df
