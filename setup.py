import os
from setuptools import setup, find_packages

ver_file = os.path.join('lettucethink', 'version.py')
with open(ver_file) as f:
    exec(f.read())

# Hack to avoid annoying conda error message
# Package name are `opencv-python` with PIP & `py-opencv` with CONDA
pyopencv = "opencv-python"
conda_build = os.environ.get('CONDA_BUILD', '0') == '1'
if conda_build:
    pyopencv = ""

opts = dict(name=NAME,
            description=DESCRIPTION,
            long_description=LONG_DESCRIPTION,
            license=LICENSE,
            classifiers=CLASSIFIERS,
            platforms=PLATFORMS,
            version=VERSION,
            packages=find_packages(),
            install_requires=[
                "pyserial",
                pyopencv
            ],
            )

if __name__ == '__main__':
    setup(**opts)
