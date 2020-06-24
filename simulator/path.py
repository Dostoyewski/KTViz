import math
from collections import namedtuple
from geographiclib.geodesic import Geodesic


class Path:
    Position = namedtuple('Position', ['lat', 'lon', 'course', 'speed'])

    class Segment:
        def __init__(self, lat, lon, begin_angle, curve, length, duration, starboard_dev, port_dev):
            self.port_dev = port_dev
            self.starboard_dev = starboard_dev
            self.duration = duration
            self.length = length
            self.curve = curve
            self.begin_angle = begin_angle  # [degrees]
            self.lon = lon
            self.lat = lat

        def position(self, time):
            speed = self.length / self.duration
            length = speed * time

            if self.curve == 0:
                dist = length  # [miles]
                direct = Geodesic.WGS84.Direct(self.lat, self.lon, self.begin_angle, dist * 1852)
                return Path.Position(direct['lat2'], direct['lon2'], self.begin_angle, speed)
            else:
                # For arcs
                b_cos = math.cos(math.radians(self.begin_angle))
                b_sin = math.sin(math.radians(self.begin_angle))
                r = abs(1 / self.curve)
                dangle = abs(length * self.curve)
                sign = 1 if self.curve > 0 else -1
                x_, y_ = math.sin(dangle), sign * (1 - math.cos(dangle))
                dx, dy = r * (x_ * b_cos - y_ * b_sin), r * (x_ * b_sin + y_ * b_cos)
                dist = math.hypot(dx, dy)
                azi1 = math.atan2(dy, dx)
                direct = Geodesic.WGS84.Direct(self.lat, self.lon, math.degrees(azi1), dist * 1852)
                return Path.Position(direct['lat2'], direct['lon2'], self.begin_angle + sign * math.degrees(dangle),
                                     speed)

    def __init__(self, start_time=None):
        self.start_time = start_time
        self.items = []

    def load_from_array(self, array):
        self.start_time = array['start_time']
        for item in array['items']:
            self.items.append(Path.Segment(item['lat'], item['lon'], item['begin_angle'], item['curve'], item['length'],
                                           item['duration'], item['starboard_dev'], item['port_dev']))

    def dump_to_array(self):
        return {'start_time': self.start_time,
                'items': [{'lat': item.lat, 'lon': item.lon, 'begin_angle': item.begin_angle, 'curve': item.curve,
                           'length': item.length, 'duration': item.duration, 'starboard_dev': item.starboard_dev,
                           'port_dev': item.port_dev} for item in self.items]}

    def position(self, time):
        time = time - self.start_time
        if time >= 0:
            for item in self.items:
                if time < item.duration:
                    return item.position(time)
                time -= item.duration
        return Path.Position(None, None, None, None)
