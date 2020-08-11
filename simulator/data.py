import json
import os

from simulator.path import Path


class Solution:
    def __init__(self, solution_type, message, solver_name, path):
        self.solution_type = solution_type
        self.message = message
        self.path = path
        self.solver_name = solver_name


class ScenarioData:
    def __init__(self, navigational, settings, hydrometeo, route, targets=None, constraints=None, maneuver=None,
                 analyse=None, predict=None):
        if targets is None:
            targets = []
        self.navigational = navigational
        self.settings = settings
        self.hydrometeo = hydrometeo
        self.route = route
        self.targets = targets
        self.constraints = constraints
        self.analyse = analyse
        self.predict = predict
        self.maneuver = maneuver

    @staticmethod
    def load_directory(directory, targets="target-data.json",
                       settings="settings.json",
                       nav_data="nav-data.json",
                       hydrometeo="hmi-data.json",
                       constraints="constraints.json",
                       route="route-data.json",
                       maneuver="maneuver.json",
                       analyse="nav-report.json",
                       predict="target-maneuvers.json"):
        def load_json(filename):
            if filename is not None and os.path.isfile(os.path.join(directory, filename)):
                with open(os.path.join(directory, filename)) as f:
                    return json.loads(f.read())
            return None

        predict_data = load_json(predict)
        if predict_data is not None:
            predict_data = [Path.load_from_array(path) for path in predict_data]

        maneuver_data = load_json(maneuver)
        if maneuver_data is not None:
            maneuver_data = [Solution(solution['solution_type'], solution['msg'], solution['solver_name'],
                                      Path.load_from_array(solution['path'])) for solution in maneuver_data]

        return ScenarioData(navigational=load_json(nav_data), settings=load_json(settings),
                            hydrometeo=load_json(hydrometeo), route=Path.load_from_array(load_json(route)),
                            targets=load_json(targets), constraints=load_json(constraints),
                            maneuver=maneuver_data, analyse=load_json(analyse), predict=predict_data)
