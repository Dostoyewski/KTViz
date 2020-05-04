import json
from konverter import coords_relative, positions
import matplotlib.pyplot as plt
from math import sin, cos, radians, degrees
import numpy as np


def plot_data(data):
    fig, ax = plt.subplots()
    pX, pY = 0, 0
    for item in data['items']:
        if item['curve'] == 0:
            X, Y = positions(item['begin_angle'], item['length'])
            ax.plot([pX, X], [pY, -Y])
            pX, pY = X, -Y
        else:
            if item['curve'] > 0:
                Xc, Yc = positions(item['begin_angle'] + 90,
                                   1 / item['curve'])
            else:
                Xc, Yc = positions(item['begin_angle'] - 90,
                                   1 / item['curve'])
            Rarc = 1 / item['curve']
            dangle = degrees(item['length']*item['curve'])
            X = []
            Y = []
            for angle in np.arange(item['begin_angle'], item['begin_angle']+dangle, dangle/100):
                X.append(Rarc * cos(radians(90 - angle)) + pX + Xc)
                Y.append(Rarc * sin(radians(90 - angle)) + pY + Yc)
            ax.plot(X, Y)
            pX, pY = X[-1], Y[-1]
    ax.set(xlabel='x', ylabel='y',
           title='Trajectory')
    ax.grid()
    fig.savefig("test.png")
    plt.show()
    plt.show()


def prepare_file(filename):
    """
    Prepares route JSON for plotting,
    changes geodesic coords to relative
    :param filename: JSON route filename
    :return: dictionary with translated route
    """
    # try:
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
    print(new_data)
    plot_data(new_data)
    return new_data
    # except:
    #     return None


if __name__ == "__main__":
    print(prepare_file('datafiles/sample_data.json'))
