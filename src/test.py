#!/usr/bien/env python3

from math import radians, asin, sin, cos, atan2, degrees

def calculate_new_position(current_lat, current_lon, wind_speed, wind_direction, time_interval):
    # Radius of the Earth in kilometers
    R = 6371.0

    # Convert latitude and longitude from degrees to radians
    lat1 = radians(current_lat)
    lon1 = radians(current_lon)

    # Convert wind direction from degrees to radians
    wind_direction_rad = radians(wind_direction)

    # Calculate the distance traveled in the given time interval
    distance = (wind_speed * time_interval)

    # Calculate the new latitude and longitude
    lat2 = asin(sin(lat1) * cos(distance / R) + cos(lat1) * sin(distance / R) * cos(wind_direction_rad))
    lon2 = lon1 + atan2(sin(wind_direction_rad) * sin(distance / R) * cos(lat1), cos(distance / R) - sin(lat1) * sin(lat2))
    
    # Convert back to degrees
    new_lat = round(degrees(lat2), 6)
    new_lon = round(degrees(lon2), 6)

    return new_lat, new_lon

# Example usage
current_latitude = 37.7749
current_longitude = -122.4194
wind_speed = 100  # in km/h
wind_direction = 135  # in degrees
time_interval = 1

new_latitude, new_longitude = calculate_new_position(current_latitude, current_longitude, wind_speed, wind_direction, time_interval)

print(f"Current Position: ({current_latitude}, {current_longitude})")
print(f"New Position 1 hour before: ({new_latitude}, {new_longitude})")