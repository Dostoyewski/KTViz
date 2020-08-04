import glob
import json
import os

from math import cos, sin, radians

from plot import Frame


def reverse_time_xy(x, y, speed, course, time):
    return x - speed * time * cos(radians(course)), y - speed * time * sin(radians(course))


def reverse_time(lat, lon, speed, course, time):
    frame = Frame(lat, lon)
    x, y, dist, angle = frame.from_wgs(lat, lon)
    x, y = reverse_time_xy(x, y, speed, course, time)
    return frame.to_wgs(x, y)


def move_route(route_data, dx, dy):
    lat, lon = route_data['items'][0]['lat'], route_data['items'][0]['lon']
    frame = Frame(lat, lon)
    for i in range(len(route_data['items'])):
        lat, lon = route_data['items'][i]['lat'], route_data['items'][i]['lon']
        x, y, dist, angle = frame.from_wgs(lat, lon)
        x, y = x + dx, y + dy
        route_data['items'][i]['lat'], route_data['items'][i]['lon'] = frame.to_wgs(x, y)
    return route_data


def update_settings(nav_data_f, route_data_f, targets_data_f, settings_data_f):
    with open(settings_data_f, 'r') as f:
        settings_data = json.load(f)

    with open(nav_data_f, 'r') as f:
        nav_data = json.load(f)

    time_advance = settings_data['maneuver_calculation']['time_advance']

    lat, lon = reverse_time(nav_data['lat'], nav_data['lon'], nav_data['SOG'] / 3600, nav_data['COG'], time_advance)
    dx, dy = -nav_data['SOG'] / 3600 * time_advance * cos(radians(nav_data['COG'])), \
             -nav_data['SOG'] / 3600 * time_advance * sin(radians(nav_data['COG']))
    nav_data['lat'], nav_data['lon'] = lat, lon

    with open(route_data_f, 'r') as f:
        route_data = json.load(f)
    route_data = move_route(route_data, dx, dy)
    # route_data['start_time'] = route_data['start_time'] - time_advance

    with open(targets_data_f, 'r') as f:
        targets_data = json.load(f)
    for i in range(len(targets_data)):
        lat, lon = reverse_time(targets_data[i]['lat'], targets_data[i]['lon'],
                                targets_data[i]['SOG'] / 3600, targets_data[i]['COG'], time_advance)
        targets_data[i]['lat'], targets_data[i]['lon'] = lat, lon

    with open(nav_data_f, 'w') as f:
        json.dump(nav_data, f, indent=2)

    with open(targets_data_f, 'w') as f:
        json.dump(targets_data, f, indent=2)

    with open(route_data_f, 'w') as f:
        json.dump(route_data, f, indent=2)


def run_case(datadir):
    working_dir = os.path.abspath(os.getcwd())
    os.chdir(datadir)
    print(datadir)
    # Get a list of old results
    file_list = glob.glob('maneuver*.json') + glob.glob('nav-report.json')
    for filePath in file_list:
        try:
            os.remove(filePath)
        except OSError:
            pass

    update_settings('nav-data.json', 'route-data.json', 'target-data.json', 'settings.json')
    os.chdir(working_dir)


def run(data_directory):
    for root, dirs, files in os.walk(data_directory):
        if "nav-data.json" in files or 'navigation.json' in files:
            run_case(os.path.join(data_directory, root))


if __name__ == "__main__":
    cur_dir = os.path.abspath(os.getcwd())
    run(cur_dir)
