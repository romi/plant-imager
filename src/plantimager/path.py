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

    This class is meant to encapsulate a 3D point using Cartesian coordinates
    (x, y, z) along with additional properties for orientation (pan and tilt).

    Attributes
    ----------
    x : float, optional
        The x-coordinate in 3D space. Initialized in the parent class.
    y : float, optional
        The y-coordinate in 3D space. Initialized in the parent class.
    z : float, optional
        The z-coordinate in 3D space. Initialized in the parent class.
    pan : float, optional
        Angular orientation around the vertical axis, in degrees.
        Defaults to ``None``.
    tilt : float, optional
        Angular orientation around the horizontal axis, in degrees.
        Defaults to ``None``.

    Examples
    --------
    >>> from plantimager.path import Pose
    >>> p = Pose(50, 250, 80, 270, 0)
    >>> print(p)
    x: 50, y: 250, z: 80, pan: 270, tilt: 0

    """

    def __init__(self, x=None, y=None, z=None, pan=None, tilt=None):
        """Represents a 3D point in space along with pan and tilt angles.

        Parameters
        ----------
        x : float, optional
            The x-coordinate (in millimeters) of the 3D point. Defaults to ``None``.
        y : float, optional
            The y-coordinate (in millimeters) of the 3D point. Defaults to ``None``.
        z : float, optional
            The z-coordinate (in millimeters) of the 3D point. Defaults to ``None``.
        pan : float, optional
            The pan angle (in degrees), _i.e._ horizontal rotation, associated with the point.
            Defaults to ``None``.
        tilt : float, optional
            The tilt angle (in degrees), _i.e._ vertical rotation, associated with the point.
            Defaults to ``None``.
        """
        self.x = x
        self.y = y
        self.z = z
        self.pan = pan
        self.tilt = tilt

    def __repr__(self):
        return ", ".join(f"{k}: {v}" for k, v in self.__dict__.items())

    def attributes(self):
        """Returns a list of attribute names related to the object's position and orientation.

        Returns
        -------
        list of str
            A list containing the names of the attributes: "x", "y", "z", "pan", and "tilt".
        """
        return ["x", "y", "z", "pan", "tilt"]


class PathElement(Pose):
    """Singleton for a `Path` class.

    This class extends the basic coordinates of x, y, z with additional
    parameters for orientation (pan, tilt) and a boolean flag to specify
    if the pose must be treated as exact.

    Attributes
    ----------
    x : float, optional
        The x-coordinate in 3D space. Initialized in the parent class.
    y : float, optional
        The y-coordinate in 3D space. Initialized in the parent class.
    z : float, optional
        The z-coordinate in 3D space. Initialized in the parent class.
    pan : float, optional
        Angular orientation around the vertical axis, in degrees.
        Defaults to ``None``.
    tilt : float, optional
        Angular orientation around the horizontal axis, in degrees.
        Defaults to ``None``.
    exact_pose : bool, optional
        Specifies whether the pose represents an exact location and
        orientation. Defaults to ``True``.

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
        """Represents a 3D pose with pan and tilt angles, as well as an
        indicator for whether the pose is an exact reference or not.

        Parameters
        ----------
        x : float, optional
            The x-coordinate in 3D space. Defaults to None.
        y : float, optional
            The y-coordinate in 3D space. Defaults to None.
        z : float, optional
            The z-coordinate in 3D space. Defaults to None.
        pan : float, optional
            Angular orientation around the vertical axis, in degrees.
            Defaults to None.
        tilt : float, optional
            Angular orientation around the horizontal axis, in degrees.
            Defaults to None.
        exact_pose : bool, optional
            Specifies if this pose is treated as exact. Defaults to True.

        """
        super().__init__(x, y, z, pan, tilt)
        self.exact_pose = exact_pose

    def __repr__(self):
        return ", ".join(f"{k}: {v}" for k, v in self.__dict__.items())


class Path(list):
    """A path is an abstract class that should be a list of ``PathElement`` instances."""

    def __init__(self):
        super().__init__()


def _round(x, dec=2):
    import numpy as np
    return list(map(float, np.round(x, decimals=dec)))


