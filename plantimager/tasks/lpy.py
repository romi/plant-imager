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

import json
import os
import random
import re
import subprocess
import tempfile

import luigi

from plantimager.configs.lpy import VirtualPlantConfig
from plantimager.lpy import LpyFileset
from romitask import RomiTask
from romitask.log import configure_logger

logger = configure_logger(__name__)


class VirtualPlant(RomiTask):
    """Task generating a virtual plant from an LPY model.

    Attributes
    ----------
    upstream_task : plantimager.lpy.LpyFileset
        The fileset specific to LPY model.
    lpy_file_id : luigi.Parameter
        Name of the LPY file used as model.
        Should exist in the `LpyFileset`.
    metadata : list
        The list of metadata to export with the model.
        By default, ask for "angles" & "internodes".
    lpy_globals : dict
        Global LPY variables used by `lpy.Lsystem()` method.
        By default, set the "SEED" LPY variable to a random integer in ``[0, 100000]``.
    """
    upstream_task = LpyFileset
    lpy_file_id = luigi.Parameter()
    metadata = luigi.ListParameter(default=["angles", "internodes"])
    lpy_globals = luigi.DictParameter(default={"SEED": random.randint(0, 100000)})

    def run(self):
        """Generates the virtual plant."""
        from openalea import lpy
        from openalea.plantgl import all

        lpy_globals = json.loads(luigi.DictParameter().serialize(self.lpy_globals))

        with tempfile.TemporaryDirectory() as tmpdir:
            x = self.input().get().get_file(self.lpy_file_id)
            tmp_filename = os.path.join(tmpdir, "f.lpy")
            with open(tmp_filename, "wb") as f:
                f.write(x.read_raw())

            lsystem = lpy.Lsystem(tmp_filename, globals=lpy_globals)
            for lstring in lsystem:
                t = all.PglTurtle()
                lsystem.turtle_interpretation(lstring, t)
            scene = t.getScene()

            output_file = self.output_file()
            fname = os.path.join(tmpdir, "plant.obj")
            scene.save(fname)
            classes = luigi.DictParameter().serialize(VirtualPlantConfig().classes).replace(" ", "")

            logger.info("Splitting mesh by classes in Blender with `romi_split_by_material`...")
            subprocess.run(["romi_split_by_material", "--", "--classes", classes, fname, fname], check=True)

            logger.info("Cleaning mesh in Blender with `romi_clean_mesh`...")
            subprocess.run(["romi_clean_mesh", "--", fname, fname], check=True)

            output_file.import_file(fname)
            output_mtl_file = self.output().get().create_file(output_file.id + "_mtl")
            output_mtl_file.import_file(fname.replace("obj", "mtl"))

        # -- UGLY HACK --
        # We need to replace the MTL file name referenced in OBJ file!
        # The OBJ file is originally saved as a temporary file named 'plant.obj' by `scene.save(fname)`
        # The associated MTL (material) file is thus named 'plant.mtl'...
        # We thus edit the `output_file` OBJ file to match the renaming done by `output_mtl_file.import_file()`
        # ---------------
        # - Load the OBJ to edit:
        with open(output_file.path(), "r") as f:
            obj_lines = f.readlines()
            # It seems that there is only one ref to the 'plant.mtl' file but, just in case, we check all lines...
            fixed_obj_lines = [re.sub('plant.mtl', f'{output_mtl_file.id}.mtl', line) for line in obj_lines]
        # - Save the fixed version:
        with open(output_file.path(), "w") as f:
            f.writelines(fixed_obj_lines)

        # - Export 'angles' and 'internodes' as metadata of the OBJ file:
        measures = {}
        for m in self.metadata:
            m_val = lsystem.context().globals()[m]
            if m in ["angles", "internodes"]:
                measures[m] = m_val
            output_file.set_metadata(m, m_val)

        # - Export 'angles' and 'internodes' to a 'measures.json' file (to match manual measurements method):
        from plantdb.fsdb import _scan_measures_path
        measures_json = _scan_measures_path(output_file.get_scan())
        with open(measures_json, 'w') as f:
            f.write(json.dumps(measures, indent=4))