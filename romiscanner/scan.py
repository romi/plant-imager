import importlib
import json
import os
import random

import luigi
from romidata import RomiTask, FilesetTarget, DatabaseConfig, io

from romidata.task import FilesetExists
from romiscanner.configs.lpy import VirtualPlantConfig
from romiscanner.configs.scan import ScanPath
from romiscanner.log import logger
from romiscanner.scanner import Scanner
from romiscanner.tasks.lpy import VirtualPlant
from romiscanner.vscan import VirtualScanner


class ObjFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "data"


class HdriFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "hdri"


class SceneFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "scenes"


class PaletteFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "palette"


class Scan(RomiTask):
    """ A task for running a scan, real or virtual.

    Module: romiscan.tasks.scan
    Default upstream tasks: None

    Parameters
    ----------
    metadata : DictParameter
        metadata for the scan
    scanner : DictParameter
        scanner hardware configuration (TODO: see hardware documentation)
    path : DictParameter
        scanner path configuration (TODO: see hardware documentation)

    """
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
        output_fileset.set_metadata("channels", scanner.channels())


class VirtualScan(Scan):
    load_scene = luigi.BoolParameter(default=False)
    scene_file_id = luigi.Parameter(default="")

    use_palette = luigi.BoolParameter(default=False)
    use_hdri = luigi.BoolParameter(default=False)

    obj_fileset = luigi.TaskParameter(default=VirtualPlant)
    hdri_fileset = luigi.TaskParameter(default=HdriFileset)
    scene_fileset = luigi.TaskParameter(default=SceneFileset)
    palette_fileset = luigi.TaskParameter(default=PaletteFileset)

    render_ground_truth = luigi.BoolParameter(default=False)

    def requires(self):
        requires = {
            "object": self.obj_fileset()
        }
        if self.use_hdri:
            requires["hdri"] = self.hdri_fileset()
        if self.use_palette:
            requires["palette"] = self.palette_fileset()
        if self.load_scene:
            requires["scene"] = self.scene_fileset()
        return requires

    def load_scanner(self):
        logger.info("Initializing VirtualScanner...")
        scanner_config = json.loads(
            luigi.DictParameter().serialize(self.scanner))

        obj_fileset = self.input()["object"].get()
        logger.info("Done loading 'obj' file!")

        if self.load_scene:
            scene_fileset = self.input()["scene"].get()
            for f in scene_fileset.get_files():
                logger.debug(f.id)
            self.tmpdir = io.tmpdir_from_fileset(scene_fileset)
            scanner_config["scene"] = os.path.join(self.tmpdir.name,
                                                   scene_fileset.get_file(
                                                       self.scene_file_id).filename)
            logger.info("Done loading 'scene'!")

        if self.render_ground_truth:
            scanner_config["classes"] = list(
                VirtualPlantConfig().classes.values())
            logger.info("Got a list of ground truth: {}".format(scanner_config["classes"]))

        vscan = VirtualScanner(**scanner_config)
        logger.info("Initialized a VirtualScanner instance!")

        while True:
            obj_file = random.choice(obj_fileset.get_files())
            if "obj" in obj_file.filename:
                break
        mtl_file = obj_fileset.get_file(obj_file.id + "_mtl")

        palette_file = None
        if self.use_palette:
            palette_file = random.choice(
                self.input()["palette"].get().get_files())
            logger.info("Done loading 'palette'!")
        vscan.load_object(obj_file, mtl=mtl_file, palette=palette_file)

        if self.use_hdri:
            hdri_fileset = self.input()["hdri"].get()
            hdri_file = random.choice(hdri_fileset.get_files())
            vscan.load_background(hdri_file)
            logger.info("Done loading 'hdri' background!")

        bb = vscan.get_bounding_box()
        self.output().get().set_metadata("bounding_box", bb)
        return vscan


class CalibrationScan(RomiTask):
    """ A task for running a scan, real or virtual, with a calibration path.

    Module: romiscan.tasks.scan
    Colmap poses for subsequent scans. (TODO: see calibration documentation)
    Default upstream tasks: None

    Parameters
    ----------
    metadata : DictParameter
        metadata for the scan
    scanner : DictParameter
        scanner hardware configuration (TODO: see hardware documentation)
    path : DictParameter
        scanner path configuration (TODO: see hardware documentation)
    n_line : int ?
        number of shots taken on the orthogonal calibration lines

    """
    n_points_line = luigi.IntParameter(default=5)

    def run(self):
        path = Scan().get_path()
        calibration_path = path(CalibrationScan, self.n_points_line)
        Scan().run(path=calibration_path)