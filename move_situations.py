import glob
import json
import os
import pandas as pd
from geographiclib.geodesic import Geodesic
import math


def find_cases(root_dir='.'):
    result = []
    for dir, dirs, files in os.walk(root_dir):
        if "nav-data.json" in files or 'navigation.json' in files:
            result.append(os.path.join(root_dir if root_dir != '.' else '', dir))
    return result


def our_coords_course(case_dir):
    with open(os.path.join(case_dir, 'nav-data.json')) as f:
        nav_data = json.load(f)
    return nav_data['lat'], nav_data['lon'], nav_data['COG']


def prepare_table(root_dir='.'):
    cases = find_cases(root_dir)
    cases_info = [our_coords_course(case_dir) for case_dir in cases]
    lats, lons, cogs = zip(*cases_info)
    d = {'dir': cases, 'lat': lats, 'lon': lons, 'cog': cogs}
    df = pd.DataFrame(data=d)
    return df


def move_point(lat, lon, lat1, lon1, lat2, lon2, da):
    path = Geodesic.WGS84.Inverse(lat1, lon1, lat, lon)
    path = Geodesic.WGS84.Direct(lat2, lon2, math.fmod(path['azi1'] + da, 360.0), path['s12'])
    return path['lat2'], path['lon2']


def move_path(path, lat1, lon1, lat2, lon2, dcog):
    for i, item in enumerate(path['items']):
        length = item['length']
        b_cos = math.cos(math.radians(item['begin_angle']))
        b_sin = math.sin(math.radians(item['begin_angle']))
        if i == 0:
            end_lat, end_lon = move_point(item['lat'], item['lon'], lat1, lon1, lat2, lon2, dcog)

        item['lat'], item['lon'] = end_lat, end_lon
        item['begin_angle'] = math.fmod(item['begin_angle'] + dcog, 360.0)

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
        r = Geodesic.WGS84.Direct(lat2, lon2, azi1, dist)
        end_lat, end_lon = r['lat2'], r['lon2']

    return path


def data_move_real_target_maneuvers(case_dir, lat1, lon1, lat2, lon2, dcog):
    filename = os.path.join(case_dir, 'real-target-maneuvers.json')
    with open(filename) as f:
        paths_data = json.load(f)

    new_paths = []
    for path in paths_data:
        new_paths.append(move_path(path, lat1, lon1, lat2, lon2, dcog))

    with open(filename, 'w') as f:
        json.dump(new_paths, f, indent='\t')
        print('rewrite: {}'.format(filename))


def data_move_route_data(case_dir, lat1, lon1, lat2, lon2, dcog):
    filename = os.path.join(case_dir, 'route-data.json')
    with open(filename) as f:
        route_data = json.load(f)
    route_data = move_path(route_data, lat1, lon1, lat2, lon2, dcog)

    with open(filename, 'w') as f:
        json.dump(route_data, f, indent='\t')
        print('rewrite: {}'.format(filename))


def data_move_targets(case_dir, lat1, lon1, lat2, lon2, dcog):
    filename = os.path.join(case_dir, 'target-data.json')
    with open(filename) as f:
        target_data = json.load(f)
    for target in target_data:
        target['lat'], target['lon'] = move_point(target['lat'], target['lon'], lat1, lon1, lat2, lon2, dcog)
        target['COG'] = math.fmod(target['COG'] + dcog, 360.0)

    with open(filename, 'w') as f:
        json.dump(target_data, f, indent='\t')
        print('rewrite: {}'.format(filename))


def data_move_constraints(case_dir, lat1, lon1, lat2, lon2, dcog):
    filename = os.path.join(case_dir, 'constraints.json')
    with open(filename) as f:
        data = json.load(f)
    for feature in data['features']:
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

    with open(filename, 'w') as f:
        json.dump(data, f)
        print('rewrite: {}'.format(filename))


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

    data_move_targets(case_dir, lat1, lon1, lat_, lon_, dcog)
    data_move_route_data(case_dir, lat1, lon1, lat_, lon_, dcog)
    data_move_real_target_maneuvers(case_dir, lat1, lon1, lat_, lon_, dcog)
    data_move_constraints(case_dir, lat1, lon1, lat_, lon_, dcog)


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
    args = parser.parse_args()

    cur_dir = os.path.abspath(os.getcwd())

    if os.path.exists(args.index_file) and os.path.isfile(args.index_file):
        with open(args.index_file) as f:
            df = pd.read_csv(f, sep='\t', )
        process_table(df)

    else:
        df = prepare_table()
        with open(args.index_file, 'w') as f:
            df.to_csv(f, index=False, sep='\t', line_terminator='\n')

    if args.pretty:
        for directory, dirs, files in os.walk(cur_dir):
            file_list = glob.glob(os.path.join(directory, '*.json'))

            for file_path in file_list:
                print('Prettify {}'.format(file_path))
                with open(file_path) as f:
                    data = json.load(f)
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent='\t')

    print(df.to_string(index=False))
