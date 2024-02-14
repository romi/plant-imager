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
import subprocess
import sys
import tempfile
from os.path import join
from pathlib import Path

import toml
from plantdb.fsdb import MARKER_FILE_NAME, LOCK_FILE_NAME
from romitask import SCAN_TOML, PIPE_TOML

LUIGI_CMD = "luigi"
LOGLEV = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
HELP_URL = "https://docs.romi-project.eu/plant_imager/tutorials/basics/"


def parsing():
    parser = argparse.ArgumentParser(
        description="Performs multiple calls to a ROMI task changing the value of a single parameter.")

    # Positional arguments:
    parser.add_argument('database_path', type=str,
                        help="Path to the database (directory) to populate with the acquisitions.")
    parser.add_argument('dataset_fmt', type=str,
                        help="Generic name to give to the datasets, should contain a `{}` to indicate the parameter position.")
    parser.add_argument('param', type=str,
                        help="Name of the parameter to change from the loaded `config`.")
    parser.add_argument('value', nargs='+',
                        help="Value(s) of the parameter to use.")
    parser.add_argument('--type', type=str, default='int', choices={'int', 'float', 'str'},
                        help="To specify the type of the parameter value(s), defaults to 'int'.")

    # Optional arguments:
    romi = parser.add_argument_group("ROMI arguments")
    romi.add_argument('--task', default="Scan",
                        help="Name of the task to perform, `Scan` by default.")
    romi.add_argument('--config', dest='config', default="",
                        help="""Pipeline configuration file or directory (JSON or TOML).
                        If a file, read the configuration from it.
                        If a directory, read & concatenate all configuration files in it""")
    romi.add_argument('--module', dest='module', default=None,
                        help="""Library and module of the task.
                        Use it if not available or different than defined in `romitask.modules.MODULES`.""")
    romi.add_argument('--log-level', dest='log_level', default='INFO', choices=LOGLEV,
                        help="Level of message logging, defaults to 'INFO'.")
    return parser


def load_config_from_directory(path):
    """Load TOML & JSON configuration files from path.

    Parameters
    ----------
    path : str
        Path to where the configuration file(s) should be.

    Returns
    -------
    dict
        The configuration dictionary, if loaded from the files.

    Notes
    -----
    We exclude the backup files ``SCAN_TOML`` & ``PIPE_TOML`` from the list of loadable files.

    """
    # List TOML config files:
    toml_list = glob.glob(os.path.join(path, "*.toml"))
    toml_list = [cfg for cfg in toml_list if cfg.split("/")[-1] not in (SCAN_TOML, PIPE_TOML)]
    # List JSON config files:
    json_list = glob.glob(os.path.join(path, "*.json"))

    if len(toml_list) == 0 and len(json_list) == 0:
        logger.critical(f"Could not find any TOML or JSON configuration file in '{path}'!")
        sys.exit("Configuration file missing!")

    config = {}
    # Read TOML configs
    for f in toml_list:
        try:
            c = toml.load(open(f))
            config = {**config, **c}
        except:
            logger.warning(f"Could not process TOML config file: {f}")
        else:
            logger.info(f"Loaded configuration file: {f}")
    # Read JSON configs:
    for f in json_list:
        try:
            c = json.load(open(f))
            config = {**config, **c}
        except:
            logger.warning(f"Could not process JSON config file: {f}")
        else:
            logger.info(f"Loaded configuration file: {f}")

    return config


def load_config_from_file(path):
    """Load TOML or JSON configuration file from path.

    Parameters
    ----------
    path : str
        Path to the configuration file to load.

    Returns
    -------
    dict
        The configuration dictionary.

    """
    config = None
    if path.endswith("toml"):
        try:
            config = toml.load(open(path))
        except:
            logger.critical(f"Could not load TOML configuration file '{path}'!")
    elif path.endswith("json"):
        try:
            config = json.load(open(path))
        except:
            logger.critical(f"Could not load JSON configuration file '{path}'!")
    else:
        logger.critical(f"Unsupported configuration file format, should be TOML or JSON!")

    if config is None:
        sys.exit(f"Error while loading configuration file!")

    return config


def _check_markers(path):
    if not isinstance(path, Path):
        path = Path(path)
    # - Make sure the `romidb` marker file exists:
    marker_file = path / MARKER_FILE_NAME
    try:
        marker_file.touch()
    except:
        pass
    # - Make sure the `lock` file do NOT exist:
    lock_file = path / LOCK_FILE_NAME
    try:
        lock_file.unlink()
        # lock_file.unlink(missing_ok=True)  # missing_ok only available since Python3.8
    except:
        pass
    return


def main():
    # - Parse the input arguments to variables:
    parser = parsing()
    args = parser.parse_args()

    # - Configure a logger from this application:
    from plantimager.log import configure_logger

    global logger
    logger = configure_logger('multi_scan')

    # Check the database path exists and have the required ROMI marker files:
    db_path = args.database_path
    if not os.path.isdir(db_path):
        os.makedirs(db_path, exist_ok=True)
    _check_markers(db_path)

    # Load the config:
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

    # Find the section and parameter name from the input argument:
    param = args.param
    print(param)
    if '.' in param:
        section = param.split('.')
        param_name = section.pop(-1)
    else:
        section = ["ScanPath", "kwargs"]
        param_name = param

    logger.info(f"Got parameter '{param_name}' from section '{'.'.join(section)}'...")
    logger.info(f"Got a list of parameter values: {args.value}")

    # Add a formatter:
    if "{}" not in args.dataset_fmt:
        args.dataset_fmt += "_{}"

    # For each value
    for value in args.value:
        # Set the name of the dataset to create:
        dataset = args.dataset_fmt.format(value)
        # Set the value of the parameter in configuration dict:
        section_cfg = config
        for k in section:
            section_cfg = section_cfg.get(k)
        section_cfg[param_name] = eval(f"{args.type}(value)")  # convert to correct type
        # Save the config dict to a TOML and run a Scan:
        with tempfile.TemporaryDirectory() as tempdir:
            tmp_cfg = join(tempdir, "config.toml")
            toml.dump(config, open(tmp_cfg, "w"))
            # Create the command to execute:
            cmd = ["romi_run_task", args.task, join(args.database_path, dataset),
                   "--config", tmp_cfg]
            if args.module is not None:
                cmd += ["--module", args.module]
            if args.log_level != "":
                cmd += ["--log-level", args.log_level]
            # - Start the configured pipeline:
            logger.info(cmd)
            subprocess.run(cmd, env={**os.environ}, check=True)

    return


if __name__ == '__main__':
    main()