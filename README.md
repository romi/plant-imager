# PlantImager & VirtualPlantImager

To be as clear as possible, we first define the following names:
- _PlantImager_: hardware control of the ROMI _3D plant imager_.
- _VirtualPlantImager_: simulate the plant imager using [LPY](https://github.com/fredboudon/lpy) to generate virtual plants and [Blender](https://www.blender.org/) for rendering. **We recommend using it inside a docker container.**

The API documentation of the `plantdb` library can be found here: https://romi.github.io/plant-imager/ 


## Getting started
Clone the repository and initialize the submodules (`plantdb` & `romistask`).
In a terminal:
```shell
# Clone the sources (here get the 'dev_lyon' branch):
git clone https://github.com/romi/plant-imager --branch dev_lyon
# Move to the cloned repository:
cd plant-imager
# Initialize and update the sub-modules:
git submodule init  # only do this ONCE if the sub-module have not yet been initialized!
git submodule update
```

## Docker
Obviously you first have to follow the [getting started](#getting-started) instructions.


### PlantImager docker image

#### Pull a pre-built image
The simplest way to use the docker image is to pull the pre-built `roboticsmicrofarms/plantimager` docker image as follows:
```shell
docker pull roboticsmicrofarms/plantimager:latest
```

#### Build the image
In this repository, you will find a dedicated script, named `build.sh`, in the `docker/plantimager/` directory.

```shell
./docker/plantimager/build.sh
```
By default, this build script will create a docker image named `roboticsmicrofarms/plantimager:latest`.
If you want more build options (specific branches, tags, ...), type `./docker/plantimager/build.sh --help`.

#### Start a container
In the `docker/plantimager/` directory, you will also find a convenience script named `run.sh`.
To get usage information, from the `plant-imager` repository root folder:
```shell
./docker/plantimager/run.sh -h
```

For example, to generate a new _plant scan dataset_, here named `my_scan`, simply do:
```shell
./docker/plantimager/run.sh \
  -c "romi_run_task Scan /myapp/db/my_scan --config plant-imager/config/hardware_scan_rx0.toml"
```

For more information have a look at the ROMI [documentation](https://docs.romi-project.eu/plant_imager/).


### VirtualPlantImager docker image

#### Pull a pre-built image
The simplest way to use the docker image is to pull the pre-built `roboticsmicrofarms/virtualplantimager` docker image as follows:
```shell
docker pull roboticsmicrofarms/virtualplantimager:latest
```

#### Build the image
In this repository, you will find a dedicated script, named `build.sh`, in the `docker/virtualplantimager/` directory.

```shell
./docker/virtualplantimager/build.sh
```
By default, this build script will create a docker image named `roboticsmicrofarms/virtualplantimager:latest`.
If you want more build options (specific branches, tags...), type `./docker/virtualplantimager/build.sh -h`.

#### Start a container
In the `docker/virtualplantimager/` directory, you will also find a convenience script named `run.sh`.
To get usage information, from the `plant-imager` repository root folder:
```shell
./docker/virtualplantimager/run.sh -h
```

For example, to generate a new _virtual plant scan dataset_, named `vplant_test`, simply do:
```shell
./docker/virtualplantimager/run.sh --test
```

For more information have a look at the ROMI [documentation](https://docs.romi-project.eu/plant_imager/).


## Install from sources
To use the _VirtualPlantImager_, we **strongly** recommend using the docker image as installing from the sources may get messy!

However, installing from the sources should go smoothly if you plan to use the _PlantImager_.

### Install from sources to use the _PlantImager_
First follows the instructions [here](#getting-started) to clone the sources, if not done yet.

#### Conda environment creation
Create a conda environment named `plant_imager` and install required dependencies:
```shell
conda create -n plant_imager python=3.10
```

> :information_source: 
> Accepted Python version ranges from 3.8 to 3.11 (included).

#### Install the sources
You may now proceed to install the python requirements and packages:
```shell
conda activate plant_imager # Don't forget to activate the environment!
# Install `plantdb` from sub-modules:
python -m pip install -e ./plantdb/
# Install `romitask` from sub-modules:
python -m pip install -e ./romitask/
# Install `plant-imager`:
python -m pip install -e .
```

> :information_source:
> The `-e` option install the source in _editable_ mode.
> Detailed explanations can be found [here](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).

### Install from sources to use the _VirtualPlantImager_
First follows the instructions [here](#getting-started) to clone the sources, if not done yet.

#### System requirements
```shell
sudo apt-get install libgl1-mesa-dev libxi6 gcc
```

#### Conda environment creation
Create a conda environment named `plant_imager` and install required dependencies listed in `conda/lpy.yaml`:
```shell
conda create -n plant_imager python=3.10
conda env update -n plant_imager --file conda/lpy.yaml
```

> :information_source: 
> Accepted Python version ranges from 3.8 to 3.11 (included).

#### Blender setup
We use Blender's embedded Python interpreter to run a `flask` server to communicate (data and config) and generate images of virtual plants.

We thus have to:
1. download and install Blender;
2. install the `plantimager` library and other packages, like `flask`, for Blender's embedded Python interpreter.

> :information_source:
> For now `2.93.16` is the latest version of Blender we tested our tools against.

##### 1. Download Blender 2.93.16
Download Blender 2.93.16, extract the archive and move its contents to `${BLENDER_PATH}`:
```shell
BLENDER_PATH="/opt/blender"
BLENDER_URL="https://ftp.halifax.rwth-aachen.de/blender/release/Blender2.93/blender-2.93.16-linux-x64.tar.xz"
wget --progress=bar:force:noscroll $BLENDER_URL
tar -xJf blender-2.93.16-linux-x64.tar.xz --directory ${BLENDER_PATH} --strip-components=1  # sudo might be required here!
rm blender-2.93.16-linux-x64.tar.xz
```

To be able to install packages for Blender's embedded Python interpreter, we change the owner of the corresponding directory:
```shell
# Give 'r+w' rights over Blender's embedded Python directory to the non-root user:
chown -R ${USER} ${BLENDER_PATH}/2.93/python/
```

To be able to call the `blender` executable, add the `${BLENDER_PATH}` path to your `$PATH` as follows:
```shell
echo 'export PATH="${BLENDER_PATH}:${PATH}"' >> ~/.bashrc
```

##### 2. Install dependencies
To install dependencies for Blender's embedded Python interpreter, from the `plant-imager` root directory simply do:
```shell
# Don't forget to activate the environment!
conda activate plant_imager
# Use `pip` from current conda environment to install dependencies for Blender's embedded Python interpreter:
python -m pip \
  --python ${BLENDER_PATH}/2.93/python/bin/python3.9 \
  install --no-cache-dir \
  --prefix ${BLENDER_PATH}/2.93/python/ \
  .[virtual]
```

> :information_source:
> Here we use `python` and `pip` from the `plant_imager` conda environment to install dependencies for Blender's embedded Python interpreter thanks to the `--python` flag.
> We also install the packages (`plantimager` and the 'virtual' extra dependencies) to `${BLENDER_PATH}/2.93/python/` with the `--prefix` flag.

#### Install sources
Finally, you can install the sources for `plant-imager`.
From the `plant-imager` root directory, using the `plant_imager` conda environment, it is done as follows:

```shell
# Don't forget to activate the environment!
conda activate plant_imager
# Install `plantdb` from sub-modules:
python -m pip install -e plantdb/
# Install `romitask` from sub-modules:
python -m pip install -e romitask/
# Install `plant-imager`:
python -m pip install -e .
```

> :information_source:
> The `-e` option install the source in _editable_ mode.
> Detailed explanations can be found [here](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).