def circle(center_x, center_y, radius, n_points, offset_angle=0, clockwise=True):
    """Generates the 2D coordinates and angles for points evenly distributed on a circle, facing the central point.

    This function computes the x and y coordinates of `n_points` evenly distributed
    on the circumference of a circle centered at (`center_x`, `center_y`) with a
    specified `radius`. Additionally, the function calculates the angle (in degrees)
    for each point with respect to the vertical axis, optionally offset by an
    `offset_angle`.

    Parameters
    ----------
    center_x : float
        The x-coordinate of the circle's center.
    center_y : float
        The y-coordinate of the circle's center.
    radius : float
        The radius of the circle.
    n_points : int
        The number of points to generate along the circle's circumference.
    offset_angle : float, optional
        The angle offset in degrees for the start of the point distribution. Defaults to 0.
    clockwise : bool, optional
        Boolean flag controlling the rotation direction.
        ``True`` for clockwise rotation, ``False`` for counter-clockwise.

    Returns
    -------
    list of float
        A list of x-coordinates for the points on the circle.
    list of float
        A list of y-coordinates for the points on the circle.
    list of float
        A list of corresponding angles (in degrees, measured clockwise) for the points
        with respect to the vertical axis.

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
    dir = 1 if clockwise else -1
    # Convert starting_angle to radians for computation
    start_rad = math.radians(offset_angle)

    for i in range(n_points):
        rad = 2 * i * math.pi / n_points + start_rad
        x.append(center_x + dir * radius * math.cos(rad))
        y.append(center_y + dir * radius * math.sin(rad))
        deg = math.degrees(rad)
        p.append(deg % 360)

    return _round(x), _round(y), _round(p)


class Circle(Path):
    """A 2D circular path in the XY plane for the scanner, with the camera facing the center of the circle.

    Notes
    -----
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

    def __init__(self, center_x, center_y, z, tilt, radius, n_points, start_offset=0, clockwwise=True):
        """Initializes an object by generating a circular arrangement of points in 3D space.

        Each path element is defined by the combination of the 2D circle
        coordinates, a fixed z-value, and specified tilt angles. This results
        in path elements with varying tilt angles, forming a complete circular
        motion in 3D space.

        Parameters
        ----------
        center_x : float
            The x-coordinate (in millimeters) of the center of the circle.
        center_y : float
            The y-coordinate (in millimeters) of the center of the circle.
        z : float
            The fixed z-coordinate (in millimeters) for all points along the circle.
        tilt : Union[float, Iterable[float]]
            One or more tilt angles (in degrees) to apply at each point.
        radius : float
            The radius (in millimeters) of the circle.
        n_points : int
            The number of points to generate around the circle.
        start_offset : float, optional
            The angular offset (in degrees) to shift the starting position
            along the circle. Measured counter-clockwise from the positive x-axis.
        clockwise : bool, optional
            Boolean flag controlling the rotation direction.
            ``True`` for clockwise rotation, ``False`` for counter-clockwise.
        """
        super().__init__()
        x, y, pan = circle(center_x, center_y, radius, n_points, start_offset, clockwwise)

        if not isinstance(tilt, Iterable):
            tilt = [tilt]

        for i in range(n_points):
            for t in tilt:
                self.append(PathElement(x[i], y[i], z, pan[i], t))


