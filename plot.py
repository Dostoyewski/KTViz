import argparse
import json
import math
import os
from collections import namedtuple
from math import sin, cos, radians, degrees

import numpy as np
from matplotlib import pyplot as plt, gridspec
from matplotlib.patches import Ellipse, Polygon

from konverter import Frame

Position = namedtuple('Position', ['x', 'y', 'course', 'vel'])


def load_json(filename):
    if not os.path.isfile(filename):
        return None

    with open(filename) as f:
        file_data = json.loads(f.read())
    return file_data


def load_case_from_directory(dir_path):
    return Case(nav_data=load_json(os.path.join(dir_path, 'nav-data.json')),
                maneuvers=load_json(os.path.join(dir_path, 'maneuver.json')),
                targets_data=load_json(os.path.join(dir_path, 'target-data.json')),
                targets_maneuvers=load_json(os.path.join(dir_path, 'target-maneuvers.json')),
                targets_real=load_json(os.path.join(dir_path, 'real-target-maneuvers.json')),
                analyse=load_json(os.path.join(dir_path, 'analyse.json')),
                constraints=load_json(os.path.join(dir_path, 'constraints.json')),
                route=load_json(os.path.join(dir_path, 'route-data.json')),
                settings=load_json(os.path.join(dir_path, 'settings.json')))


def path_time(path):
    return sum([x['duration'] for x in path['items']])


class Case:
    def __init__(self, nav_data=None, maneuvers=None, targets_data=None, targets_maneuvers=None, targets_real=None,
                 analyse=None, constraints=None, route=None, settings=None):
        self.nav_data = nav_data
        if self.nav_data is None:
            return
        self.frame = Frame(nav_data['lat'], nav_data['lon'])
        self.start_time = self.nav_data['timestamp']
        self.maneuvers = maneuvers
        if self.maneuvers is not None:
            self.start_time = maneuvers[0]['path']['start_time']
            for maneuver in self.maneuvers:
                maneuver['path'] = prepare_path(maneuver['path'], frame=self.frame)
        self.route = route
        if route is not None:
            self.route = prepare_path(route, frame=self.frame)

        self.targets_data = targets_data
        self.targets_maneuvers = targets_maneuvers
        if self.targets_maneuvers is not None:
            self.targets_maneuvers = [prepare_path(path, self.frame) for path in self.targets_maneuvers]
        self.targets_real = targets_real
        if self.targets_real is not None:
            self.targets_real = [prepare_path(path, self.frame) for path in self.targets_real]
        self.analyse = analyse
        self.constraints = constraints
        self.settings = settings


def plot_case_paths(ax, case, maneuver_index=0, all_maneuvers=True, real_maneuvers=True):
    if case.route is not None:
        plot_path(case.route, ax, '#fffffffa')

    if real_maneuvers and case.targets_real is not None:
        for path in case.targets_maneuvers:
            plot_path(path, ax, 'gray')

    if case.targets_maneuvers is not None:
        for path in case.targets_maneuvers:
            plot_path(path, ax, 'blue')

    if case.maneuvers is not None:
        if all_maneuvers:
            for i, maneuver in enumerate(case.maneuvers):
                if i != maneuver_index:
                    plot_path(case.maneuvers[maneuver_index]['path'], ax, 'darkCyan')

        if maneuver_index <= len(case.maneuvers):
            plot_path(case.maneuvers[maneuver_index]['path'], ax, 'brown')


def plot_case_positions(ax, case, t, maneuver_index=0, all_maneuvers=True, real_maneuvers=True, radius=1.5,
                        coords=False):
    positions = []
    colors = []
    names = []

    if real_maneuvers and case.targets_real is not None:
        for path in case.targets_real:
            positions.append(path_position(path, t))
            colors.append('darkGray')
            names.append(None)
    # Targets
    if case.targets_maneuvers is not None:
        for path in case.targets_maneuvers:
            positions.append(path_position(path, t))

        if case.targets_data is not None:
            names += [target['id'] for target in case.targets_data]
            if case.analyse is not None:
                statuses = {}
                for status in case.analyse['target_statuses']:
                    statuses[status['id']] = status['danger_level']
                danger_levels = {0: 'blue', 1: 'orange', 2: 'red'}
                for target in case.targets_data:
                    if target['id'] in statuses:
                        colors.append(danger_levels[statuses[target['id']]])
                    else:
                        colors.append(danger_levels[0])
            else:
                colors += ['blue'] * len(case.targets_maneuvers)

        else:
            names += [str(i) for i, path in enumerate(case.targets_maneuvers)]
            colors += ['blue'] * len(case.targets_maneuvers)

    # Our
    if case.maneuvers is not None:
        if all_maneuvers:
            for i, maneuver in enumerate(case.maneuvers):
                if i != maneuver_index:
                    positions.append(path_position(maneuver['path'], t))
                    colors.append('darkGreen')
                    names.append(None)

        if maneuver_index <= len(case.maneuvers):
            positions.append(path_position(case.maneuvers[maneuver_index]['path'], t))
            colors.append('green')
            names.append('Our')

    plot_positions(ax, positions, names, colors, radius=radius, coords=coords, frame=case.frame)
    return positions


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


