import json
import math
import os
from collections import namedtuple

from geographiclib.geodesic import Geodesic
from math import sin, cos, radians, degrees
import numpy as np
import argparse
from matplotlib import pyplot as plt

Position = namedtuple('Position', ['x', 'y', 'course', 'vel'])


def item_position(item, time):
    vel = item['length'] / item['duration']
    length = vel * time
    b_cos = cos(math.radians(item['begin_angle']))
    b_sin = sin(math.radians(item['begin_angle']))
    if item['curve'] == 0:
        return Position(item['X'] + round(length * b_cos, 2), item['Y'] + round(length * b_sin, 2), item['begin_angle'],
                        vel)
    else:
        # For arcs
        r = abs(1 / item['curve'])
        dangle = abs(length * item['curve'])
        sign = 1 if item['curve'] > 0 else -1
        x_, y_ = sin(dangle), sign * (1 - cos(dangle))
        return Position(item['X'] + r * (x_ * b_cos - y_ * b_sin), item['Y'] + r * (x_ * b_sin + y_ * b_cos),
                        item['begin_angle'] + sign * degrees(dangle), vel)


def path_position(path, t):
    time = t - path['start_time']
    if time < 0:
        raise KeyError('Time lower than path start time')
    for item in path['items']:
        if time < item['duration']:
            return item_position(item, time)
        time -= item['duration']
    return Position(None, None, None, None)


def plot_path(path, ax, color):
    angle_inc = radians(1)
    xx, yy = [], []
    for item in path['items']:
        xx.append(item['X'])
        yy.append(item['Y'])
        b_cos = cos(math.radians(item['begin_angle']))
        b_sin = sin(math.radians(item['begin_angle']))
        if item['curve'] == 0:
            xx.append(item['X'] + round(item['length'] * b_cos, 2))
            yy.append(item['Y'] + round(item['length'] * b_sin, 2))
        else:
            # For arcs
            r = abs(1 / item['curve'])
            dangle = abs(item['length'] * item['curve'])

            sign = 1 if item['curve'] > 0 else -1
            for angle in np.arange(0, dangle, angle_inc):
                x_, y_ = sin(angle), sign * (1 - cos(angle))
                xx.append(item['X'] + r * (x_ * b_cos - y_ * b_sin))
                yy.append(item['Y'] + r * (x_ * b_sin + y_ * b_cos))
    ax.plot(yy, xx, color=color)


def plot_position(x, y, course, ax, radius=.0, color='red', label=None):
    scatter = ax.scatter(y, x, color=color, marker=(3, 0, -course), label=label)
    if radius != 0:
        danger_r = plt.Circle((y, x), radius, color=color, fill=False)
        ax.add_artist(danger_r)
    return scatter


class Frame:
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def from_wgs(self, lat, lon):
        """
        Converts WGS coords to local
        :param lat:
        :param lon:
        :return: x, y, distance, bearing
        """
        path = Geodesic.WGS84.Inverse(self.lat, self.lon, lat, lon)

        angle = radians(path['azi1'])
        dist = path['s12'] / 1852
        return dist * cos(angle), dist * sin(angle), dist, angle

    def to_wgs(self, x, y):
        """
        Converts local coords to WGS
        :param x:
        :param y:
        :return: lat, lon
        """
        azi1 = degrees(math.atan2(y, x))
        dist = (x ** 2 + y ** 2) ** .5
        path = Geodesic.WGS84.Direct(self.lat, self.lon, azi1, dist * 1852)
        return path['lat2'], path['lon2']


class Data:
    def __init__(self, frame, route=None):
        self.paths = []
        self.frame = frame
        self.route = route


def prepare_path(data, frame=None):
    key1, key2 = 'lat', 'lon'
    new_data = {'items': [], 'start_time': data['start_time']}
    time = 0
    for item in data['items']:
        obj = {}
        for key in list(item.keys()):
            if key != key1 and key != key2:
                obj[key] = item[key]
        # Translate coordinates
        obj['X'], obj['Y'], dist, angle = frame.from_wgs(item[key1], item[key2])

        time += item['duration']
        new_data['items'].append(obj)
    new_data['time'] = time
    return new_data


