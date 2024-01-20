#! /usr/bin/python3

from calendar import c
import sys
import os
from datetime import datetime, timezone as tz
import traceback
import json
from django import conf
from pytz import timezone
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from numpy import repeat
import pandas as pd

from src.api.api import Api
from src.api.pollution_api import PollutionApi
from src.api.weather_api import WeatherApi
from src.util.position_offsetter import PositionOffsetter

START = datetime(2020, 11, 28, tzinfo=tz.utc)
END = datetime(2023, 12, 1, tzinfo=tz.utc)

class LocalData:
    def __init__(self):
        os.makedirs(os.path.dirname(f'../../data/'), exist_ok=True)

    def load_data(self, key):
        if (type(key) != str):
            raise TypeError("key must be a string")
        
        # Load data from local file
        with open(f'../../data/{key}', 'r') as f:
            data = f.read()
        
        return data
    
def get_next_batch(config):
    end = min(int(config["current_date"]) + (int(config["batch_size"])*24 - 1)*3600, int(config["end"]))
    # Getting weather data
    api: Api = WeatherApi()  # Don't forget to add src/ directory to $PYTHONPATH
    params = {
        "latitude": config["lat"],
        "longitude": config["lon"],
        "start_date": datetime.utcfromtimestamp(int(config["current_date"])+3600).strftime('%Y-%m-%d'),
        "end_date": datetime.utcfromtimestamp(end).strftime('%Y-%m-%d'),
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "dewpoint_2m", "wind_speed_10m", "wind_direction_10m"],
    }
    data = api.fetch(params)
    weather_df = pd.DataFrame(data["hourly"])
    weather_df["time"] = pd.to_datetime(weather_df["time"], format="%Y-%m-%d")
    weather_df.set_index("time", inplace=True)

    # Getting pollution data
    api = PollutionApi()
    params = {
        "lat": config["lat"],
        "lon": config["lon"],
        "start": config["current_date"],
        "end": end,
        "appid": config["appid"],
    }
    data = api.fetch(params)
    pol_df = pd.DataFrame(data["list"])
    pol_df.rename(columns={"dt": "time"}, inplace=True)
    pol_df["time"] = pd.to_datetime(pol_df["time"], unit="s")
    pol_df.set_index("time", inplace=True)
    pol_df = pol_df[["main", "components"]]
    pol_df = pd.concat([pol_df.drop(["main"], axis=1), pol_df["main"].apply(pd.Series)], axis=1)
    pol_df = pd.concat([pol_df.drop(["components"], axis=1), pol_df["components"].apply(pd.Series)], axis=1)

    # Getting data for every offset
    offsetted_df = pd.DataFrame()
    for i in range(0, int(config["batch_size"])):
        offsetter = PositionOffsetter(config["lat"], config["lon"])
        offsetter.offset(weather_df["wind_speed_10m"][i], weather_df["wind_direction_10m"][i], 1)
        api = PollutionApi()
        params = {
            "lat": offsetter.lat,
            "lon": offsetter.lon,
            "start": config["current_date"] + 3600*24 * (i-1),
            "end": int(config["current_date"]) + 3600*(24*i-1),
            "appid": "3f4dd805354d2b0a8aaf79250d2b44fe",
        }
        data = api.fetch(params)
        current_offset_df = pd.DataFrame(data["list"])
        current_offset_df.rename(columns={"dt": "time"}, inplace=True)
        current_offset_df["time"] = pd.to_datetime(current_offset_df["time"], unit="s")
        current_offset_df["time"] += pd.Timedelta(days=1)
        current_offset_df.set_index("time", inplace=True)
        current_offset_df = current_offset_df[["main", "components"]]
        current_offset_df = pd.concat([current_offset_df.drop(["main"], axis=1), current_offset_df["main"].apply(pd.Series)], axis=1)
        current_offset_df = pd.concat([current_offset_df.drop(["components"], axis=1), current_offset_df["components"].apply(pd.Series)], axis=1)
        offsetted_df = pd.concat([offsetted_df, current_offset_df])

    offsetted_df = offsetted_df.rename(columns=(lambda x: x + "_offset"))

    offsetted_df.to_csv(f'../../data/offsetted.csv')
    weather_df.to_csv(f'../../data/weather.csv')
    pol_df.to_csv(f'../../data/pollution.csv')

    # Merging dataframes
    df = pd.concat([weather_df, pol_df], axis=1)
    df = pd.concat([df, offsetted_df], axis=1)

    return df
    
if __name__ == "__main__":
    config = {}
    try:
        with open(f'../../data/config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Generating new config file...")
        with open(f'../../data/config.json', 'w') as cfg_file:
            config = {"lat": "45.1",
                      "lon": "5.6",
                      "appid": "3f4dd805354d2b0a8aaf79250d2b44fe",
                      "start": int(START.timestamp()),
                      "end": int(END.timestamp()),
                      "batch_size": 60,
                      "current_date": int(START.timestamp())} 
            json.dump(config, cfg_file)
        print("Done.")
    except Exception as e:
        print("Error while loading config file.")
        print(e)
        print(traceback.format_exc())
        exit()

    try:
        data = pd.DataFrame()
        with open(f'../../data/training.csv', 'r') as f:
            data = pd.read_csv(f)

            data["time"] = pd.to_datetime(data["time"], format="%Y-%m-%d")
            data.set_index("time", inplace=True)

            data = pd.concat([data, get_next_batch(config)])
            data.to_csv(f'../../data/training.csv')

            config["current_date"] = int(config["current_date"]) + int(config["batch_size"])*3600*24
            with open(f'../../data/config.json', 'w') as cfg_file:
                json.dump(config, cfg_file)
            print(f"Got data until {config['current_date']}, remaining: {(config['end'] - config['current_date']) / config['batch_size']/3600/24} batches.")
    except FileNotFoundError:
        print("File not found, creating new file...")

        df = get_next_batch(config)
        df.to_csv(f'../../data/training.csv', )

        config["current_date"] = int(config["current_date"]) + int(config["batch_size"])*3600*24
        with open(f'../../data/config.json', 'w') as cfg_file:
            json.dump(config, cfg_file)
        print("Done first batch.")
        exit()
    except Exception as e:
        print("Error while fetching data.")
        print(e)
        print(traceback.format_exc())
        print(data)
        exit()
