import threading
import digitransit.routing
import digitransit.enums
import pygame

stopinfo = digitransit.routing.get_stop_info(digitransit.enums.Endpoint.WALTTI, 826)
print(stopinfo.name)
print(stopinfo.vehicleMode)
print("-------------------")
# TODO: Get line numbers
for time in stopinfo.stoptimes:
    print(time.headsign)
    print(time.realtimeDeparture)