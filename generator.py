import itertools
import json
import os
import time
from math import pi, sin, cos, sqrt, degrees
from multiprocessing import Pool
from pathlib import Path
from random import random, vonmisesvariate

import numpy as np
import pandas as pd
from natsort import natsorted

from konverter import Frame
from paintall import Vector2


# TODO: cythonize it!


def det(a, b):
    """
    Pseudoscalar multiply of vectors
    :param a: 2D vector
    :param b: 2D vector
    :return: pseudoscalar multiply
    """
    return a.x * b.y - b.x * a.y


def calc_cpa_params(v, v0, R):
    """
    Calculating of CPA and tCPA criterions
    :param v: target speed, vector
    :param v0: our speed, vector
    :param R: relative position, vector
    :return:
    """
    w = v - v0
    cpa = abs(det(R, w) / abs(w))
    tcpa = - (R * w) / (w * w)
    return cpa, tcpa


class Generator(object):
    def __init__(self, max_dist, min_dist, N_rand, n_tests, safe_div_dist, n_targets=2, lat=56.6857, lon=19.632):
        self.dist = max_dist
        self.min_dist = min_dist
        self.n_rand = N_rand
        self.sdd = safe_div_dist
        self.danger_points = []
        self.boost = int(1e2)
        self.n_targets = n_targets
        self.our_vel = 0
        self.frame = Frame(lat, lon)
        self.t2_folder = None
        self.abs_t2_folder = None
        self.n_tests = n_tests

    def create_tests(self):
        step = 0.5
        dists = np.arange(self.min_dist, self.dist + step * .5, step)
        # Is used to provide algorithm to work more correctly
        # for i in range(N):
        #     if dists[i] == 12:
        #         dists[i] = 11.9
        print("Start generating danger points...")
        exec_time = time.time()
        with Pool() as p:
            res = p.map(self.create_danger_points, dists)

        self.danger_points = list(itertools.chain.from_iterable(res))
        print(f'Danger Point generated.\nTotal time: {time.time() - exec_time}')
        print(f'Total points: {len(self.danger_points)}')
        exec_time1 = time.time()
        print("Start generating tests...")
        # ns = [i for i in range(0, len(self.danger_points))]
        # with Pool() as p:
        # p.map(self.create_targets, ns)
        table_rows = [self.create_case(i) for i in range(len(self.danger_points))]
        df = pd.DataFrame(table_rows, columns=['datadir', 'dist1', 'course1', 'peleng1', 'speed1',
                                               'dist2', 'course2', 'peleng2', 'speed2',
                                               'safe_diverg', 'speed'])

        print(f'Tests generated.\nTime: {time.time() - exec_time1},\n Total time: {time.time() - exec_time}')
        print(f'{len(df)} tests were generated for {self.n_targets} target(s)')
        return df

    def create_case(self, i):
        self.our_vel = self.danger_points[i]['v_our']
        targets = []
        targets.append(self.danger_points[i])
        if self.n_targets == 2:
            for j in range(i, len(self.danger_points)):
                [dang, v1, v2, CPA, TCPA] = self.dangerous(self.danger_points[j]['dist'],
                                                           self.danger_points[j]['course'],
                                                           self.danger_points[j]['c_diff'],
                                                           self.our_vel)
                if not dang:
                    continue
                else:
                    record = {"course": self.danger_points[j]['course'],
                              "dist": self.danger_points[j]['dist'],
                              "c_diff": self.danger_points[j]['c_diff'],
                              "v_our": v1,
                              "v_target": v2,
                              "CPA": CPA,
                              "TCPA": TCPA}
                    targets.append(record)
                    f_name = ("sc_" + str(targets[0]['dist']) + "_" + str(targets[1]['dist']) + "_" +
                              str(round(targets[0]['v_target'], 1)) + "_" +
                              str(round(targets[1]['v_target'], 1)) + "_" +
                              str(round(self.our_vel, 1)) + "_" + str(round(targets[0]['c_diff'], 1)) + "_" +
                              str(round(targets[1]['c_diff'], 1)) + "_" + str(round(targets[0]['CPA'], 1)) +
                              "_" + str(round(targets[1]['CPA'], 1)) + "_" + str(round(targets[0]['TCPA'], 1)) +
                              "_" + str(round(targets[1]['TCPA'], 1)))
                    # self.construct_files(f_name, targets)
                    return self.construct_table_row(f_name, targets)
                    del targets[1]
        elif self.n_targets == 1:
            f_name = ("sc_" + str(targets[0]['dist']) + "_0_" +
                      str(round(targets[0]['v_target'], 1)) + "_0_" +
                      str(round(self.our_vel, 1)) + "_" + str(round(targets[0]['c_diff'], 1)) + "_0_" +
                      str(round(targets[0]['CPA'], 1)) +
                      "_0_" + str(round(targets[0]['TCPA'], 1)) + "_0")
            # self.construct_files(f_name, targets)
            return self.construct_table_row(f_name, targets)

    def construct_table_row(self, f_name, targets):
        """
        Constructs all xlsx or csv files
        @param f_name:
        @param targets:
        @return:
        """
        try:
            dist1 = targets[0]['dist']
            course1 = targets[0]['c_diff']
            peleng1 = targets[0]['course']
            speed1 = targets[0]['v_target']
        except IndexError or TypeError:
            dist1 = 0
            course1 = 0
            peleng1 = 0
            speed1 = 0

        try:
            dist2 = targets[1]['dist']
            course2 = targets[1]['c_diff']
            peleng2 = targets[1]['course']
            speed2 = targets[1]['v_target']
        except IndexError or TypeError:
            dist2 = 0
            course2 = 0
            peleng2 = 0
            speed2 = 0

        if not ((dist1 == dist2) & (course1 == course2) & (peleng1 == peleng2)):
            times = [f_name,
                     dist1,
                     course1,
                     peleng1,
                     speed1,
                     dist2,
                     course2,
                     peleng2,
                     speed2,
                     self.sdd,
                     targets[0]['v_our']]

            return times
        else:
            return None

    def create_danger_points(self, dist):
        """
        Creates danger points to specified distance
        @param dist: distance
        @return:
        """
        danger_points = []
        while len(danger_points) < self.n_tests:
            tar_c = -pi + vonmisesvariate(0, 0)
            t_c_diff = -pi + vonmisesvariate(0, 0)
            [is_dang, v0, vt, CPA, TCPA] = self.dangerous(dist, tar_c, t_c_diff)
            # Normalized true course difference
            n_tcd = 0
            if t_c_diff >= 0:
                n_tcd = degrees(t_c_diff)
            else:
                n_tcd = degrees(t_c_diff + 2 * pi)
            if is_dang:
                record = {"course": degrees(tar_c),
                          "dist": dist,
                          "c_diff": n_tcd,
                          "v_our": v0,
                          "v_target": vt,
                          "CPA": CPA,
                          "TCPA": TCPA}
                danger_points.append(record)
        return danger_points

    def dangerous(self, dist, peleng, course_diff, v1=None):
        """
        Checks, if point is dangerous.
        @param v1: our velocity
        @param dist: distance to target
        @param peleng: target peleng
        @param course_diff: course difference
        @return: [is_dangerous, our_vel, tar_vel]
        """
        v_min = 2
        v_max = 20
        alpha = peleng
        beta = course_diff
        fix_sp = False
        v2 = 0
        if v1 is not None:
            fix_sp = True
        else:
            v1 = 0
        for i in range(self.n_rand):
            try:
                if not fix_sp:
                    v1 = v_min + (v_max - v_min) * random()
                v2 = v_min + (v_max - v_min) * random()
                CPA, TCPA = self.get_CPA_TCPA(v1, v2, alpha, beta, dist)
                # TODO: fix it to non-eq operators
                if CPA <= self.sdd and 0 <= TCPA < 0.333333:
                    return [True, v1, v2, CPA, TCPA]
            except ZeroDivisionError or ValueError:
                continue
        return [False, v1, v2, -1, -1]

    def get_CPA_TCPA(self, v1, v2, course, diff, dist, method='KT'):
        if method == 'default':
            v_rel = sqrt(v1 ** 2 - 2 * v1 * v2 * cos(diff) + v2 ** 2)
            TCPA = -dist * (v2 * cos(course - diff) - v1 * cos(course)) / v_rel ** 2
            CPA = dist * abs(v2 * sin(course - diff) - v1 * sin(course)) / v_rel
            return CPA, TCPA
        elif method == 'KT':
            v_our = Vector2(v1, 0)
            v_target = Vector2(v2 * cos(diff), v2 * sin(diff))
            R = Vector2(dist * cos(course), dist * sin(course))
            return calc_cpa_params(v_target, v_our, R)

    # Files


