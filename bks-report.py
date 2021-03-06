#!/usr/bin/env python3
import base64
import ctypes
import glob
import io
import json
import os
import subprocess
import time
from datetime import datetime

from matplotlib import pyplot as plt

from plot import plot_from_files, Case


def fix_returncode(code):
    return ctypes.c_int32(code).value


class Report:

    def __init__(self, executable):
        self.exe = executable
        self.cases = []
        self.work_dir = os.path.abspath(os.getcwd())
        self.tmpdir = os.path.join(self.work_dir, ".bks_report\\")

    def generate(self, data_directory, rvo=None, nopic=False):
        for root, dirs, files in os.walk(data_directory):
            if "nav-data.json" in files or 'navigation.json' in files:
                self.run_case(os.path.join(data_directory, root), self.exe, rvo, nopic)

    def run_case(self, datadir, usv, rvo=None, nopic=False):
        working_dir = os.path.abspath(os.getcwd())
        os.chdir(datadir)

        # Get a list of old results
        file_list = glob.glob(Case.CASE_FILENAMES['maneuvers']) + glob.glob(Case.CASE_FILENAMES['analyse'])
        for filePath in file_list:
            try:
                os.remove(filePath)
            except OSError:
                pass

        # Print the exit code.
        exec_time = time.time()
        completedProc = subprocess.run([usv, "--target-settings", Case.CASE_FILENAMES['target_settings'],
                                        "--targets", Case.CASE_FILENAMES['targets_data'],
                                        "--settings", Case.CASE_FILENAMES['settings'],
                                        "--nav-data", Case.CASE_FILENAMES['nav_data'],
                                        "--hydrometeo", Case.CASE_FILENAMES['hydrometeo'],
                                        "--constraints", Case.CASE_FILENAMES['constraints'],
                                        "--route", Case.CASE_FILENAMES['route'],
                                        "--maneuver", Case.CASE_FILENAMES['maneuvers'],
                                        "--analyse", Case.CASE_FILENAMES['analyse'],
                                        "--predict", Case.CASE_FILENAMES['targets_maneuvers'],
                                        ("--rvo" if rvo is True else "--no-rvo" if rvo is False else "")],
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        exec_time = time.time() - exec_time

        print("{} .Return code: {}. Exec time: {} sec"
              .format(datadir, fix_returncode(completedProc.returncode), exec_time))
        image_data = ""
        nav_report = ""
        if fix_returncode(completedProc.returncode) in (0, 1) and not nopic:
            if os.path.isfile("maneuver.json"):
                fig = plot_from_files("maneuver.json")

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
        self.cases.append({"datadir": datadir,
                           "proc": completedProc,
                           "image_data": image_data,
                           "exec_time": exec_time,
                           "nav_report": nav_report})

    def saveHTML(self, filename):
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
<script type="text/javascript" src="http://d3js.org/d3.v3.min.js"></script>
<script type="text/javascript" src="http://mpld3.github.io/js/mpld3.v0.3.js"></script>
</head>
<body>
<h1>Report from {datetime}</h1>""".format(datetime=datetime.now(), styles=css)

        for case in self.cases:
            if case["proc"].returncode in (0, 1):
                img_tag = case["image_data"]
            else:
                img_tag = ""

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
    parser.add_argument("--rvo", action="store_true", help="Run USV with --rvo")
    parser.add_argument("--no-rvo", action="store_true", help="Run USV with --no-rvo")
    parser.add_argument("--nopic", action="store_true", help="")
    args = parser.parse_args()

    use_rvo = None
    if args.rvo:
        use_rvo = True
    if args.no_rvo:
        use_rvo = False

    cur_dir = os.path.abspath(os.getcwd())
    usv_executable = os.path.join(cur_dir, args.executable)
    report = Report(usv_executable)
    report.generate(cur_dir, rvo=use_rvo, nopic=args.nopic)
    report.saveHTML("report.html")
