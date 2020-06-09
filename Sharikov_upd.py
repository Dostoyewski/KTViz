from konverter import coords_relative, positions, coords_global
import json

def convert_file(filename):
    """
    Updates global coords
    Load target-data to this func
    :param filename:
    :return:
    """
    s_lat, s_lon = 60, 30
    with open(filename) as f:
        data = json.loads(f.read())
        for i in range(len(data)):
            lat, lon = data[i]['lat'], data[i]['lon']
            x, y = coords_relative(s_lat, s_lon, lat, lon)
            x /= 10
            y /= 10
            lat, lon = coords_global(x, y, s_lat. s_lon)
            data[i]['lat'], data[i]['lon'] = lat, lon
        with open(filename, "w") as fp:
            json.dump(data, fp)
