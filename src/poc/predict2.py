#! /usr/bin/python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

import requests
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor

from src.api.api import Api
from src.api.pollution_api import PollutionApi


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
    lat = "45.1"
    lon = "5.6"
    start = "1606488670"
    end = "1606747870"
    appid = "3f4dd805354d2b0a8aaf79250d2b44fe"
    n_neighbors = 5
    df = get_data(lat, lon, start, end, appid)
    knn = train_knn_model(df, n_neighbors)
    # Use the trained model to predict air quality at the given position
    # for the next 24 hours
    # You can use the predict() method of the KNN model to make predictions
    # based on the features of the data you have.
    # Here is an example of how to use the predict() method:
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
    print(future_y, len(future_y))