def prepare_file(filename):
    with open(filename) as f:
        file_data = json.loads(f.read())
    # Sample initial position to anchor Frame
    sample = file_data[0]['items'][0]
    if 'lat' in sample and 'lon' in sample:
        key1, key2 = 'lat', 'lon'
        frame = Frame(file_data[0]['items'][0][key1], file_data[0]['items'][0][key2])
    else:
        raise KeyError('No coords in maneuver')

    # Prepare data
    paths = []
    for data in file_data:
        new_data = prepare_path(data, frame=frame)
        paths.append(new_data)

    return paths, frame


def plot_maneuvers(ax, data):
    for i, path in enumerate(data):
        plot_path(path, ax, color=('brown' if i == 0 else 'blue'))


def plot_route(ax, file, frame):
    with open(file) as f:
        route_data = json.loads(f.read())
        path = prepare_path(route_data, frame=frame)
        plot_path(path, ax, color='#fffffffa')


def get_positions(data, t):
    return [path_position(path, t) for path in data]


def plot_positions(ax, positions, radius=1.5, coords=False, frame=None):
    for i, position in enumerate(positions):
        if position.x is not None:
            label_text = '#{}, {:.2f}knt,{:.2f}°'.format(i, position.vel * 3600, position.course)
            if coords:
                if frame is not None:
                    lat, lon = frame.to_wgs(position.x, position.y)
                    label_text += '\n{:.4f}, {:.4f}'.format(lat, lon)
                else:
                    label_text += '\n{:.4f}, {:.4f}'.format(position.x, position.y)
            plot_position(position.x, position.y, position.course, ax, radius=radius,
                          color=('red' if i == 0 else 'blue'),
                          label=label_text)
            ax.text(position.y, position.x, '#{}'.format(i), size=8)


def plot_distances(ax, positions, distance=5.):
    max_dist_sq = distance ** 2
    if positions[0].x is None:
        return
    x, y = positions[0].x, positions[0].y
    for i in range(1, len(positions)):
        if positions[i].x is not None:
            dist = (positions[i].x - x) ** 2 + (positions[i].y - y) ** 2
            if dist < max_dist_sq:
                h = ax.plot((y, positions[i].y), (x, positions[i].x), color='red')
                # Location to plot text
                text_x, text_y = (positions[i].x + x) * .5, (positions[i].y + y) * .5
                # Rotate angle
                angle = (degrees(math.atan2(positions[i].x - x, positions[i].y - y)) - 90) % 180 - 90
                # Plot text
                ax.text(text_y, text_x, '{:.1f}'.format(dist ** .5), fontsize=8, rotation=angle, rotation_mode='anchor')


def plot_captions(ax, positions):
    for i, position in positions:
        plot_position(position.x, position.y, position.course, ax, radius=1.5, color=('red' if i == 0 else 'blue'))


def plot_from_files(maneuvers_file, route_file=None):
    if os.path.isfile(maneuvers_file):
        fig = plt.figure(figsize=(10, 7.5))
        ax = fig.add_subplot(111)
        ax.clear()
        ax.set_facecolor((159 / 255, 212 / 255, 251 / 255))

        data, frame = prepare_file(maneuvers_file)

        if route_file is not None:
            plot_route(ax, route_file, frame)

        plot_maneuvers(ax, data)

        ax.axis('equal')
        ax.grid()

        start_time = data[0]['start_time']
        positions = get_positions(data, start_time)
        plot_positions(ax, positions)
        ax.legend()

        return fig
    else:
        raise FileNotFoundError("{} not found".format(maneuvers_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test scenario plotter")
    # parser.add_argument("casefile", type=str, help="Name of file or folder, when -a is used")
    # parser.add_argument("-a", action="store_true", help="Makes all files")
    # parser.add_argument("-s", action="store_true", help="Show image")
    args = parser.parse_args()

    figure = plot_from_files("maneuver.json", route_file="route-data.json")
    plt.show()
