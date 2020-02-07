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

    def run(self, path=None):
        if path is None:
            path = self.get_path()
        scanner = ScannerFactory.parse_config(self.scanner_config)
        metadata = json.loads(luigi.DictParameter().serialize(self.metadata))

        output_fileset = self.output().get()
        scanner.scan(path, output_fileset)
        output_fileset.set_metdata(metadata)

class CalibrationScan(RomiTask):
    n_points_line = luigi.IntParameter(default=5)
    def run(self):
        path = Scan().get_path()
        calibration_path = path(CalibrationScan, self.n_points_line)
        Scan().run(path=calibration_path)

class Clean(RomiTask):
    no_confirm = luigi.BoolParameter(default=False)
    upstream_task = None

    def requires(self):
        return []

    def complete(self):
        return False

    def confirm(self, c, default='n'):
        valid = {"yes": True, "y": True, "ye": True,
        "no": False, "n": False}
        if c == '':
            return valid[default]
        else:
            return valid[c]

    def run(self):
        logger.critical("This is going to delete all filesets except the scan fileset (images). Confirm? [y/N]")
        choice = self.confirm(input().lower())
        if not choice:
            raise IOError("Did not validate deletion.")

        scan = DatabaseConfig().scan
        fs_ids = [fs.id for fs in scan.get_filesets()]
        for fs in fs_ids:
            if fs != "images":
                scan.delete_fileset(fs)
