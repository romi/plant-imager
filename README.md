# Plant Imager & Virtual Plant Imager

To be as clear as possible, we first define the following names:
- _Plant Imager_: hardware control of the ROMI _3D plant imager_.
- _Virtual Plant Imager_: simulate the plant imager using [LPY](https://github.com/fredboudon/lpy) to generate virtual plants and [Blender](https://www.blender.org/) for rendering. **We recommend using it inside a docker container.**


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
For now, you have to first build the image locally, then you can use it.
> :warning: We will change that soon, so you can use pre-built images!

Obviously you first have to follow the [getting started](#getting-started) instructions.


### Using the `plantimager` docker image

#### Build the `plantimager` image
In this repository, you will find a dedicated script, named `build.sh`, in the `docker/plantimager/` directory.

You may need to update the submodules before building the image.
In a terminal move to the root of the cloned `plant-imager` repository and update the submodules with:
```shell
git submodule update
```

Now you can use the provided build script.
```shell
./docker/plantimager/build.sh
```
By default, this build script will create a docker image named `plantimager:latest`.
If you want more build options (specific branches, tags...etc), type `./docker/plantimager/build.sh --help`.

> :warning: by default the docker user is the same as the one currently used by your system. Use `echo $USER` to check the active username.


#### Run a `plantimager` container
In the `docker/plantimager/` directory, you will also find a convenience script named `run.sh`.
To get usage information and options list, use `./run.sh -h` or from the `plant-imager` repository root folder:
```shell
./docker/plantimager/run.sh -h
```

#### Example: plant acquisitions
To generate a new plant dataset, here named `test2`, we have to:
- mount the local (host) database to the docker container with the `-db` option
- provide the ROMI command to start a `Scan` task
```shell
./docker/plantimager/run.sh -db /home/${USER}/romi_db/\
  -c "romi_run_task Scan /home/${USER}/db/test_2 --config /home/${USER}/plant-imager/config/hardware_scan_rx0.toml"
```

### Using the `virtualplantimager` docker image

#### Build the `virtualplantimager` image
In this repository, you will find a dedicated script, named `build.sh`, in the `docker/virtualplantimager/` directory.

You may need to update the submodules before building the image.
In a terminal move to the root of the cloned `plant-imager` repository and update the submodules with:
```shell
git submodule update
```

Now you can use the provided build script.
```shell
./docker/virtualplantimager/build.sh
```
By default, this build script will create a docker image named `virtualplantimager:latest`.
If you want more build options (specific branches, tags...etc), type `./docker/virtualplantimager/build.sh -h`.

> :warning: by default the docker user is the same as the one currently used by your system.
> Use `echo $USER` to check the active username.


#### Run a `virtualplantimager` container
In the `docker/virtualplantimager/` directory, you will also find a convenience script named `run.sh`.
To get usage information and options list, use `./run.sh -h` or from the `plant-imager` repository root folder:
```shell
./docker/virtualplantimager/run.sh -h
```

#### Example: generating a virtual plant dataset with lpy and Blender

##### Create a temporary copy of the example database
To avoid generating the dataset in the git repository, we highly recommend to first copy the example database to a temporary folder.
On UNIX systems, from the `plant-imager/` root directory, do:
```shell
cd plant-imager
cp -r database_example /tmp/
```

You can check the temporary copy with:
```shell
ls /tmp/database_example
```

##### Generate a virtual data
Following the temporary copy, to generate a virtual _Arabidopsis thaliana_ named `generated_dataset`, do:
```shell
cd plant-imager
./docker/virtualplantimager/run.sh \
  -t latest -db /tmp/database_example \
  -c "romi_run_task VirtualScan db/generated_dataset \
        --config plant-imager/config/vscan_lpy_blender.toml"
```
This will use a standard configuration for the `VirtualScan` task defined in `plant-imager/config/vscan_lpy_blender.toml`.
After a while, if the generation has succeeded, you can check the generated dataset on your mapped host machine directory `/tmp/database_example/generated_dataset`

> :warning: stopping or restarting your system will clean the `/tmp` directory.

> :information_source: If you have an error about a locked database: `rm /tmp/generated_dataset/lock` and try again! 

For more information have a look at the official ROMI documentation [website](https://docs.romi-project.eu/plant_imager/).


## Install from sources
To use the _Virtual Plant Imager_, we **strongly** recommend using the docker image as installing from the sources can get messy!

However, installing from the sources should go smoothly if you plan to use the _Plant Imager_. 

### Getting started
If you have not done it yet, start by cloning the sources and getting the submodules (`plantdb` & `romistask`).
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
> :information_source: Note that we use the `git submodules` to clone `romitask` and `plantdb`.

### Install from sources to use the _plant imager_

#### Conda environment creation
Create a conda environment named `plant_imager` and install required dependencies:
```shell
conda create -n plant_imager python=3.9
```

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

### Install from sources to use the _virtual plant imager_

#### System requirements
```shell
sudo apt-get install libgl1-mesa-dev libxi6 gcc
```

#### Conda environment creation
Create a conda environment named `plant_imager` and install required dependencies listed in `conda/lpy.yaml`:
```shell
conda create -n plant_imager python=3.9
conda env update -n plant_imager --file conda/lpy.yaml
```

#### Blender setup
In order to use the `bpy` module we have to do this mess:

##### 1. Download Blender 2.93.16
Download Blender 2.93.16, extract the archive and move its contents to `/opt/blender`:
```shell
BLENDER_URL="https://ftp.halifax.rwth-aachen.de/blender/release/Blender2.93/blender-2.93.16-linux-x64.tar.xz"
wget --progress=bar $BLENDER_URL
tar -xJf blender-2.93.16-linux-x64.tar.xz
mv blender-2.93.16-linux-x64 /opt/blender  # sudo might be required here!
rm blender-2.93.16-linux-x64.tar.xz
```

> :information_source: For now 2.93.16 is the latest version of blender we tested our tools against.

To be able to call the `blender` executable, add the `/opt/blender` path to your `$PATH` as follows:
```shell
echo 'export PATH="/opt/blender:${PATH}"' >> ~/.bashrc
```

##### 2. Install dependencies
To install dependencies for Blender's embedded Python interpreter, simply do:
```shell
/opt/blender/2.93/python/bin/python3.9 -m ensurepip
/opt/blender/2.93/python/bin/python3.9 -m pip install -e ./romitask/
/opt/blender/2.93/python/bin/python3.9 -m pip install -e .[virtual]
```

#### Install sources
Finally, you can install the sources for `plant-imager`.
From the `plant-imager` root directory, using the `plant_imager` conda environment, it is done as follows:

```shell
# Don't forget to activate the environment!
conda activate plant_imager
# Install `plantdb` from sub-modules:
python -m pip install -e ./plantdb/
# Install `romitask` from sub-modules:
python -m pip install -e ./romitask/
# Install `plant-imager`:
python -m pip install -e .
```

> :information_source: The `-e` option install the source in _editable_ mode.
> Detailed explanations can be found [here](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).