class Cylinder(Path):
    """A cylinder-like path for the scanner as multiple circles, with the camera facing the center of the circle.

    Makes as much circular paths as `n_circles` within the given z-range.

    Notes
    -----
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
    >>> cylinder_path = Cylinder(200, 200, (0, 50), 0, 200, n_points=2, n_circles=2, aligned=False)
    >>> cylinder_path
    >>> cylinder_path = Cylinder(200, 200, (0, 50), 0, 200, n_points=2, n_circles=3)
    >>> cylinder_path
    [x: 0.0, y: 200.0, z: 0.0, pan: 270.0, tilt: 0, exact_pose: False,
     x: 400.0, y: 199.99999999999997, z: 0.0, pan: 90.0, tilt: 0, exact_pose: False,
     x: 0.0, y: 200.0, z: 25.0, pan: 270.0, tilt: 0, exact_pose: False,
     x: 400.0, y: 199.99999999999997, z: 25.0, pan: 90.0, tilt: 0, exact_pose: False,
     x: 0.0, y: 200.0, z: 50.0, pan: 270.0, tilt: 0, exact_pose: False,
     x: 400.0, y: 199.99999999999997, z: 50.0, pan: 90.0, tilt: 0, exact_pose: False]

    """

    def __init__(self, center_x, center_y, z_range, tilt, radius, n_points, clockwwise=True, n_circles=2, aligned=True):
        """Initialization of a cylinder-like structure composed of multiple circles at different heights within a z-range.

        This class constructor generates `n_circles` at varying heights within a
        given z-range and aligns the circular points optionally.

        Parameters
        ----------
        center_x : float
            The x-coordinate (in millimeters) of the center of each circle comprising the cylinder.
        center_y : float
            The y-coordinate (in millimeters) of the center of each circle comprising the cylinder.
        z_range : tuple of float
            A Pair of values indicating the minimum and maximum z-coordinates (in millimeters)
            for the cylindrical structure.
        tilt : float
            The tilt angle of each circle in degrees relative to its parallel
            orientation to the XY-plane.
        radius : float
            The radius (in millimeters) of each circle forming the cylinder.
        n_points : int
            The number of evenly spaced points that define each circle.
        clockwise : bool, optional
            Boolean flag controlling the rotation direction.
            ``True`` for clockwise rotation, ``False`` for counter-clockwise.
        n_circles : int, optional
            The total number of circles that make up the cylindrical structure.
            Defaults to 2.
        aligned : bool, optional
            If True, aligns the start points of all circles. Otherwise, offsets
            start points progressively based on the number of circles. Defaults to True.

        Raises
        ------
        ValueError
            If `n_circles` is less than 2 because at least two circles
            are required to form a cylinder-like structure.
        """
        # Call the parent class (Path) initializer
        super().__init__()

        # Ensure `n_circles` is at least 2, as a minimum of two circles is required to form a cylinder
        try:
            assert n_circles >= 2
        except AssertionError:
            raise ValueError("You need a minimum of two circles to make a cylinder!")

        # Compute the angle (in degrees) between successive points on a single circle
        step_angle = 360 / n_points

        # Determine the phase offset between the starting point of circles,
        # differentiating aligned from offset configurations
        start_offset = 0 if aligned else step_angle / n_circles

        # Extract the minimum and maximum z-values (heights) for the cylinder
        min_z, max_z = z_range
        # Calculate and iterate over `n_circles` evenly spaced heights in the z-range
        for circle_idx, z_circle in enumerate(np.arange(min_z, max_z + 1, (max_z - min_z) / float(n_circles - 1))):
            # For each height, create a 2D circular path (Circle) and offset it if required
            self.extend(Circle(center_x, center_y, z_circle, tilt, radius, n_points,
                               start_offset * circle_idx, clockwwise))


def line_1d(start, stop, n_points):
    """Generates a 1D linearly spaced sequence of values between `start` and `stop`, inclusive.

    The returned sequence contains `n_points` values equally spaced between these boundary values.

    Parameters
    ----------
    start : float or int
        The starting coordinate of the sequence.
    stop : float or int
        The ending coordinate of the sequence.
    n_points : int
        The number of values to generate in the sequence. Must be greater than or equal to 2.

    Returns
    -------
    list of float
        A list containing `n_points` equally spaced values from `start` to `stop`, inclusive.

    Examples
    --------
    >>> from plantimager.path import line_1d
    >>> line_1d(0,10,n_points=5)
    [0.0, 2.5, 5.0, 7.5, 10.0]
    """
    return [(1 - i / (n_points - 1)) * start + (i / (n_points - 1)) * stop for i in range(n_points)]


def line_3d(x_start, y_start, z_start, x_stop, y_stop, z_stop, n_points):
    """Generates coordinates of a 3D line given start and stop points and the number of intermediate points.

    This function computes the coordinates of a 3D line by generating intermediate
    linearly spaced points between the given start and stop points along the x, y, and z dimensions.

    Parameters
    ----------
    x_start : float
        The starting coordinate of the line on the x-axis.
    y_start : float
        The starting coordinate of the line on the y-axis.
    z_start : float
        The starting coordinate of the line on the z-axis.
    x_stop : float
        The ending coordinate of the line on the x-axis.
    y_stop : float
        The ending coordinate of the line on the y-axis.
    z_stop : float
        The ending coordinate of the line on the z-axis.
    n_points : int
        The number of points to generate along each line segment, including the start
        and stop points.

    Returns
    -------
    tuple of numpy.ndarray
        A tuple containing the x, y, and z coordinates of the generated 3D line.
        Each element of the tuple is a len-3 list of size `n_points` with linearly
        spaced values between the respective start and stop coordinates.

    Examples
    --------
    >>> from plantimager.path import line_3d
    >>> line_3d(0, 0, 0, 10, 10, 10, n_points=5)
    ([0.0, 2.5, 5.0, 7.5, 10.0],
     [0.0, 2.5, 5.0, 7.5, 10.0],
     [0.0, 2.5, 5.0, 7.5, 10.0])
    """
    return line_1d(x_start, x_stop, n_points), line_1d(y_start, y_stop, n_points), line_1d(z_start, z_stop, n_points)


