import json
from konverter import coords_relative


def prepare_file(filename):
    """
    Prepares route JSON for plotting,
    changes geodesic coords to relative
    :param filename: JSON route filename
    :return: dictionary with translated route
    """
    try:
        new_data = {'start_time': 0, 'items': []}
        with open(filename) as f:
            data = json.loads(f.read())
        s_lat, s_lon = data['items'][0]['lat'], data['items'][0]['lon']
        for item in data['items']:
            obj = {}
            for key in list(item.keys()):
                if key != 'lat' and key != 'lon':
                    obj[key] = item[key]
            obj['X'], obj['Y'] = coords_relative(s_lat, s_lon, item['lat'], item['lon'])
            new_data['items'].append(obj)
        new_data['start_time'] = data['start_time']
        return new_data
    except:
        return None


if __name__ == "__main__":
    print(prepare_file('datafiles/sample_data.json'))
