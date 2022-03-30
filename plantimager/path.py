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

import math
from collections.abc import Iterable

import numpy as np


class Pose(object):
    """Abstract representation of a 'camera pose' as its 5D coordinates.

    Examples
    --------
    >>> from plantimager.path import Pose
    >>> p = Pose(50, 250, 80, 270, 0)
    >>> print(p)
    x: 50, y: 250, z: 80, pan: 270, tilt: 0

    """

    def __init__(self, x=None, y=None, z=None, pan=None, tilt=None):
        """Pose constructor.

        Parameters
        ----------
        x : length_mm, optional
            Relative distance to the origin along the x-axis.
        y : length_mm, optional
            Relative distance to the origin along the y-axis.
        z : length_mm, optional
            Relative distance to the origin along the z-axis.
        pan : deg, optional
            Relative rotation to the origin along the xy-plane.
        tilt : deg, optional
            Relative rotation to the origin orthogonal to the xy-plane.
        """
        self.x = x
        self.y = y
        self.z = z
        self.pan = pan
        self.tilt = tilt

    def __repr__(self):
        return ", ".join(f"{k}: {v}" for k, v in self.__dict__.items())

    def attributes(self):
        return ["x", "y", "z", "pan", "tilt"]


class PathElement(Pose):
    """Singleton for a `Path` class.

    See Also
    --------
    plantimager.path.Pose

    Examples
    --------
    >>> from plantimager.path import PathElement
    >>> elt = PathElement(50, 250, 80, 270, 0, True)
    >>> print(elt)
    x: 50, y: 250, z: 80, pan: 270, tilt: 0, exact_pose: True

    """

    def __init__(self, x=None, y=None, z=None, pan=None, tilt=None, exact_pose=True):
        """
        Parameters
        ----------
        x : length_mm, optional
            Relative distance, in millimeters, to the origin along the x-axis.
        y : length_mm, optional
            Relative distance, in millimeters, to the origin along the y-axis.
        z : length_mm, optional
            Relative distance, in millimeters, to the origin along the z-axis.
        pan : deg, optional
            Relative rotation, in degrees, to the origin along the xy-plane.
        tilt : deg, optional
            Relative rotation, in degrees, to the origin along the xy-plane.
        exact_pose : bool, optional
            If ``True``, the above parameter values are exact, else they are approximations.

        """
        super().__init__(x, y, z, pan, tilt)
        self.exact_pose = exact_pose

    def __repr__(self):
        return ", ".join(f"{k}: {v}" for k, v in self.__dict__.items())


class Path(list):
    """A path is an abstract class that should be a list of ``PathElement`` instances."""

    def __init__(self):
        super().__init__()


def circle(center_x, center_y, radius, n_points):
    """Create a 2D circle of N points with given center and radius.

    Pan orientations are also computed to always face the center of the circle.

    Parameters
    ----------
    center_x : length_mm
        Relative position of the circle center along the X-axis.
    center_y : length_mm
        Relative position of the circle center along the Y-axis.
    radius : length_mm
        Radius of the circle to create.
    n_points : int
        Number of points used to create the circle.

    Returns
    -------
    list of length_mm
        Sequence of x positions.
    list of length_mm
        Sequence of y positions.
    list of deg
        Sequence of pan orientations.

    Examples
    --------
    >>> from plantimager.path import circle
    >>> x, y, p = circle(0, 0, 5, 5)
    >>> list(zip(x, y, p))  # to get set of 2D coordinates (x, y) and associated pan.
    [(-5.0, 0.0, 270.0),
     (-1.5450849718747373, -4.755282581475767, 342.0),
     (4.045084971874736, -2.9389262614623664, 54.0),
     (4.045084971874738, 2.938926261462365, 126.0),
     (-1.5450849718747361, 4.755282581475768, 198.0)]

    """
    x, y, p = [], [], []
    for i in range(n_points):
        pan = 2 * i * math.pi / n_points
        x.append(center_x - radius * math.cos(pan))
        y.append(center_y - radius * math.sin(pan))
        pan = pan * 180 / math.pi
        p.append((pan - 90) % 360)

    return x, y, p


