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
    """This task check the existence of a `'data'` Fileset.

    Attributes
    ----------
    upstream_task : None
        No upstream task is required.
    scan_id : luigi.Parameter
        The id of the scan dataset that should contain the fileset.
    fileset_id : str
        The name of the fileset that should exist.
    """
    scan_id = luigi.Parameter()
    fileset_id = "data"


class HdriFileset(FilesetExists):
    """This task check the existence of a `'hdri'` Fileset.

    Attributes
    ----------
    upstream_task : None
        No upstream task is required.
    scan_id : luigi.Parameter
        The id of the scan dataset that should contain the fileset.
    fileset_id : str
        The name of the fileset that should exist.
    """
    scan_id = luigi.Parameter()
    fileset_id = "hdri"


class SceneFileset(FilesetExists):
    """This task check the existence of a `'scenes'` Fileset.

    Attributes
    ----------
    upstream_task : None
        No upstream task is required.
    scan_id : luigi.Parameter
        The id of the scan dataset that should contain the fileset.
    fileset_id : str
        The name of the fileset that should exist.
    """
    scan_id = luigi.Parameter()
    fileset_id = "scenes"


class PaletteFileset(FilesetExists):
    """This task check the existence of a `'palette'` Fileset.

    Attributes
    ----------
    upstream_task : None
        No upstream task is required.
    scan_id : luigi.Parameter
        The id of the scan dataset that should contain the fileset.
    fileset_id : str
        The name of the fileset that should exist.
    """
    scan_id = luigi.Parameter()
    fileset_id = "palette"


class ScannerToCenter(RomiTask):
    """A task to move the camera at the center of the path.

    Attributes
    ----------
    upstream_task : None
        No upstream task is required.
    scan_id : luigi.Parameter, optional
        The scan id to use to get or create the ``FilesetTarget``.
    """
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
    """A task for running a scan, real or virtual.

    Module: romiscan.tasks.scan
    Default upstream tasks: None

    Attributes
    ----------
    upstream_task : None
        No upstream task is required by a `Scan` task.
    scan_id : luigi.Parameter, optional
        The scan id to use to create the ``FilesetTarget``.
    metadata : luigi.DictParameter, optional
        Metadata of the scan. Defaults to an empty dictionary.
    scanner : luigi.DictParameter, optional
        Scanner configuration to use for this task. (TODO: see hardware documentation)
        Defaults to an empty dictionary.

    """
    upstream_task = None
    metadata = luigi.DictParameter(default={})
    scanner = luigi.DictParameter(default={})

    def requires(self):
        """Nothing is required."""
        return []

    def output(self):
        """The output fileset associated to a ``Scan`` task is an 'images' dataset."""
        return FilesetTarget(DatabaseConfig().scan, "images")

    def get_path(self) -> path.Path:
        """Load the ``ScanPath`` module & get the configuration from the TOML config file."""
        path_module = importlib.import_module(ScanPath().module)
        path = getattr(path_module, ScanPath().class_name)(**ScanPath().kwargs)
        return path

    def load_scanner(self) -> Scanner:
        """Load the ``CNC``, ``Gimbal`` & ``Camera`` modules and create a ``Scanner`` instance."""
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

    def run(self, path=None, scanner=None, extra_md=None):
        """Run a scan.

        Parameters
        ----------
        path : plantimager.path.Path, optional
            If ``None`` (default), load the ``ScanPath`` module & get the configuration from the TOML config file.
            Else should be a ``plantimager.path.Path`` instance.
        scanner : plantimager.scanner.Scanner or plantimager.scanner.VirtualScanner, optional
            If ``None`` (default), load the configuration from the TOML config file with `self.load_scanner`.
            Else should be a ``Scanner`` or ``VirtualScanner`` instance.
        extra_md : dict, optional
            A dictionary of extra metadata to add to the 'images' fileset.

        """
        if path is None:
            path = self.get_path()
        if scanner is None:
            scanner = self.load_scanner()

        metadata = json.loads(luigi.DictParameter().serialize(self.metadata))
        # Import the axes limits from the ``plantimager.scanner.Scanner`` instance & add them to the "hardware" metadata
        if "hardware" not in metadata:
            logger.warning("Metadata entry 'hardware' is missing from the configuration file!")
            metadata["hardware"] = {}

        if isinstance(scanner, Scanner):
            metadata["hardware"]['x_lims'] = getattr(scanner.cnc, "x_lims", None)
            metadata["hardware"]['y_lims'] = getattr(scanner.cnc, "y_lims", None)
            metadata["hardware"]['z_lims'] = getattr(scanner.cnc, "z_lims", None)

        # Add the extra metadata to the metadata:
        if extra_md is not None:
            metadata.update(extra_md)
        # Add the acquisition time to the metadata:
        from plantimager.utils import now
        metadata["acquisition_date"] = now()

        # Get (create) the output 'images' fileset:
        output_fileset = self.output().get()
        # Scan with the plant imager:
        scanner.scan(path, output_fileset)
        if isinstance(scanner, Scanner):
            # Go back close to home position:
            scanner.cnc.moveto(10., 10., 10.)

        # Write the metadata to the JSON associated to the 'images' fileset:
        output_fileset.set_metadata(metadata)
        # Add a description of the type of scan data with a "channel" entry in the 'images' fileset metadata:
        output_fileset.set_metadata("channels", scanner.channels())
        return


