#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# romiscanner - Python tools for the ROMI 3D Scanner
#
# Copyright (C) 2018 Sony Computer Science Laboratories
# Authors: D. Colliaux, T. Wintz, P. Hanappe
#
# This file is part of romiscanner.
#
# romiscanner is free software: you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# romiscanner is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with romiscanner.  If not, see
# <https://www.gnu.org/licenses/>.

class SonyCamError(Exception):
    def __init__(self, message):
        self.message = message


class FlashAirAPIError(Exception):
    def __init__(self, message):
        self.message = message


class ScannerError(Exception):
    pass


class PathError(ScannerError):
    pass
from romitask.task import FilesetExists

import luigi

import logging

logger = logging.getLogger('plantimager')


class LpyFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "lpy"
