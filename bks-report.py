#!/usr/bin/env python3
import base64
import ctypes
import io
import json
import os
import subprocess
import time
import traceback
from collections import Counter
from datetime import datetime, date
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
from geographiclib.geodesic import Geodesic
from matplotlib import pyplot as plt
from natsort import natsorted

from plot import plot_from_files, Case


def fix_returncode(code):
    return ctypes.c_int32(code).value


class ReportGenerator:
    def __init__(self, executable):
        self.exe = executable
        self.cases = []
        self.work_dir = os.path.abspath(os.getcwd())
        self.tmpdir = os.path.join(self.work_dir, ".bks_report\\")
        self.rvo = None
        self.nopic = None
        self.fast = False

    def generate(self, data_directory, glob='*', rvo=None, nopic=False):
        self.rvo = rvo
        self.nopic = nopic
        directories_list = []
        try:
            df = pd.read_csv(data_directory + '/metainfo.csv', index_col=False)
            directories_list = df['datadirs'].values
        except FileNotFoundError:
            if not self.fast:
                for path in Path(data_directory).glob(glob):
                    for root, dirs, files in os.walk(path):
                        if "nav-data.json" in files or 'navigation.json' in files:
                            directories_list.append(os.path.join(data_directory, root))
                directories_list = natsorted(directories_list)
                df = pd.DataFrame()
                df['datadirs'] = directories_list
                df.to_csv(data_directory + '/metainfo.csv')
            else:
                dirs = os.listdir(data_directory)
                directories_list = [os.path.abspath(p) for p in dirs]

        with Pool() as p:
            cases = p.map(self.run_case, directories_list)

        return Report(cases, self.exe, self.work_dir, self.rvo)

    def generate_for_list(self, list, nopic=False):
        self.nopic = nopic
        with Pool() as p:
            cases = p.map(self.run_case, list)
        return Report(cases, self.exe, self.work_dir, self.rvo)

    def run_case(self, datadir):
        working_dir = os.path.abspath(os.getcwd())
        os.chdir(datadir)

        if os.path.exists('nav-data.json'):
            case_filenames = Case.CASE_FILENAMES_VSE
        elif os.path.exists(Case.CASE_FILENAMES['nav_data']):
            case_filenames = Case.CASE_FILENAMES
        else:
            case_filenames = Case.CASE_FILENAMES_KT
        # Get a list of old results
        cur_path = Path('.')
        file_list = list(cur_path.glob(case_filenames['maneuvers'])) + \
                    list(cur_path.glob(case_filenames['analyse']))

        for filePath in file_list:
            try:
                os.remove(filePath)
            except OSError:
                pass

        # Print the exit code.
        exec_time = time.time()
        command = [self.exe, "--target-settings", case_filenames['target_settings'],
                   "--targets", case_filenames['targets_data'],
                   "--settings", case_filenames['settings'],
                   "--nav-data", case_filenames['nav_data'],
                   "--hydrometeo", case_filenames['hydrometeo'],
                   "--constraints", case_filenames['constraints'],
                   "--route", case_filenames['route'],
                   "--maneuver", case_filenames['maneuvers'],
                   "--analyse", case_filenames['analyse'],
                   "--predict", case_filenames['targets_maneuvers'],
                   ("--rvo-enable" if self.rvo is True else "")]

        # Added to prevent freezing
        try:
            completedProc = subprocess.run(command,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           stdin=subprocess.PIPE, timeout=6)
            exec_time = time.time() - exec_time
            print("{} .Return code: {}. Exec time: {} sec"
                  .format(datadir, fix_returncode(completedProc.returncode), exec_time))
            image_data = ""
            nav_report = ""
            target_data = None
            if not self.nopic:
                try:
                    fig = plot_from_files(os.path.join(datadir, case_filenames['nav_data']))

                    f = io.BytesIO()
                    fig.savefig(f, format="png", dpi=300)
                    image_data = '<img width="100%" src="data:image/png;base64,{}">'.format(
                        base64.b64encode(f.getvalue()).decode())
                    plt.close(fig)
                except Exception as ex:
                    template = "<pre>Plot failed: An exception of type {} occurred.\n{}</pre>"
                    message = template.format(type(ex).__name__, traceback.format_exc())
                    image_data = message
            try:
                with open(case_filenames['analyse'], "r") as f:
                    nav_report = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
            except FileNotFoundError:
                pass
            try:
                with open(case_filenames['targets_data'], "r") as f:
                    target_data = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
            except FileNotFoundError:
                pass
            os.chdir(working_dir)

            try:
                target_data = json.loads(target_data)
            except:
                return
            datadir_i = os.path.split(datadir)[1]
            dist1, dist2 = 0, 0
            course1, course2 = 0, 0
            peleng1, peleng2 = 0, 0
            lat, lon = 0, 0
            try:
                with open(datadir + "/" + case_filenames['nav_data'], "r") as f:
                    nav_d = json.loads(f.read())
                    lat, lon = nav_d['lat'], nav_d['lon']
            except FileNotFoundError:
                pass
            try:
                dist1, course1, peleng1 = self.get_target_params(lat, lon, target_data[0])
            except IndexError or TypeError:
                dist1, course1, peleng1 = 0, 0, 0
            try:
                dist2, course2, peleng2 = self.get_target_params(lat, lon, target_data[1])
            except IndexError or TypeError:
                dist2, course2, peleng2 = 0, 0, 0

            types, right = self.load_maneuver(datadir, case_filenames)
            if len(types) == 1:
                types.append(None)

            return {"datadir": datadir_i,
                    "proc": completedProc,
                    "image_data": image_data,
                    "exec_time": exec_time,
                    "nav_report": nav_report,
                    "command": command,
                    "code": fix_returncode(completedProc.returncode),
                    "dist1": dist1,
                    "dist2": dist2,
                    "course1": course1,
                    "course2": course2,
                    "peleng1": peleng1,
                    "peleng2": peleng2,
                    "right": right,
                    "type1": types[0],
                    "type2": types[1]
                    }

        except subprocess.TimeoutExpired:
            print("TEST TIMEOUT ERR")
            exec_time = time.time() - exec_time
            os.chdir(working_dir)
            target_data = None
            try:
                with open(case_filenames['targets_data'], "r") as f:
                    target_data = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
            except FileNotFoundError:
                pass

            datadir_i = os.path.split(datadir)[1]
            dist1, dist2 = 0, 0
            course1, course2 = 0, 0
            peleng1, peleng2 = 0, 0
            lat, lon = 0, 0
            try:
                with open(datadir + "/" + case_filenames['nav_data'], "r") as f:
                    nav_d = json.loads(f.read())
                    lat, lon = nav_d['lat'], nav_d['lon']
            except FileNotFoundError:
                pass
            try:
                dist1, course1, peleng1 = self.get_target_params(lat, lon, target_data[0])
            except:
                dist1, course1, peleng1 = 0, 0, 0
            try:
                dist2, course2, peleng2 = self.get_target_params(lat, lon, target_data[1])
            except:
                dist2, course2, peleng2 = 0, 0, 0

            # TODO: Rewrite pelengs and dists to arrays

            return {"datadir": datadir_i,
                    "proc": None,
                    "image_data": "",
                    "exec_time": exec_time,
                    "nav_report": None,
                    "command": command,
                    "code": 6,
                    "dist1": dist1,
                    "dist2": dist2,
                    "course1": course1,
                    "course2": course2,
                    "peleng1": peleng1,
                    "peleng2": peleng2,
                    "right": None,
                    "type1": None,
                    "type2": None
                    }

    def load_maneuver(self, datadir, case_filenames):
        """
        Returns turn direction and scenarios types.
        @param datadir: data directory.
        @param case_filenames: dict with filenames
        @return: array with target types and turn direction.
        """
        c_dif = None
        try:
            with open(datadir + "/" + case_filenames['maneuvers'], "r") as f:
                maneuver = json.loads(f.read())
                parts = maneuver[0]['path']['items']
                start_angle = parts[0]['begin_angle']
                for part in parts:
                    if part['begin_angle'] != start_angle:
                        c_dif = part['begin_angle'] - start_angle
                        break
            #         if c_dif < 0 -> left, else right
            #         right = True
        except FileNotFoundError:
            pass
        types = []
        with open(datadir + "/" + case_filenames['analyse'], "r") as f:
            report = json.loads(f.read())
            targets = report['target_statuses']
            for target in targets:
                types.append(target['scenario_type'])
        try:
            return types, c_dif > 0
        except TypeError:
            return types, None

    def get_target_params(self, lat, lon, target_data):
        lat_t, lon_t = target_data["lat"], target_data["lon"]
        path = Geodesic.WGS84.Inverse(lat, lon, lat_t, lon_t)
        dist = path['s12'] / 1852
        course = target_data["COG"]
        peleng = path['azi1']
        return dist, course, peleng


