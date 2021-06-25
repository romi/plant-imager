# -Virtual- Plant Imager

To be as clear as possible, we define the following names:
- _Plant Imager_: hardware control of the ROMI _3D plant imager_.
- _Virtual Plant Imager_: simulate the plant imager using [LPY](https://github.com/fredboudon/lpy) to generate virtual plants and [Blender](https://www.blender.org/) for rendering. **We recommend using it inside a docker container.**


## Getting started
Clone the repository and initialize the sub-modules.
In a terminal:
```shell
git clone https://github.com/romi/plant-imager.git
cd plant-imager/
git submodule init  # only do this ONCE if the sub-module have not yet been initialized!
```

## Docker
For now, you have to first build the image locally, then you can use it.
> :warning: We will change that soon, so you can use pre-built images!

Obviously you first have to follow the [getting started](https://github.com/romi/plant-imager#getting-started) instructions.


### Using the `plantimager` docker image

#### Build the `plantimager` image
In this repository, you will find a dedicated script, named `build.sh`, in the `docker/plantimager/` directory.

You may need to update the sub-modules before building the image.
In a terminal move to the root of the cloned `plant-imager` repository and update the sub-modules with:
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
./docker/plantimager/run.sh -db /home/remisans/romi_db/\
  -c "romi_run_task Scan /home/remisans/db/test_2 --config /home/remisans/plant-imager/config/hardware_scan_rx0.toml"
```

### Using the `virtualplantimager` docker image

#### Build the `virtualplantimager` image
In this repository, you will find a dedicated script, named `build.sh`, in the `docker/virtualplantimager/` directory.

You may need to update the sub-modules before building the image.
In a terminal move to the root of the cloned `plant-imager` repository and update the sub-modules with:
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

For more information have a look at the official ROMI documentation [website](https://docs.romi-project.eu/Scanner/).


## Install from sources
We **highly** recommend using the docker image for the _virtual plant imager_ as installing things can get messy!

### Getting started
Start by cloning the sources and getting the sub-modules:
```shell
# Clone plant-imager sources
git clone https://github.com/romi/plant-imager
cd plant-imager
# Get the sub-modules:
git submodule init  # only do this ONCE if the sub-module have not yet been initialized!
git submodule update
```

### Install from sources to use the _plant imager_

#### Conda environment creation
Create a conda environment named `plant_imager` and install required dependencies:
```shell
conda create -n plant_imager python=3.7
```

#### Install the sources
You may now proceed to install the python requirements and packages:
```shell
# Don't forget to activate the environment!
conda activate plant_imager
cd plant-imager
# Install `plantdb` from sub-modules:
python -m pip install -e ./plantdb/
# Install `romitask` from sub-modules:
python -m pip install -e ./romitask/
# Install `plant-imager`:
python -m pip install -e .
```
> :information_source: Please notice that we here use the git sub-modules to clone and install `romitask` and `plantdb`.

### Install from sources to use the _virtual plant imager_

#### System requirements
```shell
sudo apt-get install libgl1-mesa-dev libxi6 gcc
```

#### Conda environment creation
Create a conda environment named `plant_imager` and install required dependencies:
```shell
conda create -n plant_imager python=3.7
conda install -n plant_imager -c conda-forge -c fredboudon flask imageio toml luigi boost=1.70.0 qhull=2015.2 openalea.lpy
```

#### Blender setup
In order to use the `bpy` module we have to do this mess:

##### 1. Download Blender2.81
Download Blender2.81, extract the archive and move its contents to `/opt/blender`:
```shell
BLENDER_URL=https://download.blender.org/release/Blender2.81/blender-2.81a-linux-glibc217-x86_64.tar.bz2
wget --progress=bar $BLENDER_URL
tar -xjf blender-2.81a-linux-glibc217-x86_64.tar.bz2
sudo mv blender-2.81a-linux-glibc217-x86_64 /opt/blender
rm blender-2.81a-linux-glibc217-x86_64.tar.bz2
```

Add blender library path to `$LD_LIBRARY_PATH`:
```shell
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/blender/lib' >> ~/.bashrc
```

##### 2. Copy required python libraries to blender
Copy python libraries to the python's blender site-packages:
```shell
sudo cp -r /opt/conda/envs/plant_imager/lib/python3.7/site-packages/markupsafe/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_imager/lib/python3.7/site-packages/flask/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_imager/lib/python3.7/site-packages/itsdangerous/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_imager/lib/python3.7/site-packages/click/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_imager/lib/python3.7/site-packages/werkzeug/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_imager/lib/python3.7/site-packages/jinja2/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_imager/lib/python3.7/site-packages/imageio/ /opt/blender/2.81/python/lib/python3.7/site-packages/
```

##### 3. Install ROMI sources
We will now finish by cloning and installing the ROMI sources for `plant-imager`.
```shell
# Don't forget to activate the environment!
conda activate plant_imager
cd plant-imager
# Install `plantdb` from sub-modules:
python -m pip install -e ./plantdb/
# Install `romitask` from sub-modules:
python -m pip install -e ./romitask/
# Install `plant-imager`:
python -m pip install -e .
```

> :information_source: Please notice that we here use the git sub-modules to clone and install `romitask` and `plantdb`.

> :information_source: The `-e` option install the module or sub-module in *editable* mode.
> That means you will not have to reinstall them if you make modifications to the sources.