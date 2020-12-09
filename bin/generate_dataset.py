#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec  6 14:14:31 2019

@author: alienor
"""
import numpy as np
import os
import random
import toml
import copy
from romidata import fsdb, io
import tempfile
import subprocess
import sys

random.seed(0.1423432)

param = sys.argv[-1]
db = sys.argv[-2]

def run(config, scan_name):
    with tempfile.TemporaryDirectory() as tempdir:
        toml.dump(config, open(os.path.join(tempdir, "config.toml"), "w"))
        subprocess.run(["romi_run_task", "--config", os.path.join(tempdir, "config.toml"), "--module", "romiscanner.scan", "VirtualScan", os.path.join(db, scan_name), "--local-scheduler", "--log-level", "WARNING"], check=True)

def basic_scan_config(config):
    config = copy.deepcopy(config)
    config["ScanPath"]["kwargs"]["center_x"] = random.randint(-5, 5)
    config["ScanPath"]["kwargs"]["center_y"] = random.randint(-5, 5)

    angle = random.randint(0, 30)
    distance = 30
    radius = distance

    config["ScanPath"]["kwargs"]["tilt"] = angle
    config["ScanPath"]["kwargs"]["radius"] = radius
    config["ScanPath"]["kwargs"]["z"] = float(distance * np.sin(angle / 180 * np.pi)) + random.randint(25, 40)

    focal = np.random.randint(20, 35)
    config["VirtualScan"]["scanner"]["focal"] = focal
    config["VirtualPlant"]["lpy_globals"]["BETA"] = random.randint(50, 90)
    config["VirtualPlant"]["lpy_globals"]["INTERNODE_LENGTH"] = 0.1 * random.randint(11, 15)
    config["VirtualPlant"]["lpy_globals"]["STEM_DIAMETER"] = 0.01 * random.randint(9, 20)
    config["VirtualPlant"]["lpy_globals"]["BETA"] = random.randint(50, 90)
    return config

def no_scene(config):
    config = copy.deepcopy(config)
    config["VirtualScan"]["load_scene"] = False
    return config

def multiple_branches(config):
    config = copy.deepcopy(config)
    config["VirtualPlant"]["lpy_globals"]["BRANCHON"] = True
    return config

def no_leaves(config):
    config = copy.deepcopy(config)
    config["VirtualPlant"]["lpy_globals"]["HAS_LEAVES"] = False
    return config

def branch_on(config):
    config = copy.deepcopy(config)
    config["VirtualPlant"]["lpy_globals"]["BRANCHON"] = True
    return config

def arabidopsis_big(config):
    config = copy.deepcopy(config)
    config["VirtualPlant"]["lpy_globals"]["MEAN_NB_DAYS"] = 50
    config["VirtualPlant"]["lpy_globals"]["STDEV_NB_DAYS"] = 5

    distance = 35
    radius = distance
    config["ScanPath"]["kwargs"]["radius"] = radius

    return config

orig_config = toml.load(param)
k = 20

config = basic_scan_config(orig_config)
config_no_scene = no_scene(config)
config_no_leaves = no_leaves(config_no_scene)
config_branch_on = branch_on(config_no_scene)
config_big_branch_on = arabidopsis_big(config_branch_on)
config_big = arabidopsis_big(config_no_scene)
config_big_scene = arabidopsis_big(config)

configs = [config,
config_no_leaves,
config_no_scene,
config_branch_on,
config_big_branch_on,
config_big,
config_big_scene]

for i in range(k):
    for j,c in enumerate(configs):
        run(c, "%06d"%(i*len(configs) + j))
