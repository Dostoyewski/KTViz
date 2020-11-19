from shapely.geometry import shape, Point

import copy
import json
import math

# geojson-rewind
# https://github.com/chris48s/geojson-rewind
# MIT License
#
# Copyright (c) 2018 chris48s
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

RADIUS = 6378137


def rewind(geojson, rfc7946=True):
    gj = copy.deepcopy(geojson)
    if isinstance(gj, str):
        return json.dumps(_rewind(json.loads(gj), rfc7946))
    else:
        return _rewind(gj, rfc7946)


def _rewind(gj, rfc7946):
    if gj['type'] == 'FeatureCollection':
        gj['features'] = list(
            map(lambda obj: _rewind(obj, rfc7946), gj['features'])
        )
        return gj
    if gj['type'] == 'Feature':
        gj['geometry'] = _rewind(gj['geometry'], rfc7946)
    if gj['type'] in ['Polygon', 'MultiPolygon']:
        return correct(gj, rfc7946)
    return gj


def correct(feature, rfc7946):
    if feature['type'] == 'Polygon':
        feature['coordinates'] = correctRings(feature['coordinates'], rfc7946)
    if feature['type'] == 'MultiPolygon':
        feature['coordinates'] = list(
            map(lambda obj: correctRings(obj, rfc7946), feature['coordinates'])
        )
    return feature


def correctRings(rings, rfc7946):
    # change from rfc7946: True/False to clockwise: True/False here
    # RFC 7946 ordering determines how we deal with an entire polygon
    # but at this point we are switching to deal with individual rings
    # (which in isolation are just clockwise or anti-clockwise)
    clockwise = not (bool(rfc7946))
    rings[0] = wind(rings[0], clockwise)
    for i in range(1, len(rings)):
        rings[i] = wind(rings[i], not (clockwise))
    return rings


def wind(ring, clockwise):
    if is_clockwise(ring) == clockwise:
        return ring
    return ring[::-1]


def is_clockwise(ring):
    return ringArea(ring) >= 0


def ringArea(coords):
    area = 0
    coordsLength = len(coords)

    if coordsLength > 2:
        for i in range(0, coordsLength):
            if i == coordsLength - 2:
                lowerIndex = coordsLength - 2
                middleIndex = coordsLength - 1
                upperIndex = 0
            elif i == coordsLength - 1:
                lowerIndex = coordsLength - 1
                middleIndex = 0
                upperIndex = 1
            else:
                lowerIndex = i
                middleIndex = i + 1
                upperIndex = i + 2
            p1 = coords[lowerIndex]
            p2 = coords[middleIndex]
            p3 = coords[upperIndex]
            area = area + (rad(p3[0]) - rad(p1[0])) * math.sin(rad(p2[1]))

        area = area * RADIUS * RADIUS / 2

    return area


def rad(coord):
    return coord * math.pi / 180


# end geojson-rewind

def features_containing(data, lat, lon):
    # construct point based on lon/lat returned by geocoder
    point = Point(lon, lat)
    features = []
    # check each polygon to see if it contains the point
    for feature in data['features']:
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            features.append(feature)

    return features


def fix_linerings(data):
    for feature in data['features']:
        if feature['geometry']['type'] == 'Polygon':
            for coords in feature['geometry']['coordinates']:
                if coords[-1] != coords[0]:
                    coords.append(coords[0])
    return data


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Trying to fix constraints file i.e. close all LineRings")
    parser.add_argument("constraints_file", type=str, help="constraints file")
    parser.add_argument("--in-polygons", action="store_true", help="List Polygons containing our ship")
    arguments = parser.parse_args()

    file_path = arguments.constraints_file
    with open(file_path) as f:
        data = json.load(f)

    data = fix_linerings(data)
    data = _rewind(data, True)

    if arguments.in_polygons:
        with open("nav-data.json") as f:
            nav_data = json.load(f)

        contains = features_containing(data, nav_data['lat'], nav_data['lon'])
        for p in contains:
            print('Found containing polygon id: {}, source_id: {}'.format(p['properties']['id'],
                                                                          p['properties']['source_id']))

    with open(file_path, 'w') as f:
        json.dump(data, f)
