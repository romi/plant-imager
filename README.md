# -Virtual- Plant Imager

- Plant Imager: Gather hardware control of the ROMI 3D plant imager as well as the virtual plant imager.

- Virtual Plant Imager: The romi virtual plant imager is based on Blender. We recommend using it inside a docker container.

## Docker

### Building the Docker image
In this repository, you will find a script `build.sh` in the `docker` directory.

```
    git clone https://github.com/romi/plant-imager.git
    cd plant-imager/
    ./docker/build.sh
```
This will create by default a docker image `plantimager:latest`.
Inside the docker image, a user is created and named as the one currently used by your system.
If you want more build options (specific branches, tags...etc), type `./docker/build.sh --help`.

### Running the docker container
In the docker directory, you will find also a script named `run.sh`.

To show more options, type `./run.sh --help`

#### Example: generating a virtual plant dataset with lpy and Blender
In this example, you only have to replace path values and `cd` to whose defined in your own system:
```
cp -r plant-imager/database_example /home/host/path/ # Copy the database_example to avoid generating the dataset in the git repository
cd plant-imager/docker
./run.sh -t latest -db /my/host/path/database_example # This will map to `db` directory located in the the docker's user home
>>>(lpyEnv) user@5c9e389f223d  romi_run_task --config plant-imager/config/vscan_lpy_blender.toml VirtualScan db/generated_dataset # Run VirtualScan as usual by specifying your own generated_dataset
```
After a while, if the generation has succeeded, you can check the generated dataset on your mapped host machine directory `/my/host/path/database_example/generated_dataset`

## Conda
### Install in conda environment

#### System requirements
```bash
sudo apt-get install libgl1-mesa-dev libxi6 gcc
```

#### Conda environment creation
Create a conda environment named `plant_scanner` and install required dependencies:
```bash
conda create -n plant_scanner python=3.7
conda install -n plant_scanner -c conda-forge -c fredboudon flask imageio toml luigi boost=1.70.0 qhull=2015.2 openalea.lpy
```

#### Blender setup
In order to use the `bpy` module we have to do this mess:

##### 1. Download Blender2.81
Download Blender2.81, extract the archive and move its contents to `/opt/blender`:
```bash
BLENDER_URL=https://download.blender.org/release/Blender2.81/blender-2.81a-linux-glibc217-x86_64.tar.bz2
wget --progress=bar $BLENDER_URL
tar -xjf blender-2.81a-linux-glibc217-x86_64.tar.bz2
sudo mv blender-2.81a-linux-glibc217-x86_64 /opt/blender
rm blender-2.81a-linux-glibc217-x86_64.tar.bz2
```

Add blender library path to `$LD_LIBRARY_PATH`:
```bash
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/blender/lib' >> ~/.bashrc
```

##### 2. Copy required python libraries to blender
Copy python libraries to the python's blender site-packages:
```bash
sudo cp -r /opt/conda/envs/plant_scanner/lib/python3.7/site-packages/markupsafe/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_scanner/lib/python3.7/site-packages/flask/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_scanner/lib/python3.7/site-packages/itsdangerous/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_scanner/lib/python3.7/site-packages/click/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_scanner/lib/python3.7/site-packages/werkzeug/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_scanner/lib/python3.7/site-packages/jinja2/ /opt/blender/2.81/python/lib/python3.7/site-packages/
sudo cp -r /opt/conda/envs/plant_scanner/lib/python3.7/site-packages/imageio/ /opt/blender/2.81/python/lib/python3.7/site-packages/
```

##### 3. Install ROMI sources
We will now finish by cloning and installing the ROMI sources for `romiscanner`, `romiscan` and `romidata`:
```bash
ROMISCAN_BRANCH=dev
ROMIDATA_BRANCH=dev
ROMISCANNER_BRANCH=master
# Don't forget to activate the environment!
conda activate plant_scanner
# Clone & install romidata
git clone --branch $ROMIDATA_BRANCH https://github.com/romi/romidata
python -m pip install -e ./romidata/ --no-cache-dir
# Clone & install romiscanner
git clone --branch $ROMISCANNER_BRANCH https://github.com/romi/romiscanner
python -m pip install -e ./romiscanner/ --no-cache-dir
# Clone & install romiscan
git clone --branch $ROMISCAN_BRANCH https://github.com/romi/romiscan
python -m pip install -r ./romiscan/requirements.txt --no-cache-dir
python -m pip install -e ./romiscan/ --no-cache-dir
```