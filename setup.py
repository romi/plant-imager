#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import find_packages
from setuptools import setup

s = setup(
    name='plantimager',
    version='0.2.1',
    packages=find_packages(),
    scripts=[
        'bin/multi_scan',
        'bin/romi_bpy',
        'bin/romi_virtualplantimager',
        'bin/romi_split_by_material',
        'bin/romi_clean_mesh'
    ],
    author='Timothée Wintz',
    author_email='timothee@timwin.fr',
    description='A plant imager',
    long_description='',
    # use_scm_version=True,
    # setup_requires=['setuptools_scm'],
    setup_requires=[],
    install_requires=[
        'colorlog',
        'numpy',
        'imageio',
        'psutil',
        'requests',
        'pyserial',
        'tqdm'
    ],
    include_package_data=True
)
