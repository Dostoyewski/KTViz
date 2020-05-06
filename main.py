import json
from konverter import coords_relative, positions
import matplotlib.pyplot as plt
from math import sin, cos, radians, degrees
import numpy as np
import os
import argparse

# Disable trajectory curving
USE_CURVING = False


def plot_data(datas, filename, show, ax=None, start_coords=None, p_time=0):
    """
    This function plotes arc and lines
    :param p_time: Current time moment in percents of amount time
    :param start_coords: start coords for relative coords
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
    if not start_coords:
        # End coordinates of previous segment,
        # used for curving
        pX, pY = 0, 0
    else:
        pX, pY = start_coords[0], start_coords[1]
    # By default, start_time is null
    for data in datas:
        start_time = 0
        time = p_time * data['time']
        for item in data['items']:
            vel = item['length'] / item['duration']
            if not USE_CURVING:
                pX, pY = item['X'], item['Y']
            if item['curve'] == 0:
                # For lines
                X, Y = positions(item['begin_angle'], item['length'])
                ax.plot([pY, pY + Y], [pX, pX + X], linewidth=3)
            else:
                # For arcs
                if item['curve'] > 0:
                    Xc, Yc = positions(item['begin_angle'] + 90,
                                       1 / item['curve'])
                else:
                    Xc, Yc = positions(item['begin_angle'] - 90,
                                       1 / item['curve'])
                angle = item['begin_angle']
                Rarc = 1 / item['curve']
                dx = (Rarc * cos(radians(90 - angle)) + Xc - pX)
                if not USE_CURVING:
                    dy = (Rarc * sin(radians(90 - angle)) + Yc + pY)
                else:
                    # Some hotfix
                    dy = (Rarc * sin(radians(90 - angle)) + Yc - pY)
                dangle = degrees(item['length'] * item['curve'])
                X = []
                Y = []
                for angle in np.arange(item['begin_angle'], item['begin_angle'] + dangle, dangle / 100):
                    X.append(Rarc * cos(radians(90 - angle)) + Xc - dx)
                    Y.append(-(Rarc * sin(radians(90 - angle)) + Yc - dy))
                ax.plot(Y, X, linewidth=3)
            # Plotting current targets pose
            if time - start_time < item['duration'] and time >= start_time:
                if item['curve'] == 0:
                    Xt, Yt = positions(item['begin_angle'], vel*(time - start_time))
                    ax.plot(pY + Yt, pX + Xt, marker='D', color='r')
                else:
                    # False angular sign velocity direction
                    ang_vel = -vel * item['curve']
                    Xt = Rarc * cos(radians(90 - item['begin_angle']) +
                                    ang_vel*(time - start_time)) + Xc - dx
                    Yt = -(Rarc * sin(radians(90 - item['begin_angle']) +
                                    ang_vel*(time - start_time)) + Yc - dy)
                    ax.plot(Yt, Xt, marker='D', color='r')
            # Adding previous point
            if item['curve'] == 0:
                pX, pY = pX + X, -(pY + Y)
            else:
                pX, pY = X[-1], Y[-1]
            start_time += item['duration']
    ax.set(xlabel='x', ylabel='y',
           title='Trajectory')
    ax.grid()
    if ax is None:
        fig.savefig(filename + ".png")
    if show:
        plt.show()


def prepare_file(filename, show, ax=None, rel=False, tper=0):
    """
    Prepares route JSON for plotting,
    changes geodesic coords to relative
    :param tper: percent of amount time
    :param rel: use relative coords in JSON
    :param ax: axis to plot
    :param filename: JSON route filename
    :return: dictionary with translated route
    """
    try:
        if rel:
            key1, key2 = 'x', 'y'
        else:
            key1, key2 = 'lat', 'lon'
        data_all = []
        with open(filename) as f:
            datas = json.loads(f.read())
        # Start coordinates
        s_lat, s_lon = datas[0]['items'][0][key1], datas[0]['items'][0][key2]
        for data in datas:
            new_data = {'items': []}
            time = 0
            for item in data['items']:
                obj = {}
                for key in list(item.keys()):
                    if key != key1 and key != key2:
                        obj[key] = item[key]
                # Translate coordinates
                if not rel:
                    obj['X'], obj['Y'] = coords_relative(s_lat, s_lon, item[key1], item[key2])
                else:
                    # If use relative coords, fields lat and lon should contain X and Y
                    obj['X'], obj['Y'] = item[key1], item[key2]
                time += item['duration']
                new_data['items'].append(obj)
            new_data['time'] = time
            data_all.append(new_data)
        # new_data['start_time'] = data['start_time']
        if rel:
            plot_data(data_all, filename, show, ax, [s_lat, s_lon], p_time=tper)
        else:
            plot_data(data_all, filename, show, ax, p_time=tper)
        return data_all
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
