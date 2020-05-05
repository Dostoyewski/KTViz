import json
from konverter import coords_relative, positions
import matplotlib.pyplot as plt
from math import sin, cos, radians, degrees
import numpy as np
import os
import argparse


def plot_data(data, filename, show, ax=None):
    """
    This function plotes arc and lines
    :param show: show all plots in figure window
    :param ax: axes to plot
    :param data: JSON with path
    :param filename: name of file, used to save image
    :return: void
    """
    try:
        filename = "img/" + filename.split(sep='/')[1]
    except:
        pass
    if ax is None:
        fig, ax = plt.subplots()
    pX, pY = 0, 0
    for item in data['items']:
        if item['curve'] == 0:
            X, Y = positions(item['begin_angle'], item['length'])
            ax.plot([pY, pY + Y], [pX, pX + X], linewidth=3)
            pX, pY = pX + X, -(pY + Y)
        else:
            if item['curve'] > 0:
                Xc, Yc = positions(item['begin_angle'] + 90,
                                   1 / item['curve'])
            else:
                Xc, Yc = positions(item['begin_angle'] - 90,
                                   1 / item['curve'])
            angle = item['begin_angle']
            Rarc = 1 / item['curve']
            dx = (Rarc * cos(radians(90 - angle)) + Xc - pX)
            dy = (Rarc * sin(radians(90 - angle)) + Yc - pY)
            dangle = degrees(item['length'] * item['curve'])
            X = []
            Y = []
            for angle in np.arange(item['begin_angle'], item['begin_angle'] + dangle, dangle / 100):
                X.append(Rarc * cos(radians(90 - angle)) + Xc - dx)
                Y.append(-(Rarc * sin(radians(90 - angle)) + Yc - dy))
            ax.plot(Y, X, linewidth=3)
            pX, pY = X[-1], Y[-1]
    ax.set(xlabel='x', ylabel='y',
           title='Trajectory')
    ax.grid()
    if ax is None:
        fig.savefig(filename + ".png")
    if show:
        plt.show()


def prepare_file(filename, show, ax=None):
    """
    Prepares route JSON for plotting,
    changes geodesic coords to relative
    :param ax: axis to plot
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
        plot_data(new_data, filename, show, ax)
        return new_data
    except:
        return None


def make_all(path, show):
    """
    Makes for all files in directory
    :param path: directory with datafiles
    :return: void
    """
    files = os.listdir(path)
    for file in files:
        if file[-4:] == 'json':
            prepare_file(path + '/' + file, show)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test scenario plotter")
    parser.add_argument("casefile", type=str, help="Name of file or folder, when -a is used")
    parser.add_argument("-a", action="store_true", help="Makes all files")
    parser.add_argument("-s", action="store_true", help="Show image")
    args = parser.parse_args()
    if args.a:
        print("Making for all files in path: ",
              args.casefile)
        make_all(args.casefile, args.s)
    else:
        print("Making for file: ", args.casefile)
        prepare_file(args.casefile, args.s)
