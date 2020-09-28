import json
import os
import pandas as pd
from geographiclib.geodesic import Geodesic
import math
from data_update import find_cases, prettify, process_json_file


def wrap_angle(angle):
    return math.fmod(angle + 360., 360.)


def our_coords_course(case_dir):
    with open(os.path.join(case_dir, 'nav-data.json')) as f:
        nav_data = json.load(f)
    return nav_data['lat'], nav_data['lon'], nav_data['COG']


def prepare_table(root_dir='.'):
    cases = find_cases(root_dir)
    cases_info = [our_coords_course(case_dir) for case_dir in cases]
    lats, lons, cogs = zip(*cases_info)
    d = {'dir': cases, 'lat': lats, 'lon': lons, 'cog': cogs}
    return pd.DataFrame(data=d)


def move_point(lat, lon, lat1, lon1, lat2, lon2, da):
    path = Geodesic.WGS84.Inverse(lat1, lon1, lat, lon)
    path = Geodesic.WGS84.Direct(lat2, lon2, wrap_angle(path['azi1'] + da), path['s12'])
    return path['lat2'], path['lon2']


def move_path(path, lat1, lon1, lat2, lon2, dcog):
    for i, item in enumerate(path['items']):
        length = item['length']
        if i == 0:
            end_lat, end_lon = move_point(item['lat'], item['lon'], lat1, lon1, lat2, lon2, dcog)

        item['lat'], item['lon'] = end_lat, end_lon
        item['begin_angle'] = wrap_angle(item['begin_angle'] + dcog)

        b_cos = math.cos(math.radians(item['begin_angle']))
        b_sin = math.sin(math.radians(item['begin_angle']))

        if item['curve'] == 0:
            dx, dy = round(length * b_cos, 2), round(length * b_sin, 2)
        else:
            # For arcs
            r = abs(1 / item['curve'])
            dangle = abs(length * item['curve'])
            sign = 1 if item['curve'] > 0 else -1
            x_, y_ = math.sin(dangle), sign * (1 - math.cos(dangle))
            dx, dy = r * (x_ * b_cos - y_ * b_sin), r * (x_ * b_sin + y_ * b_cos)

        azi1 = math.degrees(math.atan2(dy, dx))
        dist = (dx ** 2 + dy ** 2) ** .5
        r = Geodesic.WGS84.Direct(end_lat, end_lon, azi1, dist * 1852)
        end_lat, end_lon = r['lat2'], r['lon2']

    return path


def move_real_target_maneuvers_data(paths_data, lat1, lon1, lat2, lon2, dcog):
    new_paths = []
    for path in paths_data:
        new_paths.append(move_path(path, lat1, lon1, lat2, lon2, dcog))

    return new_paths


def move_route_data(route_data, lat1, lon1, lat2, lon2, dcog):
    return move_path(route_data, lat1, lon1, lat2, lon2, dcog)


def move_target_data(target_data, lat1, lon1, lat2, lon2, dcog):
    for target in target_data:
        target['lat'], target['lon'] = move_point(target['lat'], target['lon'], lat1, lon1, lat2, lon2, dcog)
        target['COG'] = wrap_angle(target['COG'] + dcog)
    return target_data


def move_constraints_data(data, lat1, lon1, lat2, lon2, dcog):
    for feature in data['features']:
        if 'min_course' in feature['properties']:
            feature['properties']['min_course'] = wrap_angle(feature['properties']['min_course'] + dcog)

        if 'max_course' in feature['properties']:
            feature['properties']['max_course'] = wrap_angle(feature['properties']['max_course'] + dcog)

        if feature['geometry']['type'] == 'Polygon':
            for coords in feature['geometry']['coordinates']:
                for point in coords:
                    point[1], point[0] = move_point(point[1], point[0], lat1, lon1, lat2, lon2, dcog)
        if feature['geometry']['type'] == 'Line':
            for coords in feature['geometry']['coordinates']:
                coords[1], coords[0] = move_point(coords[1], coords[0], lat1, lon1, lat2, lon2, dcog)
        if feature['geometry']['type'] == 'Line':
            feature['geometry']['coordinates'][1], feature['geometry']['coordinates'][0] = \
                move_point(feature['geometry']['coordinates'][1], feature['geometry']['coordinates'][0], lat1, lon1,
                           lat2, lon2, dcog)
    return data


def move_case(case_dir, lat_, lon_, cog_):
    nav_filename = os.path.join(case_dir, 'nav-data.json')
    with open(nav_filename) as f:
        nav_data = json.load(f)
    dcog = cog_ - nav_data['COG']
    lat1, lon1 = nav_data['lat'], nav_data['lon']
    nav_data['lat'], nav_data['lon'], nav_data['COG'], nav_data['heading'] = lat_, lon_, cog_, cog_
    with open(nav_filename, 'w') as f:
        json.dump(nav_data, f, indent='\t')
        print('rewrite: {}'.format(nav_filename))

    move_args = (lat1, lon1, lat_, lon_, dcog)
    process_json_file(os.path.join(case_dir, 'target-data.json'), move_target_data, move_args)
    process_json_file(os.path.join(case_dir, 'route-data.json'), move_route_data, move_args)
    process_json_file(os.path.join(case_dir, 'real-target-maneuvers.json'), move_real_target_maneuvers_data, move_args)
    process_json_file(os.path.join(case_dir, 'constraints.json'), move_constraints_data, move_args)


def process_table(table):
    for index, row in table.iterrows():
        try:
            lat, lon, cog = our_coords_course(row['dir'])
            if (lat, lon, cog) != (row['lat'], row['lon'], row['cog']):
                print('Found difference in {}'.format(row['dir']))
                print('Actual:')
                print('lat: {}, lon: {}, COG: {}', lat, lon, cog)
                print('From index:')
                print('lat: {}, lon: {}, COG: {}', row['lat'], row['lon'], row['cog'])
                move_case(row['dir'], row['lat'], row['lon'], row['cog'])
        except FileNotFoundError:
            print('{} not found'.format(row['dir']))
            df.drop(index, inplace=True)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Creates index file starting from working directory. If index already exists, tries to change "
                    "coordinates according to changes in index file.")
    parser.add_argument("index_file", type=str, help="Cases index file")
    parser.add_argument("--pretty", action="store_true", help="Pretty format all json files")
    arguments = parser.parse_args()

    cur_dir = os.path.abspath(os.getcwd())

    if os.path.exists(arguments.index_file) and os.path.isfile(arguments.index_file):
        with open(arguments.index_file) as f:
            df = pd.read_csv(f, sep='\t')
        process_table(df)

    else:
        df = prepare_table()
        with open(arguments.index_file, 'w') as f:
            df.to_csv(f, index=False, sep='\t', line_terminator='\n')

    if arguments.pretty:
        prettify(cur_dir)

    print(df.to_string(index=False))
