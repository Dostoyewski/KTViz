import math
from geographiclib.geodesic import Geodesic


def positions(pos_angle, pos_dist):
    """
    Converts target position from course and distance to
    relative coordinates X and Y.
    :param pos_angle: course angle for target, degrees
    :param pos_dist: distance to target, nautical miles
    :return: relative coords X and Y
    """
    return round(pos_dist * math.cos(math.radians(pos_angle)), 2), \
           round(pos_dist * math.sin(math.radians(pos_angle)), 2)


def velocities(course, vel):
    """
    Converts target velocities from course and modulus
    to vector components Vx and Vy
    :param course: target course
    :param vel: modulus of target velocity
    :return: Vector components Vx and Vy
    """
    return round(vel * math.cos(math.radians(course)), 2), \
           round(vel * math.sin(math.radians(course)), 2)


def coords_relative(s_lat, s_lon, e_lat, e_lon):
    """
    Transforms geographical coords from lat/lon
    to relative x/y
    :param s_lat: start latitude
    :param s_lon: start longitude
    :param e_lat: end latitude
    :param e_lon: end longitude
    :return: relative coords X and Y
    """
    path = Geodesic.WGS84.Inverse(s_lat, s_lon, e_lat, e_lon)
    return positions(math.radians(path['azi1']), path['s12'] / 1852)
