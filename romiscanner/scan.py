import luigi
import importlib

import numpy as np

from romidata.task import  RomiTask, FileByFileTask, FilesetTarget, DatabaseConfig
from romidata import io
from .log import logger
from .scanner import ScannerFactory

class Scan(RomiTask):
    upstream_task = None

    metadata = luigi.DictParameter(default={})
    scanner = luigi.DictParameter(default={})
    path = luigi.DictParameter(default={})

    def requires(self):
        return []

    def output(self):
        """Output for a RomiTask is a FileSetTarget, the fileset ID being
        the task ID.
        """
        return FilesetTarget(DatabaseConfig().scan, "images")

    def get_path(self):
        path_module = (path if not "path_module" in self.path_config
            else importlib.import_module(self.path_config["module"]))
        path = getattr(path_module, self.path_config["class"])(**self.path_config["kwargs"])
        return path

    def load_scanner(self):
        scanner_config = self.scanner_config

        cnc_module = scanner_config["cnc"]["module"]
        cnc_kwargs = scanner_config["cnc"]["kwargs"]
        cnc_module = importlib.import_module(cnc_module)
        cnc = getattr(cnc_module, "CNC")(**cnc_kwargs)

        gimbal_module = scanner_config["gimbal"]["module"]
        gimbal_kwargs = scanner_config["gimbal"]["kwargs"]
        gimbal_module = importlib.import_module(gimbal_module)
        gimbal = getattr(gimbal_module, "Gimbal")(**gimbal_kwargs)

        camera_module = scanner_config["camera"]["module"]
        camera_kwargs = scanner_config["camera"]["kwargs"]
        camera_module = importlib.import_module(camera_module)
        camera = getattr(camera_module, "Camera")(**camera_kwargs)

        return Scanner(cnc, gimbal, camera)

    def run(self, path=None):
        if path is None:
            path = self.get_path()

        scanner = self.load_scanner()
        metadata = json.loads(luigi.DictParameter().serialize(self.metadata))

        output_fileset = self.output().get()
        scanner.scan(path, output_fileset)
        output_fileset.set_metdata(metadata)

class VirtualScan(Scan):
    upstream_task = VirtualPlant()

class CalibrationScan(RomiTask):
    n_points_line = luigi.IntParameter(default=5)
    def run(self):
        path = Scan().get_path()
        calibration_path = path(CalibrationScan, self.n_points_line)
        Scan().run(path=calibration_path)
