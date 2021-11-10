from numpy import cos, sin, arcsin, sqrt
from math import radians

def haversine(row, lon1, lat1):
    lon2 = row['lon']
    lat2 = row['lat']
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * arcsin(sqrt(a))
    mn = 3437.9 * c
    return mn
