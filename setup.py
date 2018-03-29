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
