import luigi
import importlib
import random
import numpy as np
import json

from romidata.task import  RomiTask, FileByFileTask, FilesetTarget, DatabaseConfig, ScanParameter, FilesetExists
from romidata import io
from .log import logger
from .lpy import VirtualPlant
from .vscan import VirtualScanner

class ScanPath(luigi.Config):
    module = luigi.Parameter(default = "romiscanner.path")
    class_name = luigi.Parameter()
    kwargs = luigi.DictParameter()

class Scan(RomiTask):
    upstream_task = None

    metadata = luigi.DictParameter(default={})
    scanner = luigi.DictParameter(default={})

    def requires(self):
        return []

    def output(self):
        """Output for a RomiTask is a FileSetTarget, the fileset ID being
        the task ID.
        """
        return FilesetTarget(DatabaseConfig().scan, "images")

    def get_path(self):
        path_module = importlib.import_module(ScanPath().module)
        path = getattr(path_module, ScanPath().class_name)(**ScanPath().kwargs)
        return path

    def load_scanner(self):
        scanner_config = self.scanner

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
        output_fileset.set_metadata(metadata)

class ObjFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "data"

class HdriFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "hdri"

class SceneFileset(FilesetExists):
    scan_id = ScanParameter()
    fileset_id = "scene"


class VirtualScan(Scan):
    obj_fileset = luigi.TaskParameter(default=VirtualPlant)
    hdri_fileset = luigi.TaskParameter(default=HdriFileset)
    scene_fileset = luigi.TaskParameter(default=SceneFileset)

    def requires(self):
        return {
                    "object" : self.obj_fileset(),
                    "hdri" : self.hdri_fileset()
                }

    def load_scanner(self):
        scanner_config = self.scanner
        vscan = VirtualScanner(**scanner_config)

        obj_fileset = self.input()["object"].get()
        while True:
            obj_file = random.choice(obj_fileset.get_files())
            if "obj" in obj_file.filename:
                vscan.load_object(obj_file)
                break

        hdri_fileset = self.input()["hdri"].get()
        hdri_file = random.choice(hdri_fileset.get_files())
        vscan.load_background(hdri_file)
        return vscan


class CalibrationScan(RomiTask):
    n_points_line = luigi.IntParameter(default=5)
    def run(self):
        path = Scan().get_path()
        calibration_path = path(CalibrationScan, self.n_points_line)
        Scan().run(path=calibration_path)
