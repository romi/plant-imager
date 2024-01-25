#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import find_packages
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

opts = dict(
    name='plantimager',
    version='0.2.1',
    description='ROMI library to control the PlantImager (hardware) or the VirtualPlantImager (Blender) to acquire images of (virtual) single potted plants.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Timothée Wintz',
    author_email='timothee@timwin.fr',
    maintainer='Jonathan Legrand',
    maintainer_email='jonathan.legrand@ens-lyon.fr',
    url="https://docs.romi-project.eu/plant_imager/",
    download_url='',
    packages=find_packages(),
    include_package_data=True,
    scripts=[
        'bin/multi_scan',
        'bin/romi_bpy',
        'bin/romi_virtualplantimager',
        'bin/romi_split_by_material',
        'bin/romi_clean_mesh'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)"
    ],
    license="LGPL-3.0",
    license_files='LICENSE.txt',
    keywords=['ROMI', 'skeletonization', 'CGAL'],
    platforms=['linux'],
    zip_safe=False,
    python_requires='==3.9.2',
    setup_requires=[],
    install_requires=[
        'colorlog',
        'imageio',
        'numpy',
        'psutil',
        'requests',
        'pyserial',
        'tqdm',
    ],
)

if __name__ == '__main__':
    setup(**opts)
