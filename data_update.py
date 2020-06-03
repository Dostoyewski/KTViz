import json
import os
import glob


def update_settings(filename):
    with open(filename, 'r') as f:
        settings = json.load(f)

    if not ('forward_speed1' in settings['maneuver_calculation']):
        print('Updating...')
        max_speed = settings['maneuver_calculation']['maximal_speed']
        min_speed = settings['maneuver_calculation']['minimal_speed']
        step = (max_speed - min_speed) / 4
        settings['maneuver_calculation']['forward_speed1'] = min_speed
        settings['maneuver_calculation']['forward_speed2'] = min_speed + step
        settings['maneuver_calculation']['forward_speed3'] = min_speed + step * 2
        settings['maneuver_calculation']['forward_speed4'] = min_speed + step * 3
        settings['maneuver_calculation']['forward_speed5'] = max_speed

        settings['maneuver_calculation']['reverse_speed1'] = max_speed * .5
        settings['maneuver_calculation']['reverse_speed2'] = max_speed

        settings['maneuver_calculation']['max_circulation_radius'] = settings['maneuver_calculation'][
            'circulation_radius']
        settings['maneuver_calculation']['min_circulation_radius'] = settings['maneuver_calculation'][
            'circulation_radius']

        del settings['maneuver_calculation']['circulation_radius']

        settings['maneuver_calculation']['breaking_distance'] = 0
        settings['maneuver_calculation']['run_out_distance'] = 0
        settings['maneuver_calculation']['forecast_time'] = 3600 * 2  # 2 hours
        with open(filename, 'w') as f:
            json.dump(settings, f,indent=2)
    else:
        print('Skip')


def run_case(datadir):
    working_dir = os.path.abspath(os.getcwd())
    os.chdir(datadir)
    print(datadir)
    # Get a list of old results
    file_list = glob.glob('maneuver*.json') + glob.glob('nav-report.json')
    for filePath in file_list:
        try:
            os.remove(filePath)
        except OSError:
            pass

    update_settings('settings.json')
    os.chdir(working_dir)


def run(data_directory):
    for root, dirs, files in os.walk(data_directory):
        if "nav-data.json" in files:
            run_case(os.path.join(data_directory, root))


if __name__ == "__main__":
    cur_dir = os.path.abspath(os.getcwd())
    run(cur_dir)