class Line(Path):
    """A 3D linear path with specified start and stop positions, camera parameters, and number of points along the path.

    Notes
    -----
    If an iterable is given for `tilt`, performs more than one camera acquisition at same xyz position.

    Examples
    --------
    >>> from plantimager.path import Line
    >>> linear_path = Line(0, 0, 0, 10, 10, 0, 180, 0, n_points=2)
    >>> linear_path
    [x: 0.0, y: 0.0, z: 0.0, pan: 180, tilt: 0, exact_pose: True,
     x: 10.0, y: 10.0, z: 0.0, pan: 180, tilt: 0, exact_pose: True]

    """

    def __init__(self, x_start, y_start, z_start, x_stop, y_stop, z_stop, pan, tilt, n_points):
        """Initializes an object by generating a linear arrangement of points in 3D space.

        This class generates a linear sequence of points in 3D space, with each point
        associated with specific camera pan and tilt values.
        It can also accommodate multiple camera acquisitions at the same 3D position
        if multiple tilt values are provided.

        Parameters
        ----------
        x_start : float
            The starting x-coordinate (in millimeters) of the 3D line path.
        y_start : float
            The starting y-coordinate (in millimeters) of the 3D line path.
        z_start : float
            The starting z-coordinate (in millimeters) of the 3D line path.
        x_stop : float
            The ending x-coordinate (in millimeters) of the 3D line path.
        y_stop : float
            The ending y-coordinate (in millimeters) of the 3D line path.
        z_stop : float
            The ending z-coordinate (in millimeters) of the 3D line path.
        pan : float
            The pan angle (in degrees) for all path elements.
        tilt : float or Iterable[float]
            The tilt angle(s) (in degrees) to be applied at each point of the path.
            If a single float is provided, it will be used for all path elements.
            If an iterable is provided, each tilt value will be used in conjunction with the generated points.
        n_points : int
            The number of points to generate along the 3D line path. Must be greater than or equal to 2.

        Raises
        ------
        ValueError
            If `n_points` is less than 2, as at least two points are required to define a line.
        TypeError
            If `tilt` is not an iterable, nor a single float.
        """
        super().__init__()
        try:
            assert n_points >= 2
        except AssertionError:
            raise ValueError("You need a minimum of two points to make a line!")

        if not isinstance(tilt, Iterable):
            tilt = [tilt]

        x, y, z = line_3d(x_start, y_start, z_start, x_stop, y_stop, z_stop, n_points)
        for i in range(n_points):
            for t in tilt:
                self.append(PathElement(x[i], y[i], z[i], pan, t, exact_pose=False))


