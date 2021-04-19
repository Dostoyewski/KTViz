#!/usr/bin/env python3
import base64
import ctypes
import io
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from multiprocessing import Pool
from matplotlib import pyplot as plt
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

    def generate(self, data_directory, glob='*', rvo=None, nopic=False):
        self.rvo = rvo
        self.nopic = nopic
        directories_list = []
        for path in Path(data_directory).glob(glob):
            for root, dirs, files in os.walk(path):
                if "nav-data.json" in files or 'navigation.json' in files:
                    directories_list.append(os.path.join(data_directory, root))
        directories_list.sort()

        with Pool() as p:
            cases = p.map(self.run_case, directories_list)

        return Report(cases, self.exe, self.work_dir)

    def run_case(self, datadir):
        working_dir = os.path.abspath(os.getcwd())
        os.chdir(datadir)

        if os.path.exists(Case.CASE_FILENAMES['nav_data']):
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
                                        ("--rvo" if self.rvo is True else "--no-rvo" if self.rvo is False else "")]

        completedProc = subprocess.run(command,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        exec_time = time.time() - exec_time

        print("{} .Return code: {}. Exec time: {} sec"
              .format(datadir, fix_returncode(completedProc.returncode), exec_time))
        image_data = ""
        nav_report = ""
        if not self.nopic:
            fig = plot_from_files(case_filenames['nav_data'])

            f = io.BytesIO()
            fig.savefig(f, format="png", dpi=300)
            image_data = '<img width="100%" src="data:image/png;base64,{}">'.format(
                base64.b64encode(f.getvalue()).decode())
            plt.close(fig)
        try:
            with open("nav-report.json", "r") as f:
                nav_report = json.dumps(json.loads(f.read()), indent=4, sort_keys=True)
        except FileNotFoundError:
            pass

        os.chdir(working_dir)
        return {"datadir": datadir,
                "proc": completedProc,
                "image_data": image_data,
                "exec_time": exec_time,
                "nav_report": nav_report,
                "command": command}


class Report:

    def __init__(self, cases, executable, work_dir):
        self.cases = cases
        self.exe = executable
        self.work_dir = work_dir

    def save_html(self, filename):
        css = """
        h2 {{margin-top: 2em;}}
        .case {
            display: flex;
            max-height: 540pt;
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
        }
        .stdout pre {
            max-height: 100%;
            overflow-y: auto;
            background: #555;
            color: #fff;
            margin: 0;
            padding: 1em;
        }
        .stdout p{
            border-bottom: 1px black solid;
            padding: 0.5em;
            margin: 0;
        }
        .stdout input[type=checkbox] {
            visibility: visible;
            height: 2em;
            width: 100%;
        }

        .stdout input[type=checkbox]:after {
            content: attr(text);
            visibility: visible;
            display: block;
            padding: 0.5em;
        }

        .stdout input[type=checkbox] + pre {
            display: none;
        }
        .stdout input[type=checkbox]:checked + pre {
            display: block;
        }
        img{
            image-rendering: -moz-crisp-edges;         /* Firefox */
            image-rendering:   -o-crisp-edges;         /* Opera */
            image-rendering: -webkit-optimize-contrast;/* Webkit (non-standard naming) */
            image-rendering: crisp-edges;
            -ms-interpolation-mode: nearest-neighbor;
        }
        """

        html = """<!DOCTYPE HTML>
<html>
<head>
<meta charset="utf-8">
<title>Results from {datetime}</title>
<style>{styles}</style>
</head>
<body>
<h1>Report from {datetime}</h1>""".format(datetime=datetime.now(), styles=css)

        for case in self.cases:
            img_tag = case["image_data"]
            html += """<div>
<h2>{casename}</h2>
<div class="case">
<div class="pic">
<picture>{image}</picture>
</div>
<div class="stdout">
<p>Return code: {return_code}</p>
<p>Execution time: {exec_time} seconds</p>
<input type="checkbox" text="Situation report">
<pre>{nav_report}</pre>
<input type="checkbox" text="STDOUT"{checked}>
<pre>{stdout}</pre>
</div></div></div>""".format(casename=case["datadir"],
                             return_code=fix_returncode(case["proc"].returncode),
                             exec_time=case["exec_time"],
                             stdout=str(case["proc"].stdout.decode("utf-8")),
                             nav_report=case["nav_report"],
                             image=img_tag,
                             checked=" checked" if case["proc"].returncode in (0, 1) else "")

        html += "</body></html>"
        with io.open(filename, "w", encoding="utf-8") as f:
            f.write(html)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BKS report generator")
    parser.add_argument("executable", type=str, help="Path to USV executable")
    parser.add_argument("--glob", type=str, default='*', help="Pattern for scanned directories")

    parser.add_argument("--rvo", action="store_true", help="Run USV with --rvo")
    parser.add_argument("--no-rvo", action="store_true", help="Run USV with --no-rvo")
    parser.add_argument("--nopic", action="store_true", help="")
    parser.add_argument("--working_dir", type=str, help="Path to USV executable")
    args = parser.parse_args()

    use_rvo = None
    if args.rvo:
        use_rvo = True
    if args.no_rvo:
        use_rvo = False

    if args.working_dir is not None:
        cur_dir = os.path.abspath(args.working_dir)
    else:
        cur_dir = os.path.abspath(os.getcwd())
    t0 = time.time()
    usv_executable = os.path.join(cur_dir, args.executable)
    report = ReportGenerator(usv_executable)
    report.generate(cur_dir, glob=args.glob, rvo=use_rvo, nopic=args.nopic).save_html("report.html")
    print(f'Total time: {time.time() - t0}')
