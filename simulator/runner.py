import subprocess
import tempfile
import time
from .data import ScenarioData


class RunResult:
    def __init__(self, data, stdout, return_code, time):
        self.data = data
        self.stdout = stdout
        self.return_code = return_code
        self.time = time


class Runner:
    def __init__(self, executable):
        self.executable = executable

    def run(self, data):
        tmpdir = tempfile.TemporaryDirectory()
        data.dump_directory(tmpdir.name)
        result = self.run_directory(tmpdir.name)
        tmpdir.cleanup()
        return result

    def run_directory(self, directory, targets="target-data.json",
                      settings="settings.json",
                      nav_data="nav-data.json",
                      hydrometeo="hmi-data.json",
                      constraints="constraints.json",
                      route="route-data.json",
                      maneuver="maneuver.json",
                      analyse="nav-report.json",
                      predict="target-maneuvers.json",
                      rvo=False,
                      no_rvo=False,
                      simple_prediction=False):
        args = [self.executable, "--targets", targets,
                "--settings", settings,
                "--nav-data", nav_data,
                "--hydrometeo", hydrometeo,
                "--constraints", constraints,
                "--route", route,
                "--maneuver", maneuver,
                "--analyse", analyse,
                "--predict", predict]
        if rvo:
            args.append('--rvo')
        if no_rvo:
            args.append('--no-rvo')
        if simple_prediction:
            args.append('--simple-prediction')

        exec_time = time.time()
        completedProc = subprocess.run(args, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        exec_time = time.time() - exec_time

        return RunResult(ScenarioData.load_directory(directory), completedProc.stdout, completedProc.returncode, time)