class Circle(Path):
    """Creates a circular path for the scanner.

    Compute the `x`, `y` & `pan` ``PathElement`` values to create that circle.

    Notes
    -----
    The `pan` is computed to always face the center of the circle.
    If an iterable is given for `tilt`, performs more than one camera acquisition at same xyz position.

    See Also
    --------
    plantimager.path.circle

    Examples
    --------
    >>> from plantimager.path import Circle
    >>> circular_path = Circle(200, 200, 50, 0, 200, 9)
    >>> circular_path
    [x: 0.0, y: 200.0, z: 50, pan: 270.0, tilt: 0, exact_pose: False,
     x: 46.791111376204384, y: 71.44247806269215, z: 50, pan: 310.0, tilt: 0, exact_pose: False,
     x: 165.27036446661393, y: 3.038449397558395, z: 50, pan: 350.0, tilt: 0, exact_pose: False,
     x: 299.99999999999994, y: 26.794919243112247, z: 50, pan: 29.999999999999986, tilt: 0, exact_pose: False,
     x: 387.93852415718163, y: 131.59597133486622, z: 50, pan: 70.0, tilt: 0, exact_pose: False,
     x: 387.9385241571817, y: 268.40402866513375, z: 50, pan: 110.0, tilt: 0, exact_pose: False,
     x: 300.0000000000001, y: 373.2050807568877, z: 50, pan: 149.99999999999997, tilt: 0, exact_pose: False,
     x: 165.270364466614, y: 396.96155060244166, z: 50, pan: 190.0, tilt: 0, exact_pose: False,
     x: 46.79111137620444, y: 328.5575219373079, z: 50, pan: 230.0, tilt: 0, exact_pose: False]
    >>> circular_path = Circle(200, 200, 50, (0, 10), 200, 2)
    >>> circular_path
    [x: 0.0, y: 200.0, z: 50, pan: 270.0, tilt: 0, exact_pose: False,
     x: 0.0, y: 200.0, z: 50, pan: 270.0, tilt: 10, exact_pose: False,
     x: 400.0, y: 199.99999999999997, z: 50, pan: 90.0, tilt: 0, exact_pose: False,
     x: 400.0, y: 199.99999999999997, z: 50, pan: 90.0, tilt: 10, exact_pose: False]

    """

    def __init__(self, center_x, center_y, z, tilt, radius, n_points):
        """
        Parameters
        ----------
        center_x : length_mm
            X-axis position, in millimeters, of the circle's center, relative to the origin.
        center_y : length_mm
            Y-axis position, in millimeters, of the circle's center, relative to the origin.
        z : length_mm
            Height at which to make the circle.
        tilt : deg or list(deg)
            Camera tilt(s), in degrees, to use for this circle.
            If an iterable is given, performs more than one camera acquisition at same xyz position.
        radius : length_mm
            Radius, in millimeters, of the circular path to create.
        n_points : int
            Number of points (``PathElement``) used to generate the circular path.
        """
        super().__init__()
        x, y, pan = circle(center_x, center_y, radius, n_points)

        if not isinstance(tilt, Iterable):
            tilt = [tilt]

        for i in range(n_points):
            for t in tilt:
                self.append(PathElement(x[i], y[i], z, pan[i], t, exact_pose=False))


class Cylinder(Path):
    """Creates a z-axis aligned cylinder path for the scanner.

    Makes as much circular paths as `n_circles` within the given z range.

    Notes
    -----
    The `pan` is computed to always face the center of the circle.
    If an iterable is given for `tilt`, performs more than one camera acquisition at same xyz position.

    See Also
    --------
    plantimager.path.circle

    Examples
    --------
    >>> from plantimager.path import Cylinder
    >>> cylinder_path = Cylinder(200, 200, (0, 50), 0, 200, n_points=2, n_circles=2)
    >>> cylinder_path
    [x: 0.0, y: 200.0, z: 0, pan: 270.0, tilt: 0, exact_pose: False,
     x: 400.0, y: 199.99999999999997, z: 0, pan: 90.0, tilt: 0, exact_pose: False,
     x: 0.0, y: 200.0, z: 50, pan: 270.0, tilt: 0, exact_pose: False,
     x: 400.0, y: 199.99999999999997, z: 50, pan: 90.0, tilt: 0, exact_pose: False]
    >>> cylinder_path = Cylinder(200, 200, (0, 50), 0, 200, n_points=2, n_circles=3)
    >>> cylinder_path
    [x: 0.0, y: 200.0, z: 0.0, pan: 270.0, tilt: 0, exact_pose: False,
     x: 400.0, y: 199.99999999999997, z: 0.0, pan: 90.0, tilt: 0, exact_pose: False,
     x: 0.0, y: 200.0, z: 25.0, pan: 270.0, tilt: 0, exact_pose: False,
     x: 400.0, y: 199.99999999999997, z: 25.0, pan: 90.0, tilt: 0, exact_pose: False,
     x: 0.0, y: 200.0, z: 50.0, pan: 270.0, tilt: 0, exact_pose: False,
     x: 400.0, y: 199.99999999999997, z: 50.0, pan: 90.0, tilt: 0, exact_pose: False]

    """

    def __init__(self, center_x, center_y, z_range, tilt, radius, n_points, n_circles=2):
        """
        Parameters
        ----------
        center_x : length_mm
            X-axis position, in millimeters, of the circle's center, relative to the origin.
        center_y : length_mm
            Y-axis position, in millimeters, of the circle's center, relative to the origin.
        z_range : (length_mm, length_mm)
            Height range, in millimeters, at which to make the cylinder.
        tilt : deg or list of deg
            Camera tilt(s), in degrees, to use for this circle.
            If an iterable is given, performs more than one camera acquisition at same xyz position.
        radius : length_mm
            Radius of the circular path to create.
        n_points : int
            Number of points (``PathElement``) used to generate the circular path.
        n_circles : int, optional
            Number of circular path to make within the cylinder, minimum value is 2.

        Raises
        ------
        ValueError
            If the number of circles `n_circles` is not superior or equal to `2`.

        """
        super().__init__()

        try:
            assert n_circles >= 2
        except AssertionError:
            raise ValueError("You need a minimum of two circles to make a cylinder!")

        min_z, max_z = z_range
        for z_circle in np.arange(min_z, max_z + 1, (max_z - min_z) / float(n_circles-1)):
            self.extend(Circle(center_x, center_y, z_circle, tilt, radius, n_points))


