#! /usr/bin/python3

import os

from src.api.api import Api
from src.api.pollution_api import PollutionApi

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
    print("Fetching data...")
    localData = LocalData()
    api: Api = PollutionApi()  # Don't forget to add src/ directory to $PYTHONPATH
    params = {
        "lat": "45.1",
        "lon": "5.6",
        "start": "1606488670",
        "end": "1606747870",
        "appid": "3f4dd805354d2b0a8aaf79250d2b44fe",
    }
    data = api.fetch(params)
    print("Saving data...")
    localData.savePollution(data)
    print("Done.")