class Report:

    def __init__(self, cases, executable, work_dir, rvo):
        self.cases = cases
        self.exe = executable
        self.work_dir = work_dir
        self.rvo = rvo

    def save_html(self, filename):
        css = """
        *{font-family: sans-serif;}
        h2 {margin-top: 2em;}
        .case {
            display: flex;
            max-height: 540pt;
            font-family: sans-serif;
        }
        .case .pic {
            flex: 1;
        }
        .case .stdout {
            flex: 1;
            border: 1px black solid;
            padding: 0;
            display: flex;
            flex-direction: column;
            background: #555;
            overflow-y: auto;
        }
        .stdout pre {
            max-height: 100%;
            overflow-y: auto;
            color: #fff;
            margin: 0;
            padding: 1em;
            white-space: pre-line;
            font-family: monospace;
        }
        .stdout pre.cmd::before {
            content: '$ ';
            font-weight: bold;
        }
        .stdout pre.cmd {background: #222;}
        .stdout p{
            border-bottom: 1px black solid;
            padding: 0.5em;
            margin: 0;
            font: 400 13.3333px sans-serif;
        }
        .stdout input[type=checkbox] {
            visibility: visible;
            height: 2em;
            width: 100%;
            margin: 0;
        }
        .stdout input[type=checkbox]:after, .stdout p{
            visibility: visible;
            display: block;
            padding: 0.5em;
            background: #fff;
        }

        .stdout input[type=checkbox] + div {
            display: none;
        }
        .stdout input[type=checkbox]:checked + div {
            display: block;
        }
        .stdout input[type=checkbox]::after{content: '▸ ' attr(text);}
        .stdout input[type=checkbox]:checked::after{content: '▾ ' attr(text);}
        img{
            image-rendering: -moz-crisp-edges;         /* Firefox */
            image-rendering:   -o-crisp-edges;         /* Opera */
            image-rendering: -webkit-optimize-contrast;/* Webkit (non-standard naming) */
            image-rendering: crisp-edges;
            -ms-interpolation-mode: nearest-neighbor;
        }
        table.summary {
            border-collapse: collapse;
        }
        
        table.summary td[code="0"]{
            background-color: green;
            color: white;
        }
        table.summary td[code="1"]{
            background-color: darkorange;
            color: white;
        }
        table.summary td[code="2"]{
            background-color: red;
            color: white;
        }
        """
        print("Creating report file in HTML format")
        tbody = ''.join([
            f'<tr><td><a href="#case_{i}">{os.path.relpath(case["datadir"], self.work_dir)}</a></td><td code="{case["code"]}">{case["code"]}</td></tr>'
            for i, case in
            enumerate(self.cases)])
        codes = dict(Counter([case["code"] for case in self.cases]))
        table = """
        <table class="summary" border="1">
        <thead><tr><td></td><td>{code_summary}</td></tr><br>
        <tr><td>Case</td><td>Code</td></tr></thead>
        <tbody>{tbody}</tbody>
        </table>
        """.format(tbody=tbody, code_summary='<br>'.join(['{}: {}'.format(k, codes[k]) for k in sorted(codes)]))

        html = """<!DOCTYPE HTML>
<html>
<head>
<meta charset="utf-8">
<title>Results from {datetime}</title>
<style>{styles}</style>
</head>
<body>
<h1>Report from {datetime} {rvo}</h1>""".format(datetime=datetime.now(), styles=css,
                                                rvo='<b>rvo enabled</b>' if self.rvo else '')
        html += table

        for i, case in enumerate(self.cases):
            img_tag = case["image_data"]
            try:
                html += """<div>
    <h2 id="case_{case_i}">{casename}</h2>
    <div class="case">
    <div class="pic">
    <picture>{image}</picture>
    </div>
    <div class="stdout">
    <p>Return code: {return_code}</p>
    <p>Execution time: {exec_time} seconds</p>
    <input type="checkbox" text="Situation report">
    <div><pre>{nav_report}</pre></div>
    <input type="checkbox" text="STDOUT"{checked}><div>
    <pre class="cmd">{command}</pre>
    <pre>{stdout}</pre></div>
    </div></div></div>""".format(casename=case["datadir"],
                                 return_code=fix_returncode(case["proc"].returncode),
                                 exec_time=case["exec_time"],
                                 command=str(' '.join(case["command"])),
                                 stdout=str(case["proc"].stdout.decode("utf-8")),
                                 nav_report=case["nav_report"],
                                 image=img_tag,
                                 checked=" checked",
                                 case_i=i)
            except AttributeError:
                html += """<div>
                    <h2 id="case_{case_i}">{casename}</h2>
                    <div class="case">
                    <div class="pic">
                    <picture>{image}</picture>
                    </div>
                    <div class="stdout">
                    <p>Return code: {return_code}</p>
                    <p>Execution time: {exec_time} seconds</p>
                    <input type="checkbox" text="Situation report">
                    <div><pre>{nav_report}</pre></div>
                    <input type="checkbox" text="STDOUT"{checked}><div>
                    <pre class="cmd">{command}</pre>
                    <pre>{stdout}</pre></div>
                    </div></div></div>""".format(casename=case["datadir"],
                                                 return_code=10,
                                                 exec_time=case["exec_time"],
                                                 command=str(' '.join(case["command"])),
                                                 stdout="TIME_ERR",
                                                 nav_report=case["nav_report"],
                                                 image="",
                                                 checked=" checked",
                                                 case_i=i)

        html += "</body></html>"
        with io.open(filename, "w", encoding="utf-8") as f:
            f.write(html)

    def save_excel(self, filename='report.xlsx'):
        df = pd.json_normalize(self.cases)
        try:
            df.to_excel(filename)
        except ValueError:
            df.to_csv(filename)
        return df

    def get_danger_params(self, statuses):
        return [rec['datadir'] for rec in self.cases if rec['code'] in statuses]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BKS report generator")
    parser.add_argument("executable", type=str, help="Path to USV executable")
    parser.add_argument("--glob", type=str, default='*', help="Pattern for scanned directories")

    parser.add_argument("--rvo", action="store_true", help="Run USV with --rvo")
    parser.add_argument("--nopic", action="store_true", help="")
    parser.add_argument("--working_dir", type=str, help="Path to USV executable")
    parser.add_argument("--report_file", type=str, help="Report file")
    args = parser.parse_args()

    use_rvo = None
    if args.rvo:
        use_rvo = True

    if args.working_dir is not None:
        cur_dir = os.path.abspath(args.working_dir)
    else:
        cur_dir = os.path.abspath(os.getcwd())
    t0 = time.time()
    usv_executable = os.path.join(cur_dir, args.executable)
    report = ReportGenerator(usv_executable)
    print("Starting converstion...")
    report_out = report.generate(cur_dir, glob=args.glob, rvo=use_rvo, nopic=args.nopic)
    print(f'Finished in {time.time() - t0} sec')
    # print("Starting saving to HTML")
    # report_out.save_html("report.html")

    t_save = time.time()
    if args.report_file:
        name = args.report_file
    else:
        name = "./reports/report1_" + str(date.today()) + ".xlsx"

    print(f"Starting saving report to '{name}'")
    meta_ = report_out.save_excel(name)
    meta = meta_[['code', 'type1']]
    meta['datadirs'] = meta_['datadir']
    meta.to_csv(cur_dir + '/metainfo.csv')
    # build_percent_diag(name, 12, 4, 0.5)
    # print("Creating report for danger scenarios")
    # report_d_out = report.generate_for_list(report_out00.get_danger_params([2, 4]))
    # report_d_out.save_html("report_status_2_4_" + str(date.today()) + ".html")
    # report_d_out.save_excel("report_2_4_" + str(date.today()) + ".xlsx")
    print(f'Save time: {time.time() - t_save}')
    print(f'Total time: {time.time() - t0}')
