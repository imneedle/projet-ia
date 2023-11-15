#! /usr/bin/python3

import os
import datetime
import traceback

from numpy import repeat

from src.api.api import Api
from src.api.pollution_api import PollutionApi
from src.api.weather_api import WeatherApi

START = datetime.datetime(2020, 11, 28)
END = datetime.datetime(2020, 11, 30)

class LocalData:
    def __init__(self):
        os.makedirs(os.path.dirname(f'../../data/'), exist_ok=True)

    def saveData(self, data):
        if (type(data) != dict):
            raise TypeError("data must be a dict")
        
        # Save data to local file
        for key in data:
            with open(f'../../data/{key}', 'w') as f:
                f.write(data[key])
    
    def savePollution(self, data, prefix=""):
        if (type(data) != dict):
            raise TypeError("data must be a dict")
        
        if (type(prefix) != str):
            raise TypeError("prefix must be a string")
        
        # Open all files only once
        files = {}
        for component in data["list"][0]["components"]:
            files[component] = open(f"../../data/{prefix}{component}.txt", 'w')
        files["dt"] = open(f"../../data/{prefix}dt.txt", 'w')
        files["aqi"] = open(f"../../data/{prefix}aqi.txt", 'w')
            
        # Save data to local files
        for i in range(len(data["list"])):
            files["dt"].write(str(data["list"][i]["dt"]) + "\n")
            files["aqi"].write(str(data["list"][i]["main"]["aqi"]) + "\n")
            for component in data["list"][i]["components"]:
                print(data["list"][i]["components"][component], file=files[component])

        # Close all files
        for component in files:
            files[component].close()

    def saveWeather(self, data, prefix=""):
        if (type(data) != dict):
            raise TypeError("data must be a dict")
        
        if (type(prefix) != str):
            raise TypeError("prefix must be a string")
        
        # Open all files only once
        files = {}
        for component in data["hourly"]:
            files[component] = open(f"../../data/{prefix}{component}.txt", 'w')
        for component in data["daily"]:
            files[component] = open(f"../../data/{prefix}{component}.txt", 'w')

        # Save data to local files
        for component in data["hourly"]:
            if (component != "time"):
                print("\n".join(data["hourly"][component]), file=files[component])
        
        for component in data["daily"]:
            if (component != "time"):
                print("\n".join(repeat(data["daily"][component]), 24), file=files[component])

        # Close all files
        for component in files:
            files[component].close()

    def loadData(self, key):
        if (type(key) != str):
            raise TypeError("key must be a string")
        
        # Load data from local file
        with open(f'../../data/{key}', 'r') as f:
            data = f.read()
        
        return data
    
if __name__ == "__main__":
    print("Running this script will delete all data in the data/ directory. Are you sure you want to continue? (y/N)")
    if (input() != "y"):
        print("Aborting...")
        exit()
    print("Deleting data...")
    try :
        os.system("rm -r ../../data/*")
    except:
        print("Error while deleting data.")
        exit()
    
    print("Done.")

    try:
        print("Processing pollution data...")
        localData = LocalData()
        api: Api = PollutionApi()  # Don't forget to add src/ directory to $PYTHONPATH
        params = {
            "lat": "45.1",
            "lon": "5.6",
            "start": int(START.timestamp()),
            "end": int(END.timestamp()),
            "appid": "3f4dd805354d2b0a8aaf79250d2b44fe",
        }
        data = api.fetch(params)
        localData.savePollution(data)

        print("Processing weather data...")
        api: Api = WeatherApi()  # Don't forget to add src/ directory to $PYTHONPATH
        params = {
            "latitude": "45.18857814633678",
            "longitude": "5.718267792253707",
            "hourly": "relativehumidity_2m,dewpoint_2m,cloudcover_mid,windspeed_80m,winddirection_80m,temperature_80m",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "Europe/London",
            "start_date": START.strftime("%Y-%m-%d"),
            "end_date": END.strftime("%Y-%m-%d")
        }
        data = api.fetch(params)
        localData.saveWeather(data)
        print("Done.")
    except Exception as e:
        print("Error while fetching data.")
        print(e)
        print(traceback.format_exc())
        print(data)
        exit()