class FilderGenerator:

    def __init__(self, max_dist, min_dist, N_dp, N_rand, n_tests, safe_div_dist, n_targets=2, foldername="./scenars1",
                 lat=56.6857, lon=19.632, n_stack=3000):
        self.dist = max_dist
        self.min_dist = min_dist
        self.n_dp = N_dp
        self.n_rand = N_rand
        self.sdd = safe_div_dist
        self.danger_points = []
        self.boost = int(1e2)
        self.n_targets = n_targets
        self.our_vel = 0
        self.frame = Frame(lat, lon)
        self.t2_folder = None
        self.abs_t2_folder = None
        self.foldername = foldername
        self.abs_foldername = None
        self.dirlist = None
        self.cwd = os.getcwd()
        self.n_stack = n_stack
        self.n_tests = n_tests
        self.metainfo = pd.DataFrame(columns=['datadir'])
        N = int((max_dist - min_dist) / 0.5)
        self.dists = [0 for i in range(N + 1)]
        # os.makedirs(self.foldername, exist_ok=True)
        # os.chdir(self.foldername)
        self.df = pd.DataFrame(columns=['datadir', 'dist1', 'course1', 'peleng1', 'speed1',
                                        'dist2', 'course2', 'peleng2', 'speed2',
                                        'safe_diverg', 'speed'])

    def construct_files(self, f_name, targets):
        """
        Constructs all json files
        @param f_name:
        @param targets:
        @return:
        """
        os.makedirs(f_name, exist_ok=True)
        with open(f_name + '/constraints.json', "w") as fp:
            json.dump(self.construct_constrains(), fp)
        with open(f_name + '/hmi-data.json', "w") as fp:
            json.dump(self.construct_hmi_data(), fp)
        with open(f_name + '/nav-data.json', "w") as fp:
            json.dump(self.construct_nav_data(), fp)
        with open(f_name + '/route-data.json', "w") as fp:
            json.dump(self.construct_route_data(), fp)
        with open(f_name + '/settings.json', "w") as fp:
            json.dump(self.construct_settings(), fp)
        with open(f_name + '/target-data.json', "w") as fp:
            json.dump(self.construct_target_data(targets), fp)
        with open(f_name + '/target-settings.json', "w") as fp:
            json.dump(self.construct_target_settings(), fp)

    def construct_target_data(self, targets):
        t_data = []
        for i, target in enumerate(targets):
            lat, lon = self.frame.to_wgs_azi(target['course'], target['dist'])
            payload = {
                "id": "target" + str(i),
                "cat": 0,
                "lat": lat,
                "lon": lon,
                "SOG": target['v_target'],
                "COG": target['c_diff'],
                "heading": target['c_diff'],
                "peleng": target['course'],
                "first_detect_dist": 5.0,
                "cross_dist": 0,
                "width": 16.0,
                "length": 100.0,
                "width_offset": 10.0,
                "length_offset": 15.0,
                "timestamp": 1594730134
            }
            t_data.append(payload)
        return t_data

    @staticmethod
    def construct_constrains():
        payload = {
            "type": "FeatureCollection",
            "features": []
        }
        return payload

    @staticmethod
    def construct_hmi_data():
        payload = {
            "wind_direction": 189.0,
            "wind_speed": 1.1,
            "tide_direction": 0.0,
            "tide_speed": 0.0,
            "swell": 1.0,
            "visibility": 13.0
        }
        return payload

    def construct_nav_data(self):
        payload = {
            "cat": 0,
            "lat": self.frame.lat,
            "lon": self.frame.lon,
            "SOG": self.our_vel,
            "STW": self.our_vel,
            "COG": 0.0,
            "heading": 0.0,
            "width": 16.0,
            "length": 100.0,
            "width_offset": 10.0,
            "length_offset": 15.0,
            "timestamp": 1594730134
        }
        return payload

    def construct_route_data(self):
        payload = {
            "items": [
                {
                    "begin_angle": 0.0,
                    "curve": 0,
                    "duration": 120.0 / self.our_vel * 3600,
                    "lat": self.frame.lat,
                    "lon": self.frame.lon,
                    "length": 120.0,
                    "port_dev": 1.5,
                    "starboard_dev": 1.5,
                }
            ],
            "start_time": 1594730134
        }
        return payload

    def construct_settings(self):
        payload = {
            "maneuver_calculation": {
                "priority": 0,
                "maneuver_way": 0,
                "safe_diverg_dist": self.sdd,
                "minimal_speed": 3.0,
                "maximal_speed": 30.0,
                "max_course_delta": 180,
                "time_advance": 300,
                "can_leave_route": True,
                "max_route_deviation": 4,
                "forward_speed1": 3.0,
                "forward_speed2": 9.75,
                "forward_speed3": 16.5,
                "forward_speed4": 23.25,
                "forward_speed5": 30.0,
                "reverse_speed1": 15.0,
                "reverse_speed2": 30.0,
                "max_circulation_radius": 0.3,
                "min_circulation_radius": 0.3,
                "breaking_distance": 0,
                "run_out_distance": 0,
                "forecast_time": 14400,
                "min_diverg_dist": 1.8
            },
            "safety_control": {
                "cpa": 2.0,
                "tcpa": 900,
                "min_detect_dist": 9.0,
                "last_moment_dist": 2.0,
                "safety_zone": {
                    "safety_zone_type": 0,
                    "radius": 1.0
                }
            }
        }
        return payload

    def construct_target_settings(self):
        payload = {
            "maneuver_calculation": {
                "priority": 0,
                "maneuver_way": 2,
                "safe_diverg_dist": self.sdd,
                "minimal_speed": 3.0,
                "maximal_speed": 30.0,
                "max_course_delta": 180,
                "time_advance": 300,
                "can_leave_route": True,
                "max_route_deviation": 8,
                "forward_speed1": 3.0,
                "forward_speed2": 9.75,
                "forward_speed3": 16.5,
                "forward_speed4": 23.25,
                "forward_speed5": 30.0,
                "reverse_speed1": 15.0,
                "reverse_speed2": 30.0,
                "max_circulation_radius": 0.1,
                "min_circulation_radius": 0.1,
                "breaking_distance": 0,
                "run_out_distance": 0,
                "forecast_time": 14400,
            },
            "safety_control": {
                "cpa": 2.0,
                "tcpa": 900,
                "min_detect_dist": 9.0,
                "last_moment_dist": 2.0,
                "safety_zone": {
                    "safety_zone_type": 0,
                    "radius": 1.0
                }
            }
        }
        return payload

    def get_dir_list(self, typo=1):
        directories_list = []
        if typo == 1:
            os.chdir(self.cwd)
            os.chdir(self.foldername)
        else:
            os.chdir(self.cwd)
            os.chdir(self.t2_folder)
        for path in Path(os.getcwd()).glob('*'):
            for root, dirs, files in os.walk(path):
                if "nav-data.json" in files or 'navigation.json' in files:
                    directories_list.append(os.path.join(self.foldername, root))
        self.dirlist = natsorted(directories_list)
        os.chdir(self.cwd)

    @staticmethod
    def get_target_data(dirname):
        os.chdir(dirname)
        data = None
        with open('target-data.json', 'r') as fp:
            data = json.load(fp)
        return data[0]

    def build_foldername(self, dir, target):
        dir = dir.split(sep='_')
        dir[2] = str(round(self.frame.dist_azi_to_point(target['lat'], target['lon'])[0], 1))
        dir[4] = str(round(target['SOG'], 1))
        dir[7] = str(round(target['COG'], 1))
        strs = ''
        for s in dir:
            strs += s + '_'
        return strs[:-1]


def save_table(df, filename):
    print(f'Tests were saved to {os.path.abspath(filename)}.')
    df.to_csv(filename)


if __name__ == "__main__":
    gen = Generator(12, 3.5, 1000, safe_div_dist=1, n_tests=200000, n_targets=1)
    tests_df = gen.create_tests()
    save_table(tests_df, 'tests.csv')