def recalc_lims(path):
    xx, yy = calculate_path_points(path)
    xmax, xmin = np.max(yy), np.min(yy)
    dx = xmax - xmin
    ymax, ymin = np.max(xx), np.min(xx)
    dy = ymax - ymin
    # if dx > dy:
    xlim = (xmin - dx * .1, xmax + dx * .1)
    # else:
    ylim = (ymin - dy * .1, ymax + dy * .1)
    return xlim, ylim


def calculate_path_points(path):
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
    return xx, yy


def plot_path(path, ax, color):
    xx, yy = calculate_path_points(path)
    ax.plot(yy, xx, color=color)


def plot_position(x, y, course, ax, radius=.0, color='red', label=None):
    scatter = ax.scatter(y, x, color=color, marker=(3, 0, -course), label=label, zorder=5)
    if radius != 0:
        danger_r = plt.Circle((y, x), radius, color=color, fill=False)
        ax.add_artist(danger_r)
    return scatter


def prepare_path(data, frame=None):
    key1, key2 = 'lat', 'lon'
    new_data = {'items': [], 'start_time': data['start_time']}
    time = 0
    for item in data['items']:
        obj = {}
        for key in list(item.keys()):
            obj[key] = item[key]
        # Translate coordinates
        obj['X'], obj['Y'], dist, angle = frame.from_wgs(item[key1], item[key2])

        time += item['duration']
        new_data['items'].append(obj)
    new_data['time'] = time
    return new_data


def plot_case_limits(ax, case):
    plot_limits(ax, case.constraints, case.frame)


def plot_limits(ax, data, frame):
    """
    This function plots navigation limits
    :param frame: frame to convert
    :param ax: axes
    :param data: limitations
    :return:
    """
    polygons = [item for item in data['features']
                if item['geometry']['type'] == 'Polygon']
    points = [item for item in data['features']
              if item['geometry']['type'] == 'Point']
    lines = [item for item in data['features']
             if item['geometry']['type'] == 'LineString']
    plot_polygons(ax, polygons, frame)
    plot_points(ax, points, frame)
    plot_lines(ax, lines, frame)


def plot_lines(ax, lines, frame):
    """
    Plot line_crossing_prohibition objects
    :param frame: frame
    :param ax: axes
    :param lines: array with lines
    :return:
    """
    for obj in lines:
        coords = obj['geometry']['coordinates']
        coords_x = [frame.from_wgs(item[1], item[0])[1] for item in coords]
        coords_y = [frame.from_wgs(item[1], item[0])[0] for item in coords]
        ax.plot(coords_x, coords_y, marker='D', color='r')


def plot_points(ax, points, frame):
    """
    Plot point_approach_prohibition objects
    :param frame: frame
    :param ax: axes
    :param points: array with points
    :return:
    """
    for obj in points:
        coords = obj['geometry']['coordinates']
        dist = obj['properties']['distance']
        coords = frame.from_wgs(coords[1], coords[0])
        ax.plot(coords[1], coords[0], marker='*', color='r')
        ax.add_patch(Ellipse((coords[1], coords[0]), dist, dist, fill=False,
                             hatch='/', color='red'))


def plot_polygons(ax, polygons, frame):
    """
    Plot polygons
    :param frame: frame
    :param ax: axes
    :param polygons: array with polygons
    :return:
    """
    for obj in polygons:
        coords = obj['geometry']['coordinates']
        # GeoJSON uses lon, lat notation
        coords = [frame.from_wgs(item[1], item[0])[:2] for item in coords[0]]
        coords = [[obj[1], obj[0]] for obj in coords]
        if obj['properties']['limitation_type'] == "zone_entering_prohibition":
            ax.add_patch(Polygon(coords, closed=True,
                                 fill=False, hatch='/', color='red'))
        elif obj['properties']['limitation_type'] == "zone_leaving_prohibition":
            ax.add_patch(Polygon(coords, closed=True,
                                 fill=False, hatch='/', color='blue'))
        elif obj['properties']['limitation_type'] == "movement_parameters_limitation":
            ax.add_patch(Polygon(coords, closed=True,
                                 fill=False, hatch='|', color='orange'))


