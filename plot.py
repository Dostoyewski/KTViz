import argparse
from collections import namedtuple

import numpy as np
from math import sin, cos, radians, degrees
from matplotlib import pyplot as plt, gridspec
from matplotlib.patches import Ellipse, Polygon

from app import *
from konverter import Frame

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


def plot_limits(ax, filename, frame=None):
    """
    This function plots navigation limits
    :param frame: frame to convert
    :param ax: axes
    :param filename: file with limitations
    :return:
    """
    with open(filename) as f:
        data = json.loads(f.read())
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
        ax.add_patch(Ellipse([coords[1], coords[0]], dist, dist, fill=False,
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


def check_multiply_trajs(filename):
    """
    Checks, if it is more, than one traj in file
    :param filename:
    :return:
    """
    with open(filename) as f:
        file_data = json.loads(f.read())
    try:
        data = [file_data[0]['path']]
        if len(file_data) > 1:
            return True
    except:
        pass
    return False


def get_path_info(filename, solver):
    """

    :param filename:
    :param solver:
    :return:
    """
    with open(filename) as f:
        file_data = json.loads(f.read())
    return file_data[solver]['solver_name'], file_data[solver]['msg']


def prepare_file(filename, solver=0, has_maneuver=True):
    """
    Prepares data from file to plot
    :param has_maneuver: if has maneuver.json
    :param filename: name of file
    :param solver: index of solution (if exist)
    :return: path, convertation frame, new_format flag
    """
    new_format = False
    if has_maneuver:
        with open(filename) as f:
            file_data = json.loads(f.read())
    else:
        file_data = [{'path': []}, {'path': []}]
    try:
        # If new format
        data = [file_data[solver]['path']]
        if DEBUG:
            print('New type detected')
        dirname = os.path.split(filename)[0]
        if DEBUG:
            print('Path: ', dirname)
        try:
            with open(os.path.join(dirname, 'target-maneuvers.json')) as f:
                target_data = json.loads(f.read())
                data.extend(target_data)
                if DEBUG:
                    print('Loaded target data')
        except FileNotFoundError:
            try:
                with open(os.path.join(dirname, 'predicted_tracks.json')) as f:
                    target_data = json.loads(f.read())
                    data.extend(target_data)
                    if DEBUG:
                        print('Loaded target data')
            except FileNotFoundError:
                if DEBUG:
                    print("target data does not exist!!!")
        has_real = False
        try:
            with open(os.path.join(dirname, 'real-target-maneuvers.json')) as f:
                real_target_data = json.loads(f.read())
                if DEBUG:
                    print('Loaded real target data')
            for obj in real_target_data:
                # Flag if real
                obj['real'] = True
            data.extend(real_target_data)
            has_real = True
        except FileNotFoundError:
            pass
        need_add_flag = False
        try:
            # Loading data from new solver
            if solver == 0:
                solver_new = 1
            else:
                solver_new = 0
            data_new = file_data[solver_new]['path']
            data.append(data_new)
            need_add_flag = True
        except:
            pass
        new_format = True
    except KeyError:
        if DEBUG:
            print('Format set to old')
        data = file_data
    # Sample initial position to anchor Frame
    try:
        sample = data[0]['items'][0]
        if 'lat' in sample and 'lon' in sample:
            key1, key2 = 'lat', 'lon'
            frame = Frame(data[0]['items'][0][key1], data[0]['items'][0][key2])
    except TypeError:
        if not has_maneuver:
            with open(filename) as f:
                file_data = json.loads(f.read())
            lat, lon = file_data['items'][0]['lat'], file_data['items'][0]['lon']
        frame = Frame(lat, lon)
    else:
        raise KeyError('No coords in maneuver')

    # Prepare data
    paths = []
    for obj in data:
        try:
            new_data = prepare_path(obj, frame=frame)
            paths.append(new_data)
        except TypeError:
            pass
    if need_add_flag:
        paths[-1]['second'] = True
    if has_real:
        for i in range(len(data)):
            try:
                # Copying 'real' flags from data
                if data[i]['real']:
                    paths[i]['real'] = True
            except KeyError:
                pass
    return paths, frame, new_format


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


def plot_poly(ax, file, frame):
    with open(file) as f:
        poly_data = json.loads(f.read())


def get_positions(data, t):
    return [path_position(path, t) for path in data]


def plot_nav_points(ax, nav_file, target_file, frame):
    """
    Plots current positions from nav-data file
    :param frame: converter frame
    :param target_file: target-data file
    :param ax: mtplb axes
    :param nav_file: nav-data file
    :return:
    """
    with open(nav_file) as f:
        nav_data = json.loads(f.read())
    with open(target_file) as f:
        target_data = json.loads(f.read())
    target_data.append(nav_data)
    for obj in target_data:
        out = frame.from_wgs(obj['lat'], obj['lon'])
        x, y = out[0], out[1]
        # Dummy fix:
        if abs(x) > 1500 or abs(y) > 1500:
            out = frame.from_wgs(obj['lon'], obj['lat'])
            x, y = out[0], out[1]
        ax.scatter(y, x, color='black', marker='x')
        ax.text(y, x, str(obj['timestamp']))


def plot_positions(ax, positions, radius=1.5, coords=False, frame=None, two_trajs=False,
                   real_trajs=False, only_real=False, has_maneuver=True):
    """
    Plots ships positions
    :param has_maneuver: if has maneuver.json
    :param only_real: flag if has only real-target-maneuvers
    :param ax: plot axes
    :param positions: array with positions
    :param radius: safe radius
    :param coords: if needs to konvert from local to WGS84
    :param frame: frame
    :param two_trajs: if has two trajs from different solvers
    :param real_trajs: if has real-target-maneuvers.json
    :return:
    """
    for i, position in enumerate(positions):
        if not has_maneuver:
            i += 1
        if position.x is not None:
            if real_trajs and i > len(positions) / 2 and not only_real and i != 0:
                label_text = 'real-#{}, {:.2f}knt,{:.2f}°'.format(int(i - len(positions) / 2 + 0.5),
                                                                  position.vel * 3600, position.course)
            else:
                if only_real and i != 0:
                    label_text = 'real-#{}, {:.2f}knt,{:.2f}°'.format(i, position.vel * 3600, position.course)
                else:
                    label_text = '#{}, {:.2f}knt,{:.2f}°'.format(i, position.vel * 3600, position.course)
            if coords:
                if frame is not None:
                    lat, lon = frame.to_wgs(position.x, position.y)
                    label_text += '\n{:.4f}°, {:.4f}°'.format(lat, lon)
                else:
                    label_text += '\n{:.4f}, {:.4f}'.format(position.x, position.y)
            if two_trajs and i == len(positions) - 1:
                plot_position(position.x, position.y, position.course, ax, radius=radius,
                              color='darkCyan',
                              label=label_text)
            else:
                plot_position(position.x, position.y, position.course, ax, radius=radius,
                              color=('red' if i == 0 else 'blue'),
                              label=label_text)

            if real_trajs and i > len(positions) / 2 and not only_real and i != 0:
                ax.text(position.y, position.x, 'real-#{}'.format(int(i - len(positions) / 2 + 0.5), size=8))
            else:
                if only_real and i != 0:
                    ax.text(position.y, position.x, 'real-#{}'.format(i, size=8))
                else:
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


def plot_speed(ax, path):
    """
    Makes speed plot
    :param ax: axes
    :param path: path, contains trajectory items
    :return:
    """
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


def plot_from_files(maneuvers_file, route_file=None, poly_file=None, settings_file=None):
    if os.path.isfile(maneuvers_file):
        fig = plt.figure(figsize=(10, 7.5))
        gs1 = gridspec.GridSpec(5, 1)
        ax = fig.add_subplot(gs1[0:4, :])
        ax.clear()
        ax_vel = fig.add_subplot(gs1[4, :])
        ax_vel.clear()
        ax.set_facecolor((159 / 255, 212 / 255, 251 / 255))

        data, frame, new_format = prepare_file(maneuvers_file)
        if new_format:
            has_two_trajs = plot.check_multiply_trajs(maneuvers_file)
            data, frame, new_format = plot.prepare_file(maneuvers_file, solver=0)
            if has_two_trajs:
                data2, frame2, new_format = plot.prepare_file(maneuvers_file, solver=1)

            solver_info, info_msg = plot.get_path_info(maneuvers_file, 0)
        else:
            has_two_trajs = False
            solver_info, info_msg = "", ""

        if route_file is not None:
            plot_route(ax, route_file, frame)

        try:
            if poly_file is not None:
                plot.plot_limits(ax, poly_file, frame)
        except FileNotFoundError:
            pass

        radius = 1.5
        try:
            if settings_file is not None:
                settings_file = 'settings.json'
                with open(settings_file) as f:
                    settings_data = json.loads(f.read())
                    radius = settings_data['maneuver_calculation']['safe_diverg_dist'] * .5
        except FileNotFoundError:
            pass

        plot_maneuvers(ax, data)
        if has_two_trajs:
            plot_path(data2[0], ax, 'red')
        plot_speed(ax_vel, data[0])

        ax.axis('equal')
        total_time = sum([x['duration'] for x in data[0]['items']])
        t = total_time + data[0]['start_time']
        h, m, s = math.floor(total_time / 3600), math.floor(total_time % 3600 / 60), total_time % 60
        ax.set_title('t=({:.0f}): {:.0f} h {:.0f} min {:.0f} sec'.format(t, h, m, s))
        ax.grid()

        start_time = data[0]['start_time']
        try:
            positions = get_positions(data, start_time)
        except KeyError:
            start_time = find_max_time(data)
            positions = get_positions(data, start_time)
        plot_positions(ax, positions, radius=radius)
        ax.legend()

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

    figure = plot_from_files("maneuver.json", route_file="route-data.json")
    plt.show()