class VirtualScan(Scan):
    """Task to create scans of virtual plants using Blender.

    Attributes
    ----------
    upstream_task : None
        No upstream task is required by a `VirtualScan` task.
    scan_id : luigi.Parameter, optional
        The scan id to use to create the ``FilesetTarget``.
    metadata : luigi.DictParameter, optional
        Metadata of the scan. Defaults to an empty dictionary.
    scanner : luigi.DictParameter, optional
        VirtualScanner configuration to use for this task.
        Defaults to an empty dictionary.
    load_scene : luigi.BoolParameter, optional
        Whether to load the scene file.
        Defaults to ``False``.
    scene_file_id : luigi.Parameter, optional
        The name of the scene file to load, if any.
        Defaults to an empty string.
    use_palette : luigi.BoolParameter, optional
        Whether to use a color palette to rendre the virtual plant.
        Defaults to ``False``.
    use_hdri : luigi.BoolParameter, optional
        Whether to use an HDRI file for the background.
        Defaults to ``False``.
    obj_fileset : luigi.TaskParameter, optional
        The Fileset that contains the virtual plant OBJ file to render and capture.
        Defaults to ``VirtualPlant``.
    hdri_fileset : luigi.TaskParameter, optional
        The Fileset that contains the HDRI files to use as background.
        Defaults to ``HdriFileset``.
    scene_fileset : luigi.TaskParameter, optional
        The Fileset that contain the scenes to use.
        Defaults to ``SceneFileset``.
    palette_fileset : luigi.TaskParameter, optional
        The Fileset that contains the color palette to use to render the virtual plant.
        Defaults to ``PaletteFileset``.
    render_ground_truth : luigi.BoolParameter, optional
        If ``True``, create the mask image for defined ground truth classes in virtual plant model.
        Defaults to ``False``.
    colorize : bool, optional
        Whether the virtual plant should be colorized in Blender.
        Defaults to ``True``.

    """
    load_scene = luigi.BoolParameter(default=False)
    scene_file_id = luigi.Parameter(default="")

    use_palette = luigi.BoolParameter(default=False)
    use_hdri = luigi.BoolParameter(default=False)

    obj_fileset = luigi.TaskParameter(default=VirtualPlant)
    hdri_fileset = luigi.TaskParameter(default=HdriFileset)
    scene_fileset = luigi.TaskParameter(default=SceneFileset)
    palette_fileset = luigi.TaskParameter(default=PaletteFileset)

    render_ground_truth = luigi.BoolParameter(default=False)
    colorize = luigi.BoolParameter(default=True)

    def requires(self):
        """Defines the ``VirtualScan`` task requirements.

        Always require a `Fileset` that contains a virtual plant.
        It can be an ``ObjFileset`` or the output of the ``VirtualPlant`` task.
        If the use of an HDRI is required, check the ``HdriFileset`` exists.
        If the use of a color palette is required, check the ``PaletteFileset`` exists.
        If the use of a scene is required, check the ``SceneFileset`` exists.

        Notes
        -----
        Overrides the method from ``Scan``.
        """
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
        """Create the virtual scanner configuration and defines the files it.

        Returns
        -------
        plantimager.vscan.VirtualScanner
            The configured virtual scanner.

        Notes
        -----
        Overrides the method from ``Scan``.
        """
        # - Create the virtual scanner configuration (from TOML section 'VirtualScan.scanner'):
        scanner_config = json.loads(luigi.DictParameter().serialize(self.scanner))

        # - Defines the virtual plant files:
        # Get the `Fileset` containing the OBJ & MTL files:
        obj_fileset = self.input()["object"].get()
        # Get the OBJ `File`:
        while True:
            # Randomly pick one of the files from the fileset...
            obj_file = random.choice(obj_fileset.get_files())
            if "obj" in obj_file.filename:
                # ...stop when "obj" is found in the filename
                break
        # Get the MTL `File`:
        try:
            mtl_file = obj_fileset.get_file(obj_file.id + "_mtl")
        except:
            mtl_file = None

        # - Defines the palette `File`, if requested:
        palette_file = None
        if self.use_palette:
            # Randomly choose among existing palette files:
            palette_fileset = self.input()["palette"].get()
            palette_file = random.choice(palette_fileset.get_files())

        # - Defines the hdri `File`, if requested:
        hdri_file = None
        if self.use_hdri:
            # Randomly choose among existing hdri files:
            hdri_fileset = self.input()["hdri"].get()
            hdri_file = random.choice(hdri_fileset.get_files())

        # - Defines the scene `File`, if requested:
        if self.load_scene:
            scene_fileset = self.input()["scene"].get()
            # Duplicate all files in a temporary directory: (TODO: why?!)
            self.tmpdir = io.tmpdir_from_fileset(scene_fileset)
            # Use the selected `scene_file_id` to get the `File`:
            scene_file = scene_fileset.get_file(self.scene_file_id).filename
            # Add its path to the virtual scanner config to create:
            scanner_config["scene"] = os.path.join(self.tmpdir.name, scene_file)

        # - Defines the list of classes to create ground-truth images for, if requested:
        if self.render_ground_truth:
            # Add the list of classes names to the virtual scanner config to create:
            scanner_config["classes"] = list(VirtualPlantConfig().classes.values())

        # - Instantiate the `VirtualScanner` using the config:
        vscan = VirtualScanner(**scanner_config)
        # - Load the defined OBJ, MTL and palette files to Blender:
        vscan.load_object(obj_file, mtl=mtl_file, palette=palette_file, colorize=self.colorize)
        # - Load the HDRI files to Blender, if requested:
        if self.use_hdri:
            vscan.load_background(hdri_file)
        # Get the bounding-box from Blender & add it to the output fileset metadata:
        bbox = vscan.get_bounding_box()
        self.output().get().set_metadata("bounding_box", bbox)

        return vscan