def line1d(start, stop, n_points):
    """Create a 1D line of N points between start and stop position (included).

    Parameters
    ----------
    start : length_mm
        Line starting position, in millimeters.
    stop : length_mm
        Line ending position, in millimeters.
    n_points : int
        Number of points used to create the line of points.

    Returns
    -------
    list of length_mm
        Sequence of 1D positions.

    Examples
    --------
    >>> from plantimager.path import line1d
    >>> line1d(0, 10, n_points=5)
    [0.0, 2.5, 5.0, 7.5, 10.0]

    """
    return [(1 - i / (n_points - 1)) * start + (i / (n_points - 1)) * stop for i in range(n_points)]


def line3d(x_start, y_start, z_start, x_stop, y_stop, z_stop, n_points):
    """Create a 3D line of N points between start and stop position (included).

    Parameters
    ----------
    x_start : length_mm
        Line starting position, in millimeters, for the x-axis.
    y_start : length_mm
        Line starting position, in millimeters, for the y-axis.
    z_start : length_mm
        Line starting position, in millimeters, for the z-axis.
    x_stop : length_mm
        Line ending position, in millimeters, for the x-axis.
    y_stop : length_mm
        Line ending position, in millimeters, for the y-axis.
    z_stop : length_mm
        Line ending position, in millimeters, for the z-axis.
    n_points : int
        Number of points used to create the linear path.

    Returns
    -------
    list of length_mm
        Sequence of x positions.
    list of length_mm
        Sequence of y positions.
    list of length_mm
        Sequence of z positions.

    Examples
    --------
    >>> from plantimager.path import line3d
    >>> line3d(0, 0, 0, 10, 10, 10, n_points=5)
    ([0.0, 2.5, 5.0, 7.5, 10.0],
     [0.0, 2.5, 5.0, 7.5, 10.0],
     [0.0, 2.5, 5.0, 7.5, 10.0])

    """
    return line1d(x_start, x_stop, n_points), line1d(y_start, y_stop, n_points), line1d(z_start, z_stop, n_points)


class Line(Path):
    """Creates a linear path for the scanner.

    See Also
    --------
    plantimager.path.line3d

    Examples
    --------
    >>> from plantimager.path import Line
    >>> linear_path = Line(0, 0, 0, 10, 10, 0, 180, 0, n_points=2)
    >>> linear_path
    [x: 0.0, y: 0.0, z: 0.0, pan: 180, tilt: 0, exact_pose: True,
     x: 10.0, y: 10.0, z: 0.0, pan: 180, tilt: 0, exact_pose: True]

    """

    def __init__(self, x_start, y_start, z_start, x_stop, y_stop, z_stop, pan, tilt, n_points):
        """
        Parameters
        ----------
        x_start : length_mm
            Line starting position, in millimeters for the x-axis.
        y_start : length_mm
            Line starting position, in millimeters for the y-axis.
        z_start : length_mm
            Line starting position, in millimeters for the z-axis.
        x_stop : length_mm
            Line ending position, in millimeters for the x-axis.
        y_stop : length_mm
            Line ending position, in millimeters for the y-axis.
        z_stop : length_mm
            Line ending position, in millimeters for the z-axis.
        pan : deg
            Camera pan value, in degrees, to use for the linear path.
        tilt : deg or list(deg)
            Camera tilt(s), in degrees, to use for this circle.
            If an iterable is given, performs more than one camera acquisition at same xyz position.
        n_points : int
            Number of points used to create the linear path.
        """
        super().__init__()
        try:
            assert n_points >= 2
        except AssertionError:
            raise ValueError("You need a minimum of two points to make a line!")

        if not isinstance(tilt, Iterable):
            tilt = [tilt]

        x, y, z = line3d(x_start, y_start, z_start, x_stop, y_stop, z_stop, n_points)
        for i in range(n_points):
            for t in tilt:
                self.append(PathElement(x[i], y[i], z[i], pan, t, exact_pose=True))