def get_path_info(filename, solver):
    """

    :param filename:
    :param solver:
    :return:
    """
    with open(filename) as f:
        file_data = json.loads(f.read())
    return file_data[solver]['solver_name'], file_data[solver]['msg']


def plot_maneuvers(ax, data, no_maneuver=False):
    """
    Plot trajs
    :param ax:
    :param data:
    :param no_maneuver: if no maneuver.json
    :return:
    """
    for i, path in enumerate(data):
        # Dummy fix #2
        if no_maneuver:
            z = i + 1
        else:
            z = i
        # Plot path from second solver
        try:
            if path['second']:
                plot_path(path, ax, color='darkCyan')
                continue
        except KeyError:
            pass
        try:
            if path['real']:
                plot_path(path, ax, color='gray')
                continue
        except KeyError:
            pass
        plot_path(path, ax, color=('brown' if z == 0 else 'blue'))


def plot_route(ax, file, frame):
    with open(file) as f:
        route_data = json.loads(f.read())
        path = prepare_path(route_data, frame=frame)
        plot_path(path, ax, color='#fffffffa')


def get_positions(data, t):
    return [path_position(path, t) for path in data]


def plot_nav_points(ax, case):
    """
    Plots current positions from nav-data file
    :param case: Case
    :param ax: mtplb axes
    :return:
    """
    target_data = [case.nav_data] + case.targets_data
    for obj in target_data:
        out = case.frame.from_wgs(obj['lat'], obj['lon'])
        x, y = out[0], out[1]
        # Dummy fix:
        if abs(x) > 1500 or abs(y) > 1500:
            out = case.frame.from_wgs(obj['lon'], obj['lat'])
            x, y = out[0], out[1]
        ax.scatter(y, x, color='black', marker='x')
        ax.text(y, x, str(obj['timestamp']), size=8)


def plot_positions(ax, positions, names=None, colors=None, radius=1.5, coords=False, frame=None):
    """
    Plots ships positions
    :param colors: list of colors
    :param names: list of names
    :param ax: plot axes
    :param positions: array with positions
    :param radius: safe radius
    :param coords: if needs to konvert from local to WGS84
    :param frame: frame
    :return:
    """
    if colors is None:
        colors = [('red' if i == 0 else 'blue') for i in range(len(positions))]

    if names is None:
        names = ['#' + str(i) for i in range(len(positions))]

    for i, position in enumerate(positions):
        if position.x is not None and position.y is not None:
            label_text = '{}, {:.2f}knt,{:.2f}°'.format(names[i], position.vel * 3600, position.course)
            if coords:
                if frame is not None:
                    lat, lon = frame.to_wgs(position.x, position.y)
                    label_text += '\n{:.4f}°, {:.4f}°'.format(lat, lon)
                else:
                    label_text += '\n{:.4f}, {:.4f}'.format(position.x, position.y)
            plot_position(position.x, position.y, position.course, ax, radius=radius,
                          color=colors[i], label=(label_text if names[i] is not None else None))
            ax.text(position.y, position.x, names[i], size=8)


def plot_distances(ax, positions, distance=5.):
    max_dist_sq = distance ** 2
    if positions[0].x is None:
        return
    x, y = positions[0].x, positions[0].y
    for i in range(1, len(positions)):
        if positions[i].x is not None:
            dist = (positions[i].x - x) ** 2 + (positions[i].y - y) ** 2
            if dist < max_dist_sq:
                ax.plot((y, positions[i].y), (x, positions[i].x), color='red')
                # Location to plot text
                text_x, text_y = (positions[i].x + x) * .5, (positions[i].y + y) * .5
                # Rotate angle
                angle = (degrees(math.atan2(positions[i].x - x, positions[i].y - y)) - 90) % 180 - 90
                # Plot text
                ax.text(text_y, text_x, '{:.1f}'.format(dist ** .5), fontsize=8, rotation=angle, rotation_mode='anchor')


def plot_captions(ax, positions):
    for i, position in positions:
        plot_position(position.x, position.y, position.course, ax, radius=1.5, color=('red' if i == 0 else 'blue'))