class CalibrationScan(Scan):
    """A task for running a scan, real or virtual, with a calibration path.

    Module: romiscan.tasks.scan
    Colmap poses for subsequent scans. (TODO: see calibration documentation)
    Default upstream tasks: None

    Parameters
    ----------
    metadata : luigi.DictParameter
        metadata for the scan
    scanner : luigi.DictParameter
        scanner hardware configuration (TODO: see hardware documentation)
    path : luigi.DictParameter
        scanner path configuration (TODO: see hardware documentation)
    n_points_line : luigi.IntParameter, optional
        Number of shots taken on the orthogonal calibration lines. Defaults to ``10``.
    offset : luigi.IntParameter, optional
        Offset to axis limits, in millimeters. Defaults to ``5``.

    """
    n_points_line = luigi.IntParameter(default=11)
    offset = luigi.IntParameter(default=5)  # limits offset in mm

    def run(self):
        """Run the calibration scan.

        Notes
        -----
        Overrides the method from ``Scan``.
        """
        path = Scan().get_path()
        # Load the Scanner instance to get axes limits:
        scanner = Scan().load_scanner()
        # Get axes limits:
        x_lims = getattr(scanner.cnc, 'x_lims', None)
        if x_lims is not None:
            logger.info(f"Got X limits from scanner: {x_lims}")
            # Avoid true limits, as you might get stuck in some cases:
            x_lims = [x_lims[0] + self.offset, x_lims[1] - self.offset]
        y_lims = getattr(scanner.cnc, 'y_lims', None)
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
        Scan().run(path=calibration_path, scanner=scanner)


class IntrinsicCalibrationScan(Scan):
    """A task to calibrate the intrinsic parameters of the camera.

    Parameters
    ----------
    n_poses : luigi.IntParameter, optional
        Number of calibration pattern pictures to take. Defaults to ``20``.
    offset : luigi.IntParameter, optional
        Offset to axis limits, in millimeters. Defaults to ``5``.

    romi_run_task IntrinsicCalibrationScan ~/Soft/romi_db/intrinsic_calib --config ~/Soft/romi_db/scan_v2.toml --module plantimager.tasks.scan
    """
    n_poses = luigi.IntParameter(default=20)  # number of acquisitions to make
    offset = luigi.IntParameter(default=5)  # limits offset in mm

    def run(self):
        from plantimager.path import PathElement
        path = Scan().get_path()
        # Load the Scanner instance to get axes limits:
        scanner = Scan().load_scanner()

        # Get axes limits:
        x_lims = getattr(scanner.cnc, 'x_lims', None)
        if x_lims is not None:
            logger.info(f"Got X limits from scanner: {x_lims}")
            # Avoid true limits, as you might get stuck in some cases:
            x_lims = [x_lims[0] + self.offset, x_lims[1] - self.offset]
        else:
            x_coords = [pelt.x for pelt in path]
            x_lims = [min(x_coords), max(x_coords)]

        y_lims = getattr(scanner.cnc, 'y_lims', None)
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
        Scan().run(path=calibration_path, scanner=scanner)
