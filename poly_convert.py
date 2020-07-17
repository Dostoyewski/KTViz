#!/usr/bin/env python3
import glob
import json
import os

from geographiclib.geodesic import Geodesic

from plot import Frame


def is_too_far(lat1, lon1, lat2, lon2):
    path = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)
    return path['s12'] / 1852 > 300


def fix_polygon(feature, frame):
    lon, lat = feature['geometry']['coordinates'][0][0]
    if is_too_far(lat, lon, frame.lat, frame.lon):
        for coords in feature['geometry']['coordinates']:
            for point in coords:
                point[0], point[1] = point[1], point[0]

    return feature


def fix_linestring(feature, frame):
    lon, lat = feature['geometry']['coordinates'][0][0]
    if is_too_far(lat, lon, frame.lat, frame.lon):
        for coords in feature['geometry']['coordinates']:
            coords[0], coords[1] = coords[1], coords[0]

    return feature


def fix_point(feature, frame):
    lon, lat = feature['geometry']['coordinates']
    if is_too_far(lat, lon, frame.lat, frame.lon):
        feature['geometry']['coordinates'][0], feature['geometry']['coordinates'][1] = \
            feature['geometry']['coordinates'][1], feature['geometry']['coordinates'][0]

    return feature


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

    for i in range(len(data['features'])):
        data['features'][i] = fix_feature(data['features'][i], frame)

    with open(file, 'w') as f:
        json.dump(data, f)


def run_directory(datadir):
    os.chdir(datadir)

    # Get a list of old results
    # file_list = glob.glob('maneuver*.json') + glob.glob('nav-report.json')
    # and remove them
    # for filePath in file_list:
    #     try:
    #         os.remove(filePath)
    #     except OSError:
    #         pass

    with open(os.path.join(datadir, 'nav-data.json')) as f:
        nav_data = json.loads(f.read())
        frame = Frame(nav_data['lat'], nav_data['lon'])

    file_list = glob.glob('constraints*.json')
    for constr_file in file_list:
        check_constraints_file(constr_file, frame)


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
