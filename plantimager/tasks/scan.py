#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# plantimager - Python tools for the ROMI 3D Plant Imager
#
# Copyright (C) 2018 Sony Computer Science Laboratories
# Authors: D. Colliaux, T. Wintz, P. Hanappe
#
# This file is part of plantimager.
#
# plantimager is free software: you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# plantimager is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with plantimager.  If not, see
# <https://www.gnu.org/licenses/>.

import importlib
import json
import os
import random

import luigi
from plantimager import path
from plantimager.configs.lpy import VirtualPlantConfig
from plantimager.configs.scan import ScanPath
from plantimager.log import logger
from plantimager.scanner import Scanner
from plantimager.tasks.lpy import VirtualPlant
from plantimager.vscan import VirtualScanner

from plantdb import io
from romitask import DatabaseConfig
from romitask import FilesetTarget
from romitask import RomiTask
from romitask.task import FilesetExists


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


class ScannerToCenter(RomiTask):
    """A task to move the camera at the center of the path."""
    upstream_task = None

    def requires(self):
        return []

    def output(self):
        return []

    def run(self):
        hw_scanner = Scan().load_scanner()
        cx = ScanPath().kwargs["center_x"]
        cy = ScanPath().kwargs["center_y"]
        hw_scanner.cnc.moveto(cx, cy, 0.)
        logger.info(f"Moved to X:{cx}mm, Y:{cy}mm!")
        return


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
        """The output fileset associated to a ``Scan`` is an 'images' dataset."""
        return FilesetTarget(DatabaseConfig().scan, "images")

    def get_path(self) -> path.Path:
        """Load the ``ScanPath`` module & get the configuration from the TOML config file."""
        path_module = importlib.import_module(ScanPath().module)
        path = getattr(path_module, ScanPath().class_name)(**ScanPath().kwargs)
        return path

    def load_scanner(self) -> Scanner:
        """Load the ``CNC``, ``Gimbal`` & ``Camera`` modules and create a ``Scanner`` configuration."""
        scanner_config = self.scanner

        # - Load the CNC configuration from TOML:
        cnc_module = scanner_config["cnc"]["module"]
        logger.debug(f"CNC module: {cnc_module}")
        cnc_kwargs = scanner_config["cnc"]["kwargs"]
        param_str = [f"\n  - {k}={v}" for k, v in cnc_kwargs.items()]
        logger.debug(f"CNC parameters: {''.join(param_str)}")
        # - Import corresponding module to python:
        cnc_module = importlib.import_module(cnc_module)
        cnc = getattr(cnc_module, "CNC")(**cnc_kwargs)

        # - Load the Gimbal configuration from TOML:
        gimbal_module = scanner_config["gimbal"]["module"]
        gimbal_kwargs = scanner_config["gimbal"]["kwargs"]
        logger.debug(f"Gimbal module: {gimbal_module}")
        param_str = [f"\n  - {k}={v}" for k, v in gimbal_kwargs.items()]
        logger.debug(f"Gimbal parameters: {''.join(param_str)}")
        # - Import corresponding module to python:
        gimbal_module = importlib.import_module(gimbal_module)
        gimbal = getattr(gimbal_module, "Gimbal")(**gimbal_kwargs)

        # - Load the Camera configuration from TOML:
        camera_module = scanner_config["camera"]["module"]
        camera_kwargs = scanner_config["camera"]["kwargs"]
        logger.debug(f"Camera module: {camera_module}")
        param_str = [f"\n  - {k}={v}" for k, v in camera_kwargs.items()]
        logger.debug(f"Camera parameters: {''.join(param_str)}")
        # - Import corresponding module to python:
        camera_module = importlib.import_module(camera_module)
        camera = getattr(camera_module, "Camera")(**camera_kwargs)

        return Scanner(cnc, gimbal, camera)

    def run(self, path=None, hw_scanner=None, extra_md=None):
        """Run a scan

        Parameters
        ----------
        path : plantimager.path.Path, optional
            If ``None`` (default), load the ``ScanPath`` module & get the configuration from the TOML config file.
            Else should be a ``plantimager.path.Path`` instance.
        hw_scanner : plantimager.scanner.Scanner, optional
            If ``None`` (default), load the ``CNC``, ``Gimbal`` & ``Camera`` modules & get the configuration from the
            TOML config file.
            Else should be a ``plantimager.scanner.Scanner`` instance.
        extra_md : dict, optional
            A dictionary of extra metadata to add to the 'images' fileset.

        """
        if path is None:
            path = self.get_path()
        if hw_scanner is None:
            hw_scanner = self.load_scanner()

        metadata = json.loads(luigi.DictParameter().serialize(self.metadata))
        # Import the axes limits from the ``plantimager.scanner.Scanner`` instance & add them to the "hardware" metadata
        if "hardware" not in metadata:
            logger.warning("Metadata entry 'hardware' is missing from the configuration file!")
            metadata["hardware"] = {}
        metadata["hardware"]['x_lims'] = getattr(hw_scanner.cnc, "x_lims", None)
        metadata["hardware"]['y_lims'] = getattr(hw_scanner.cnc, "y_lims", None)
        metadata["hardware"]['z_lims'] = getattr(hw_scanner.cnc, "z_lims", None)
        # Add the extra metadata to the metadata
        if extra_md is not None:
            metadata.update(extra_md)

        # Get (create) the output 'images' fileset:
        output_fileset = self.output().get()
        # Scan with the plant imager:
        hw_scanner.scan(path, output_fileset)
        # Go back close to home position:
        hw_scanner.cnc.moveto(10., 10., 10.)

        # Write the metadata to the JSON associated to the 'images' fileset:
        output_fileset.set_metadata(metadata)
        # Add a description of the type of scan data with a "channel" entry in the 'images' fileset metadata:
        output_fileset.set_metadata("channels", hw_scanner.channels())
        return


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
        scanner_config = json.loads(
            luigi.DictParameter().serialize(self.scanner))

        obj_fileset = self.input()["object"].get()
        if self.load_scene:
            scene_fileset = self.input()["scene"].get()
            for f in scene_fileset.get_files():
                logger.debug(f.id)
            self.tmpdir = io.tmpdir_from_fileset(scene_fileset)
            scanner_config["scene"] = os.path.join(self.tmpdir.name,
                                                   scene_fileset.get_file(
                                                       self.scene_file_id).filename)

        if self.render_ground_truth:
            scanner_config["classes"] = list(
                VirtualPlantConfig().classes.values())

        vscan = VirtualScanner(**scanner_config)
        while True:
            obj_file = random.choice(obj_fileset.get_files())
            if "obj" in obj_file.filename:
                break
        mtl_file = obj_fileset.get_file(obj_file.id + "_mtl")
        palette_file = None
        if self.use_palette:
            palette_file = random.choice(
                self.input()["palette"].get().get_files())
        vscan.load_object(obj_file, mtl=mtl_file, palette=palette_file)

        if self.use_hdri:
            hdri_fileset = self.input()["hdri"].get()
            hdri_file = random.choice(hdri_fileset.get_files())
            vscan.load_background(hdri_file)

        bb = vscan.get_bounding_box()
        self.output().get().set_metadata("bounding_box", bb)
        return vscan


