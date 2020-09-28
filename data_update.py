import glob
import json
import os
import math


def process_json_file(filename, function, args=()):
    with open(filename) as f:
        json_data = json.load(f)

    json_data = function(json_data, *args)

    with open(filename, 'w') as f:
        json.dump(json_data, f, indent='\t')
        print('rewrite: {}'.format(filename))


def wrap_angle(angle):
    return math.fmod(angle + 360., 360.)


def find_cases(root_dir='.'):
    result = []
    for item in os.listdir(root_dir):
        if os.path.isdir(os.path.join(root_dir, item)):
            files = os.listdir(os.path.join(root_dir, item))
            if "nav-data.json" in files:
                result.append(os.path.join(root_dir if root_dir != '.' else '', item))
    return result


def prepare_table(root_dir='.'):
    cases = find_cases(root_dir)
    for case in cases:
        print(case)
        change_case(case)


def change_case(case_dir):
    # move_args = (lat1, lon1, lat_, lon_, dcog)
    def change_min_dist(json_data):
        json_data['maneuver_calculation']['min_diverg_dist'] = json_data['maneuver_calculation'][
                                                                   'safe_diverg_dist'] * .9
        return json_data

    def change_target(data):
        data['maneuver_calculation']['safe_diverg_dist'] = 2.4
        data['safety_control']['cpa'] = 2.4
        return data

    # process_json_file(os.path.join(case_dir, 'settings.json'), change_min_dist)
    # process_json_file(os.path.join(case_dir, 'target-settings.json'), change_target)
    # process_json_file(os.path.join(case_dir, 'real-target-maneuvers.json'), move_real_target_maneuvers_data, move_args)
    # process_json_file(os.path.join(case_dir, 'constraints.json'), move_constraints_data, move_args)


def prettify(root_dir):
    for directory, dirs, files in os.walk(root_dir):
        file_list = glob.glob(os.path.join(directory, '*.json'))

        for file_path in file_list:
            print('Prettify {}'.format(file_path))
            with open(file_path) as f:
                data = json.load(f)
            basename = os.path.basename(file_path)

            if basename == 'nav-data.json':
                data['COG'] = wrap_angle(data['COG'])
                data['heading'] = wrap_angle(data['heading'])

            if basename == 'route-data.json':
                for item in data['items']:
                    item['begin_angle'] = wrap_angle(item['begin_angle'])

            if basename == 'target-data.json':
                for target in data:
                    target['COG'] = wrap_angle(target['COG'])

            if basename == 'real-target-maneuvers.json':
                for path in data:
                    for item in path['items']:
                        item['begin_angle'] = wrap_angle(item['begin_angle'])

            with open(file_path, 'w') as f:
                json.dump(data, f, indent='\t')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Creates index file starting from working directory. If index already exists, tries to change "
                    "coordinates according to changes in index file.")
    parser.add_argument("--pretty", action="store_true", help="Pretty format all json files")
    arguments = parser.parse_args()

    cur_dir = os.path.abspath(os.getcwd())
    prepare_table()
    if arguments.pretty:
        prettify(cur_dir)