class CalibrationPath(Path):
    """Creates a calibration path for the scanner.

    This build two lines spanning the X & Y axes extent of the given path.

    Notes
    -----
    The calibration path is made of the path to calibrate, plus two linear paths, X & Y, in that order.

    Takes the first ``PathElement`` of the input path to calibrate as lines starting points

    Takes the max distance to input path origin along x & y axes to create X & Y lines ending points.
    Let x0, y0 & z0 be the first `ElementPath` xyz position, then:
     - line #1: (x0, y0, z0, max_dist(xi, x0), y0, z0)
     - line #2: (x0, y0, z0, x0, max_dist(yi, y0), z0)

    See Also
    --------
    plant3dvision.tasks.colmap.use_calibrated_poses

    Examples
    --------
    >>> from plantimager.path import CalibrationPath
    >>> from plantimager.path import Circle
    >>> circular_path = Circle(200, 200, 50, 0, 200, 9)
    >>> n_points_line = 5
    >>> calib_path = CalibrationPath(circular_path, n_points_line)
    >>> calib_path
    [x = 0.00, y = 200.00, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 0.00, y = 167.86, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 0.00, y = 135.72, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 0.00, y = 103.58, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 0.00, y = 71.44, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 0.00, y = 200.00, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 11.70, y = 200.00, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 23.40, y = 200.00, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 35.09, y = 200.00, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 46.79, y = 200.00, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 0.00, y = 200.00, z = 50.00, pan = 270.00, tilt = 0.00,
     x = 46.79, y = 71.44, z = 50.00, pan = 310.00, tilt = 0.00,
     x = 165.27, y = 3.04, z = 50.00, pan = 350.00, tilt = 0.00,
     x = 300.00, y = 26.79, z = 50.00, pan = 30.00, tilt = 0.00,
     x = 387.94, y = 131.60, z = 50.00, pan = 70.00, tilt = 0.00,
     x = 387.94, y = 268.40, z = 50.00, pan = 110.00, tilt = 0.00,
     x = 300.00, y = 373.21, z = 50.00, pan = 150.00, tilt = 0.00,
     x = 165.27, y = 396.96, z = 50.00, pan = 190.00, tilt = 0.00,
     x = 46.79, y = 328.56, z = 50.00, pan = 230.00, tilt = 0.00]
    """

    def __init__(self, path, n_points_line):
        """
        Parameters
        ----------
        path : Path
            A path to calibrate.
        n_points_line : int
            The number of points per line.
        """
        super().__init__()
        el0 = path[0]
        # # TODO: find a better "algo" than this to select y-limit for line #1 and x-limit for line #2
        # el1 = path[len(path) // 4 - 1]
        # self.extend(Line(el0.x, el0.y, el0.z, el0.x, el1.y, el0.z, el0.pan, el0.tilt, n_points_line))
        # self.extend(Line(el0.x, el0.y, el0.z, el1.x, el0.y, el0.z, el0.pan, el0.tilt, n_points_line))
        # - Start with the path to calibrate
        self.extend(path)
        # x-axis line, from the first `ElementPath` xyz position to the most distant point from the origin along this x-axis
        x_max = path[np.argmax([pelt.x - el0.x for pelt in path])].x
        # y-axis line, from the first `ElementPath` xyz position to the most distant point from the origin along this y-axis
        y_max = path[np.argmax([pelt.y - el0.y for pelt in path])].y
        self.extend(Line(el0.x, el0.y, el0.z, x_max // 2, el0.y, el0.z, el0.pan, el0.tilt, n_points_line))
        self.extend(Line(el0.x, el0.y, el0.z, el0.x, y_max, el0.z, el0.pan, el0.tilt, n_points_line))
