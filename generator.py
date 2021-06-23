import json
import os
import time
from math import pi, sin, cos, sqrt, degrees
from multiprocessing import Pool
from random import random

from konverter import Frame


class Generator(object):
    def __init__(self, max_dist, N_dp, N_rand, safe_div_dist, n_targets=2, lat=56.6857, lon=19.632):
        self.dist = max_dist
        self.n_dp = N_dp
        self.n_rand = N_rand
        self.sdd = safe_div_dist
        self.danger_points = []
        self.n_targets = n_targets
        self.our_vel = 0
        self.frame = Frame(lat, lon)
        os.makedirs("./scenars", exist_ok=True)
        os.chdir("./scenars")

    def create_tests(self):
        step = 0.5
        N = int((self.dist - 5) / step)
        dists = [self.dist - i * step for i in range(N)]
        print("Start generating danger points...")
        exec_time = time.time()
        with Pool() as p:
            res = p.map(self.create_danger_points, dists)
        for r in res:
            self.danger_points.extend(r)
        print(f'Danger Point generated.\nTotal time: {time.time() - exec_time}')
        exec_time1 = time.time()
        print("Start generating tests...")
        ns = [i for i in range(len(self.danger_points))]
        with Pool() as p:
            p.map(self.create_targets)
        self.create_targets(500)
        print(f'Tests generated.\nTime: {time.time() - exec_time1},\n Total time: {time.time() - exec_time}')

    def create_targets(self, i):
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
                    f_name = ("./sc_" + str(targets[0]['dist']) + "_" + str(targets[1]['dist']) + "_" +
                              str(round(targets[0]['v_target'], 1)) + "_" +
                              str(round(targets[1]['v_target'], 1)) + "_" +
                              str(round(self.our_vel, 1)) + "_" + str(round(targets[0]['c_diff'], 1)) + "_" +
                              str(round(targets[1]['c_diff'], 1)))
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
                    del targets[1]

    def create_danger_points(self, dist):
        """
        Creates danger points to specified distance
        @param dist: distance
        @return:
        """
        danger_points = []
        for i in range(self.n_dp):
            for j in range(self.n_dp):
                tar_c = -pi + 2 * pi * i / self.n_dp
                t_c_diff = -pi + 2 * pi * j / self.n_dp
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

    def dangerous(self, dist, course, diff, v1=None):
        """
        Checks, if point is dangerous.
        @param v1: our velocity
        @param dist: distance to target
        @param course: target course
        @param diff: course diff
        @return: [is_dangerous, our_vel, tar_vel]
        """
        v_min = 3
        v_max = 20
        alpha = course
        beta = diff
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
                v_rel = sqrt(v1 ** 2 - 2 * v1 * v2 * cos(beta) + v2 ** 2)
                TCPA = -dist * (v2 * cos(alpha - beta) - v1 * cos(alpha)) / v_rel ** 2
                CPA = dist * abs(v2 * sin(alpha - beta) - v1 * sin(alpha)) / v_rel
                if CPA <= self.sdd and 0 <= TCPA < 0.3333333:
                    return [True, v1, v2, CPA, TCPA]
            except ZeroDivisionError or ValueError:
                continue
        return [False, v1, v2, -1, -1]

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
            "tide_direction": 0,
            "tide_speed": 0,
            "swell": 1,
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
                    "begin_angle": 0,
                    "curve": 0,
                    "duration": 120 / self.our_vel * 3600,
                    "lat": self.frame.lat,
                    "lon": self.frame.lon,
                    "length": 72.0,
                    "port_dev": 1.5,
                    "starboard_dev": 1.5,
                }
            ],
            "start_time": 1594730134
        }
        return payload

    @staticmethod
    def construct_settings():
        payload = {
            "maneuver_calculation": {
                "priority": 0,
                "maneuver_way": 0,
                "safe_diverg_dist": 2.0,
                "minimal_speed": 3,
                "maximal_speed": 30,
                "max_course_delta": 180,
                "time_advance": 300,
                "can_leave_route": 'true',
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

    @staticmethod
    def construct_target_settings():
        payload = {
            "maneuver_calculation": {
                "priority": 0,
                "maneuver_way": 2,
                "safe_diverg_dist": 2.4,
                "minimal_speed": 3,
                "maximal_speed": 30,
                "max_course_delta": 180,
                "time_advance": 1,
                "can_leave_route": 'true',
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


if __name__ == "__main__":
    gen = Generator(12, 100, 5000, 2)
    gen.create_tests()
    print(len(gen.danger_points))
