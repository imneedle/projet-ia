#!/usr/bin/env python3

import math


class PositionOffsetter:
    EARTH_RADIUS_KM = 6371.0
    FLOAT_APPROXIMATION = 6

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def offset(self, wind_speed, wind_direction, time):
        """Offsets the position depending on the wind
        :param wind_speed: speed of the wind in km/h
        :param wind_direction: direction of the wind in degrees
        :param time: the time interval in hours"""
        lat1 = math.radians(self.lat)
        lon1 = math.radians(self.lon)
        wind_direction_rad = math.radians(wind_direction)
        distance = wind_speed * time

        A = math.cos(distance / self.EARTH_RADIUS_KM)
        B = math.sin(distance / self.EARTH_RADIUS_KM)
        lat2 = math.asin(math.sin(lat1) * A + math.cos(lat1) * B * math.cos(wind_direction_rad))
        lon2 = lon1 + math.atan2(math.sin(wind_direction_rad) * B * math.cos(lat1), A - math.sin(lat1) * math.sin(lat2))

        self.lat = round(math.degrees(lat2), self.FLOAT_APPROXIMATION)
        self.lon = round(math.degrees(lon2), self.FLOAT_APPROXIMATION)


if __name__ == "__main__":
    lat = 37.7749
    lon = -122.4194
    position = PositionOffsetter(lat, lon)

    wind_speed = 100  # in km/h
    wind_direction = 135  # in degrees
    time = 1  # in hours

    print(f"Current Position: ({position.lat}, {position.lon})")
    position.offset(wind_speed, wind_direction, time)
    print(f"New Position {time} hours after: ({position.lat}, {position.lon})")