def plot_speed(ax, path):
    """
    Makes speed plot
    :param ax: axes
    :param path: path, contains trajectory items
    :return:
    """
    if len(path['items']) > 0:
        velocities = [item['length'] / item['duration'] * 3600 for item in path["items"]]
        times = [item['duration'] / 3600 for item in path["items"]]
        dtimes = [0]
        for i in range(len(times)):
            dtimes.append(sum(dtimes[0:i + 1]) + times[i])
        velocities.append(velocities[-1])
        ax.step(np.arange(.5, len(velocities) + .5, 1), velocities, where='post')
        # ax.step(dtimes, velocities, where='post')
        ax.set_ylim(bottom=0)
        ax.set_ylim(top=max(velocities) * 1.1)
        ax.set_xticks(np.arange(1, len(velocities), 1))
        # ax.set_xticks(dtimes)
        xticks = np.arange(.5, len(velocities) + .5, 1)
        for i in range(len(dtimes)):
            # Эта методика округления нужна для нормального отображения результатов!
            # Ее не трогать!!! Это НЕ костыль!!!
            ax.text(xticks[i], velocities[i] - 1, str(round(dtimes[i], 2))[:-1])
        ax.set_xlabel('Number of segment')
        # ax.set_xlabel('Time, h')
        ax.set_ylabel('Speed, knt')
        ax.grid()


def plot_time_speed(ax, path):
    """
    Makes speed plot
    :param ax: axes
    :param path: path, contains trajectory items
    :return:
    """
    if len(path['items']) > 0:
        velocities = [item['length'] / item['duration'] * 3600 for item in path["items"]]
        times = [item['duration'] for item in path["items"]]
        times = [0] + times + times[-1:]
        velocities = velocities[0:1] + velocities + velocities[-1:]
        ax.step(np.cumsum(times) + path['start_time'], velocities, where='post')
        ax.set_ylim(bottom=0)
        ax.set_ylim(top=max(velocities) * 1.1)
        ax.set_xlabel('Timestamp, s')
        ax.set_ylabel('Speed, knt')
        ax.grid()


def plot_from_files(maneuvers_file):
    if os.path.isfile(maneuvers_file):
        fig = plt.figure(figsize=(10, 7.5))
        gs1 = gridspec.GridSpec(5, 1)
        ax = fig.add_subplot(gs1[0:4, :])
        ax.clear()
        ax_vel = fig.add_subplot(gs1[4, :])
        ax_vel.clear()
        ax.set_facecolor((159 / 255, 212 / 255, 251 / 255))

        case = load_case_from_directory(os.path.dirname(maneuvers_file))

        if case.route is not None:
            plot_path(case.route, ax, color='#fffffffa')

        if case.constraints is not None:
            plot_case_limits(ax, case)

        radius = 1.5
        if case.settings is not None:
            radius = case.settings['maneuver_calculation']['safe_diverg_dist'] * .5

        plot_case_paths(ax, case)
        ax.axis('equal')
        if case.maneuvers is not None:
            plot_speed(ax_vel, case.maneuvers[0]['path'])
            total_time = path_time(case.maneuvers[0]['path'])
            start_time = case.maneuvers[0]['path']['start_time']
            t = total_time + start_time
        else:
            total_time = path_time(case.targets_maneuvers[0])
            start_time = case.targets_maneuvers[0]['start_time']
            t = total_time + start_time

        h, m, s = math.floor(total_time / 3600), math.floor(total_time % 3600 / 60), total_time % 60
        ax.set_title('t=({:.0f}): {:.0f} h {:.0f} min {:.0f} sec'.format(t, h, m, s))
        ax.grid()

        plot_case_positions(ax, case, start_time, radius=radius)
        ax.legend()

        if case.maneuvers is not None:
            xlim, ylim = recalc_lims(case.maneuvers[0]['path'])
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

        return fig
    else:
        raise FileNotFoundError("{} not found".format(maneuvers_file))


def find_max_time(data):
    """
    Finds minimal time
    :param data: trajs file
    :return: minimal time from epoch
    """
    return max([path['start_time'] for path in data])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test scenario plotter")
    # parser.add_argument("casefile", type=str, help="Name of file or folder, when -a is used")
    # parser.add_argument("-a", action="store_true", help="Makes all files")
    # parser.add_argument("-s", action="store_true", help="Show image")
    args = parser.parse_args()

    figure = plot_from_files("maneuver.json")
    plt.show()
