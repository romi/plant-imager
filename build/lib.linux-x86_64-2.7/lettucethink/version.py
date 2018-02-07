# Format expected by setup.py and doc/source/conf.py: string of form "X.Y.Z"
_version_major = 0
_version_minor = 1
_version_micro = ''  # use '' for first of series, number for 1 and above
_version_extra = 'dev'
# _version_extra = ''  # Uncomment this for full releases

# Construct full version string from these.
_ver = [_version_major, _version_minor]
if _version_micro:
    _ver.append(_version_micro)
if _version_extra:
    _ver.append(_version_extra)

__version__ = '.'.join(map(str, _ver))

CLASSIFIERS = ["Operating System :: OS Independent",
               "Programming Language :: Python",
               "Topic :: Scientific/Engineering"]

# Description should be a one-liner:
description = "lettucethink: controllers and tools for agribots "

# Long description will go up on the pypi page
long_description = """
lettucethink
=================

`lettucethink` is a Python module, it gathers low-level control the LettuceThink robot and tools for the related applications.

# LettuceScan

In the LettuceScan application, the useful functions are controlling:

- the RGBD camera,
- the CNC for the xyz motion of the arn,
- the bracket for pan and tilt motion.
Please read the repository README_ on Github or our documentation
"""

NAME = "lettucethink"
DESCRIPTION = description
LONG_DESCRIPTION = long_description
LICENSE = "L-GPL-3"
PLATFORMS = "OS Independent"
MAJOR = _version_major
MINOR = _version_minor
MICRO = _version_micro
VERSION = __version__
