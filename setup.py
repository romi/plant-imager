import os
from setuptools import setup, find_packages

import lettucethink

ver_file = os.path.join('lettucethink', 'version.py')
with open(ver_file) as f:
    exec(f.read())

# Hack to avoid annoying conda error message
# Package name are `opencv-python` with PIP & `py-opencv` with CONDA
pyopencv = "opencv-python"
conda_build = os.environ.get('CONDA_BUILD', '0') == '1'
if conda_build:
    pyopencv = ""

opts = dict(name='lettucethink-python',
            description="Python tools for the LettuceThink robot",
            long_description="",
            license="",
            platforms=["Linux"],
            version=lettucethink.__version__,
            packages=find_packages(),
            install_requires=[
                "pyserial",
                pyopencv
            ],
            classifiers=[
                "Programming Language :: Python",
                "Intended Audience :: Science/Research",
                "Natural Language :: English",
                "Programming Language :: Python :: 3.7",
                "Topic :: Scientific/Engineering",
            ],
            )

if __name__ == '__main__':
    setup(**opts)
