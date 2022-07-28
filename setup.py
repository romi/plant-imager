import subprocess
import plantimager

from shutil import copyfile
from setuptools import setup, Extension, find_packages

s = setup(
    name='plantimager',
    packages=find_packages(),
    version='0.12',
    scripts=[
        'bin/romi_bpy',
        'bin/romi_virtualplantimager',
        'bin/romi_split_by_material',
        'bin/romi_clean_mesh'
    ],
    author='Timothée Wintz',
    author_email='timothee@timwin.fr',
    description='A plant imager',
    long_description='',
    zip_safe=False,
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    install_requires=[
        'colorlog',
        'numpy',
        'imageio',
        'psutil',
        'requests',
        'pyserial'
    ],
    include_package_data=True
)