class CalibrationScan(Scan):
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
    n_points_line : IntParameter, optional
        Number of shots taken on the orthogonal calibration lines. Defaults to ``10``.
    offset : IntParameter, optional
        Offset to axis limits, in millimeters. Defaults to ``5``.

    """
    n_points_line = luigi.IntParameter(default=11)
    offset = luigi.IntParameter(default=5)  # limits offset in mm

    def run(self):
        path = Scan().get_path()
        # Load the Scanner instance to get axes limits:
        hw_scanner = Scan().load_scanner()
        # Get axes limits:
        x_lims = getattr(hw_scanner.cnc, 'x_lims', None)
        if x_lims is not None:
            logger.info(f"Got X limits from scanner: {x_lims}")
            # Avoid true limits, as you might get stuck in some cases:
            x_lims = [x_lims[0] + self.offset, x_lims[1] - self.offset]
        y_lims = getattr(hw_scanner.cnc, 'y_lims', None)
        if y_lims is not None:
            logger.info(f"Got Y limits from scanner: {y_lims}")
            # Avoid true limits, as you might get stuck in some cases:
            y_lims = [y_lims[0] + self.offset, y_lims[1] - self.offset]
        # Get the ScanPath module:
        path_module = importlib.import_module(ScanPath().module)
        # Create a CalibrationPath instance:
        calibration_path = getattr(path_module, "CalibrationPath")(path, self.n_points_line,
                                                                   x_lims=x_lims, y_lims=y_lims)
        # Run the calibration procedure:
        Scan().run(path=calibration_path, hw_scanner=hw_scanner)


class IntrinsicCalibrationScan(Scan):
    """A task to calibrate the intrinsic parameters of the camera.

    Parameters
    ----------
    n_poses : IntParameter, optional
        Number of calibration pattern pictures to take. Defaults to ``20``.
    offset : IntParameter, optional
        Offset to axis limits, in millimeters. Defaults to ``5``.

    romi_run_task IntrinsicCalibrationScan ~/Soft/romi_db/intrinsic_calib --config ~/Soft/romi_db/scan_v2.toml --module plantimager.tasks.scan
    """
    n_poses = luigi.IntParameter(default=20)  # number of acquisitions to make
    offset = luigi.IntParameter(default=5)  # limits offset in mm

    def run(self):
        from plantimager.path import PathElement
        path = Scan().get_path()
        # Load the Scanner instance to get axes limits:
        hw_scanner = Scan().load_scanner()

        # Get axes limits:
        x_lims = getattr(hw_scanner.cnc, 'x_lims', None)
        if x_lims is not None:
            logger.info(f"Got X limits from scanner: {x_lims}")
            # Avoid true limits, as you might get stuck in some cases:
            x_lims = [x_lims[0] + self.offset, x_lims[1] - self.offset]
        else:
            x_coords = [pelt.x for pelt in path]
            x_lims = [min(x_coords), max(x_coords)]

        y_lims = getattr(hw_scanner.cnc, 'y_lims', None)
        if y_lims is not None:
            logger.info(f"Got Y limits from scanner: {y_lims}")
            # Avoid true limits, as you might get stuck in some cases:
            y_lims = [y_lims[0] + self.offset, y_lims[1] - self.offset]
        else:
            y_coords = [pelt.y for pelt in path]
            y_lims = [min(y_coords), max(y_coords)]

        # Move the camera to the center of the scanner entrance (middle of x-axis, beginning of y-axis)
        x = (x_lims[1] - x_lims[0]) // 2.
        y = y_lims[0]
        elt = PathElement(x, y, 0, 0, 0)
        # Repeat this pose `n_poses` times to create the `Path` instance:
        calibration_path = []
        for n in range(0, self.n_poses):
            calibration_path.append(elt)

        # Run the calibration procedure:
        Scan().run(path=calibration_path, hw_scanner=hw_scanner)