class CalibrationPath(Path):
    """Creates a calibration path for the Plant Imager.

    Notes
    -----
    The calibration path is made of the path to calibrate, plus four linear paths:
      1. a "y-line" (from `y_min` to `y_max`) at `x_min`, facing `x_max` with `n_points_line` poses
      2. a first "half x-line" (from `x_min` to `x_max/2`) at `y_max/2`, facing `x_max` with `n_points_line/2` poses
      3. a second "half x-line" (from `x_max/2` to `x_max`) at `y_max/2`, facing `x_min` with `n_points_line/2` poses
      4. a "y-line" (from `y_min` to `y_max`) at `x_max`, facing `x_min` with `n_points_line` poses
    The central and extreme points of the "x-line" at `y_max/2` are removed to avoid duplicates.

    See Also
    --------
    plantimager.tasks.colmap.use_calibrated_poses

    Examples
    --------
    >>> from plantimager.path import CalibrationPath
    >>> from plantimager.path import Circle
    >>> n_points_circle = 36
    >>> circular_path = Circle(300, 300, 50, 0, 250, n_points_circle)
    >>> n_points_line = 11
    >>> calib_path = CalibrationPath(circular_path, n_points_line, x_lims=[0, 600], y_lims=[0, 600])
    >>> calib_path[36:]  # the calibration lines
    >>> len(calib_path) == n_points_circle + n_points_line*3
    >>> # View the Calibration points coordinates:
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> x,y = np.array([(p.x, p.y) for p in calib_path]).T  # get the XY coordinates
    >>> fig, ax = plt.subplots(figsize=(8,8))
    >>> ax.scatter(x[:36], y[:36], marker='+', color=['r']*n_points_circle, label="Circle")
    >>> ax.scatter(x[36:], y[36:], marker='x', color=['b']*(n_points_line*3-3), label="Lines")
    >>> [ax.text(x[i], y[i], str(i)) for i in range(len(x))]
    >>> ax.grid(True, which='major', axis='both', linestyle='dotted')
    >>> ax.set_aspect('equal')
    >>> ax.legend()
    >>> ax.set_title("Calibration path")
    >>> ax.set_xlabel("X-axis")
    >>> ax.set_ylabel("Y-axis")

    """

    def __init__(self, path, n_points_line=11, x_lims=None, y_lims=None):
        """
        Parameters
        ----------
        path : Path
            A path to calibrate.
        n_points_line : int, optional
            The number of points per line, should be an odd number (or we will add one point).
            Defaults to `11` and should be greater or equal to `5`.
        x_lims : list of int, optional
            Set the min/max `x` range for the calibration (do NOT apply to the path to calibrate).
            Else, will be set from the min/max of the path to calibrate on the x-axis.
        y_lims : list of int, optional
            Set the min/max `y` range for the calibration (do NOT apply to the path to calibrate).
            Else, will be set from the min/max of the path to calibrate on the y-axis.
        """
        super().__init__()
        # Check the `n_points_line` parameter:
        try:
            assert n_points_line >= 5
        except:
            raise ValueError(f"CalibrationPath require a number of point per line >= `5`, got {n_points_line}!")

        # - Start the calibration path with the path to calibrate:
        self.extend(path)

        p0 = path[0]  # get the first pose
        # Compute the X & Y range for calibration lines:
        if x_lims is None:
            x_coords = [pelt.x for pelt in path]
            x_min, x_max = min(x_coords), max(x_coords)
            # x_min = path[np.argmin([p_i.x - p0.x for p_i in path])].x
            # x_max = path[np.argmax([p_i.x - p0.x for p_i in path])].x
        else:
            x_min, x_max = x_lims
        if y_lims is None:
            y_coords = [pelt.y for pelt in path]
            y_min, y_max = min(y_coords), max(y_coords)
            # y_min = path[np.argmin([p_i.y - p0.y for p_i in path])].y
            # y_max = path[np.argmax([p_i.y - p0.y for p_i in path])].y
        else:
            y_min, y_max = y_lims

        # Get the middle coordinates in X & Y:
        mid_x = (x_max - x_min) // 2. + x_min
        mid_y = (y_max - y_min) // 2. + y_min
        # Make sure the number of point per line is an odd number:
        if n_points_line % 2 == 0:
            n_points_line += 1
        # Get the number of point to make a "half line":
        n_points_half_line = n_points_line // 2 + 1

        # Add the first Y-line at x-min, facing the x-max:
        self.extend(Line(x_min, y_min, p0.z, x_min, y_max, p0.z, 270., p0.tilt, n_points_line))
        # Add the first half X-line facing the x-max:
        #  - remove the first pose as it has been done during the first Y-line at x-min
        #  - remove the last pose as it would be at the center (and we want to exclude a central point)
        self.extend(Line(x_min, mid_y, p0.z, mid_x, mid_y, p0.z, 270., p0.tilt, n_points_half_line)[1:-1])
        # Add the second half X-line facing the x-min:
        #  - remove the first pose as it would be at the center (and we want to exclude a central point)
        #  - remove the last pose as it will be done during the second Y-line at x-max
        self.extend(Line(mid_x, mid_y, p0.z, x_max, mid_y, p0.z, 90., p0.tilt, n_points_half_line)[1:-1])
        # Add the second Y-line at x-max, facing the x-min:
        self.extend(Line(x_max, y_min, p0.z, x_max, y_max, p0.z, 90., p0.tilt, n_points_line))
        # TODO: search for line points to close to circle points & remove them according to a distance threshold?
