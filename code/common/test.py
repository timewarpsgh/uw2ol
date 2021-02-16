def _calc_longitude_and_latitude(x, y):
    # transform to longitude
    longitude = None
    if x >= 900 and x <= 1980:
        longitude = int(( x - 900 )/6)
        longitude = str(longitude) + 'e'
    elif x > 1980:
        longitude = int((900 + 2160 - x)/6)
        longitude = str(longitude) + 'w'
    else:
        longitude = int((900 - x)/6)
        longitude = str(longitude) + 'w'

    # transform to latitude
    latitude = None
    if y <= 640:
        latitude = int((640 - y)/7.2)
        latitude = str(latitude) + 'N'
    else:
        latitude = int((y - 640)/7.2)
        latitude = str(latitude) + 'S'

    return (longitude, latitude)

positions = [[900, 262], [600, 600]]

for pos in positions:
    x = pos[0]
    y = pos[1]
    longitude, latitude = _calc_longitude_and_latitude(x, y)
    pos[0] = longitude
    pos[1] = latitude



print(positions)