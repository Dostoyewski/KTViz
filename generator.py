import time
from math import pi, sin, cos, sqrt, degrees
from multiprocessing import Pool
from random import random

from konverter import Frame


class Generator(object):
    def __init__(self, max_dist, N_dp, N_rand, safe_div_dist, n_targets=1, lat=56.6857, lon=19.6321):
        self.dist = max_dist
        self.n_dp = N_dp
        self.n_rand = N_rand
        self.sdd = safe_div_dist
        self.danger_points = []
        self.n_targets = n_targets
        self.frame = Frame(lat, lon)

    def create_tests(self):
        step = 0.5
        N = int((self.dist - 5) / step)
        dists = [self.dist - i * step for i in range(N)]
        print("Start generating tests...")
        exec_time = time.time()
        with Pool() as p:
            res = p.map(self.create_danger_points, dists)
        for r in res:
            self.danger_points.extend(r)
        print(f'Total time: {time.time() - exec_time}')

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

    def dangerous(self, dist, course, diff):
        """
        Checks, if point is dangerous.
        @param dist: distance to target
        @param course: target course
        @param diff: course diff
        @return: [is_dangerous, our_vel, tar_vel]
        """
        v_min = 3
        v_max = 20
        alpha = course
        beta = diff
        is_dang = False
        v1, v2 = 0, 0
        for i in range(self.n_rand):
            try:
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


if __name__ == "__main__":
    gen = Generator(12, 100, 3000, 2)
    gen.create_tests()
    print(len(gen.danger_points))
