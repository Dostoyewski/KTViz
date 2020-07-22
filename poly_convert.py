#!/usr/bin/env python3
import glob
import json
import os

from geographiclib.geodesic import Geodesic

from konverter import Frame


def is_too_far(lat1, lon1, lat2, lon2):
    path = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
    return path['s12'] / 1852 > 300


def fix_polygon(feature, frame):
    lon, lat = feature['geometry']['coordinates'][0][0]
    changed = False
    if is_too_far(lat, lon, frame.lat, frame.lon):
        for coords in feature['geometry']['coordinates']:
            for point in coords:
                point[0], point[1] = point[1], point[0]
        changed = True
    return feature, changed


def fix_linestring(feature, frame):
    lon, lat = feature['geometry']['coordinates'][0][0]
    changed = False
    if is_too_far(lat, lon, frame.lat, frame.lon):
        for coords in feature['geometry']['coordinates']:
            coords[0], coords[1] = coords[1], coords[0]
        changed = True
    return feature, changed


def fix_point(feature, frame):
    lon, lat = feature['geometry']['coordinates']
    changed = False
    if is_too_far(lat, lon, frame.lat, frame.lon):
        feature['geometry']['coordinates'][0], feature['geometry']['coordinates'][1] = \
            feature['geometry']['coordinates'][1], feature['geometry']['coordinates'][0]
        changed = True
    return feature, changed


def fix_feature(feature, frame):
    if feature['geometry']['type'] == 'Polygon':
        return fix_polygon(feature, frame)
    if feature['geometry']['type'] == 'Point':
        return fix_point(feature, frame)
    if feature['geometry']['type'] == 'LineString':
        return fix_linestring(feature, frame)


def check_constraints_file(file, frame):
    with open(file) as f:
        data = json.loads(f.read())

    any_changed = False
    for i in range(len(data['features'])):
        data['features'][i], changed = fix_feature(data['features'][i], frame)
        any_changed = any_changed or changed

    with open(file, 'w') as f:
        json.dump(data, f)

    if any_changed:
        print('{} fixed'.format(os.path.abspath(file)))
    return any_changed


def run_directory(datadir):
    os.chdir(datadir)

    with open(os.path.join(datadir, 'nav-data.json')) as f:
        nav_data = json.loads(f.read())
        frame = Frame(nav_data['lat'], nav_data['lon'])

    file_list = glob.glob('constraints*.json')
    any_changed = False
    for constr_file in file_list:
        changed = check_constraints_file(constr_file, frame)
        any_changed = any_changed or changed

    return any_changed


def fix_from_root(data_directory):
    for root, dirs, files in os.walk(data_directory):
        if "nav-data.json" in files:
            run_directory(os.path.join(data_directory, root))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BKS report generator")
    parser.add_argument("root_dir", type=str, nargs='?', help="Path cases root", default=os.getcwd())
    args = parser.parse_args()

    cur_dir = os.path.abspath(args.root_dir)

    fix_from_root(cur_dir)
