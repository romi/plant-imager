"""

    lettucethink-python - Python tools for the LettuceThink robot

    Copyright (C) 2018 Sony Computer Science Laboratories
    Authors: D. Colliaux, T. Wintz, P. Hanappe
  
    This file is part of lettucethink-python.

    lettucethink-python is free software: you can redistribute it
    and/or modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.

    lettucethink-python is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with lettucethink-python.  If not, see
    <https://www.gnu.org/licenses/>.

"""    
from setuptools import setup, find_packages
import os

ver_file = os.path.join('lettucethink', 'version.py')
with open(ver_file) as f:
    exec(f.read())


opts = dict(name=NAME,
            description=DESCRIPTION,
            long_description=LONG_DESCRIPTION,
            license=LICENSE,
            classifiers=CLASSIFIERS,
            platforms=PLATFORMS,
            version=VERSION,
            packages=find_packages(),

            install_requires=[
                'imageio',
                'gphoto2'
                ],
            )

if __name__ == '__main__':
    setup(**opts)
