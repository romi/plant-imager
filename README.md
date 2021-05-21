# -Virtual- Plant Imager

- Plant Imager: Gather hardware control of the ROMI _3D plant imager_ as well as the _virtual plant imager_.

- Virtual Plant Imager: The romi _virtual plant imager_ is based on Blender. We recommend using it inside a docker container.


## Docker

### Building the docker image
In this repository, you will find a script `build.sh` in the `docker/` directory.

```shell
git clone https://github.com/romi/plant-imager.git
cd plant-imager/
git submodule init
git submodule update
./docker/build.sh
```

This will create by default a docker image named `plantimager:latest`.
Inside the docker image, a user is created and named as the one currently used by your system.
If you want more build options (specific branches, tags...etc), type `./docker/build.sh --help`.

### Running the docker container
In the docker directory, you will also find a script named `run.sh`.

To show more options, type `./run.sh --help`

#### Example: generating a virtual plant dataset with lpy and Blender
In this example, you only have to replace path values and `cd` to whose defined in your own system:
```shell
cp -r plant-imager/database_example /home/host/path/ # Copy the database_example to avoid generating the dataset in the git repository
cd plant-imager/docker
./run.sh -t latest -db /my/host/path/database_example # This will map to `db` directory located in the the docker's user home
>>>(lpyEnv) user@5c9e389f223d  romi_run_task --config plant-imager/config/vscan_lpy_blender.toml VirtualScan db/generated_dataset # Run VirtualScan as usual by specifying your own generated_dataset
```
After a while, if the generation has succeeded, you can check the generated dataset on your mapped host machine directory `/my/host/path/database_example/generated_dataset`


## Conda
### Install in conda environment

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
We will now finish by cloning and installing the ROMI sources for `plant-imager`, `plant-3d-vision` and `plantdb`:
```shell
PLANT3DVISION_BRANCH=dev
PLANTDB_BRANCH=dev
PLANTIMAGER_BRANCH=master
# Don't forget to activate the environment!
conda activate plant_imager
# Clone & install plantdb
git clone --branch $PLANTDB_BRANCH https://github.com/romi/plantdb
python -m pip install -e ./plantdb/ --no-cache-dir
# Clone & install plant-imager
git clone --branch $PLANTIMAGER_BRANCH https://github.com/romi/plant-imager
python -m pip install -e ./plant-imager/ --no-cache-dir
# Clone & install plant-3d-vision
git clone --branch $PLANT3DVISION_BRANCH https://github.com/romi/plant-3d-vision
python -m pip install -r ./plant-3d-vision/requirements.txt --no-cache-dir
python -m pip install -e ./plant-3d-vision/ --no-cache-dir
```