#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# romitask - Task handling tools for the ROMI project
#
# Copyright (C) 2018-2019 Sony Computer Science Laboratories
# Authors: D. Colliaux, T. Wintz, P. Hanappe
#
# This file is part of romitask.
#
# romitask is free software: you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# romitask is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with romitask.  If not, see
# <https://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

""" Multiple imaging with varying parameters to assess/test acquisition or reconstruction pipelines.
"""

import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import toml
from pathlib import Path
from romitask.log import get_logging_config
from romitask.modules import MODULES
from romitask.modules import TASKS

from romitask import SCAN_TOML, PIPE_TOML

LUIGI_CMD = "luigi"
LOGLEV = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
HELP_URL = "https://docs.romi-project.eu/plant_imager/tutorials/basics/"


def parsing():
    parser = argparse.ArgumentParser(
        description="Performs multiple calls to Scan.")

    # Positional arguments:
    parser.add_argument('database_path', type='str',
                        help="Path to the database (directory) to populate with the acquisitions.")
    parser.add_argument('dataset_fmt', type=str,
                        help="Name to give to the datasets, must contain a `{}` to indicate the parameter position.")
    parser.add_argument('param', type='str',
                        help="Name of the parameter to change.")
    parser.add_argument('value', nargs='+',
                        help="Value(s) of the parameter to change.")

    # Optional arguments:
    parser.add_argument('--config', dest='config', default="",
                        help="""Pipeline configuration file or directory (JSON or TOML).
                        If a file, read the configuration from it.
                        If a directory, read & concatenate all configuration files in it.
                        By default, search in the selected dataset directory.""")
    parser.add_argument('--module', dest='module', default=None,
                        help="""Library and module of the task.
                        Use it if not available or different than defined in `romitask.modules.MODULES`.""")
    parser.add_argument('--log-level', dest='log_level', default='INFO', choices=LOGLEV,
                        help="Level of message logging, defaults to 'INFO'.")

    # Luigi related arguments:
    luigi = parser.add_argument_group("luigi options")
    luigi.add_argument('--luigicmd', dest='luigicmd', default=LUIGI_CMD,
                       help=f"Luigi command, defaults to `{LUIGI_CMD}`.")
    luigi.add_argument('--local-scheduler', dest='ls', action="store_true", default=True,
                       help="Use the local luigi scheduler, defaults to `True`.")
    return parser


def main(args):
    if args.config != "" and not os.path.isfile(args.config) and not os.path.isdir(args.config):
        logger.critical(f"Could not understand `config` option '{args.config}'!")
        sys.exit("Error with configuration file!")
    elif os.path.isdir(args.config):
        config = load_config_from_directory(args.config)
    elif os.path.isfile(args.config):
        config = load_config_from_file(args.config)
    else:
        logger.critical(f"A path or TOML file is required as `config`, got {args.config}!")
        sys.exit("Error with configuration file!")

    param = args.param
    if '.' in param:
        section = '.'.join('.'.split(param)[:-1])
        param_name = '.'.split(param)[-1]
    else:
        section = "ScanPath.kwargs"
        param_name = param

    for value in args.value:
        dataset = args.dataset_fmt.format(value)
        config[section][param_name] = value
        with tempfile.TemporaryDirectory() as tempdir:
            tmp_cfg = os.path.join(tempdir, "config.toml")
            toml.dump(config, open(tmp_cfg, "w"))
        cmd = ["romi_run_task", "Scan", join(args.database_path, dataset),
               "--config", tmp_cfg]
        # - Start the configured pipeline:
        subprocess.run(cmd, env={**os.environ, **env}, check=True)

    return


if __name__ == '__main__':
    # - Parse the input arguments to variables:
    parser = parsing()
    args = parser.parse_args()

    # - Configure a logger from this application:
    from romitask.log import configure_logger

    global logger
    logger = configure_logger('romi_run_task')

    folders = sorted(glob.glob(args.dataset_path))

    if len(folders) > 1:
        fnames = [Path(folder).name for folder in folders]
        logger.info(f"Got a list of {len(folders)} scan dataset to analyze: {', '.join(fnames)}")
        for folder in folders:
            args.dataset_path = folder
            try:
                main(args)
            except Exception as e:
                print(e)
    else:
        args.dataset_path = folders[0]
        main(args)
