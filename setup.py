import subprocess
import romiscanner

from shutil import copyfile
from setuptools import setup, Extension, find_packages

s = setup(
    name='romiscanner',
    packages=find_packages(),
    scripts=['bin/romi_bpy', 'bin/romi_virtualscanner', 'bin/romi_split_by_material', 'bin/romi_clean_mesh'],
    author='Timothée Wintz',
    author_email='timothee@timwin.fr',
    description='A plant scanner',
    long_description='',
    zip_safe=False,
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    install_requires=[
        'numpy',
        'imageio',
        'psutil'
    ],
    include_package_data=True,
)
