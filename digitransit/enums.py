from enum import Enum

class Mode(Enum):
    AIRPLANE = "AIRPLANE"
    BICYCLE = "BICYCLE"
    BUS = "BUS"
    CABLE_CAR = "CABLE_CAR"
    CAR = "CAR"
    FERRY = "FERRY"
    FUNICULAR = "FUNICULAR"
    GONDOLA = "GONDOLA"
    RAIL = "RAIL"
    SUBWAY = "SUBWAY"
    TRAM = "TRAM"
    WALK = "WALK"

    TRANSIT = "TRANSIT"

class Endpoint(Enum):
    HELSINKI = "hsl"
    WALTTI = "waltti"
    FINLAND = "finland"

class RealtimeState(Enum):
    SCHEDULED = "SCHEDULED"
    UPDATED = "UPDATED"
    CANCELED = "CANCELED"
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"