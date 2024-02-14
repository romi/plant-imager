# Docker for VirtualPlantImager

## Prerequisites

Follow the [getting started with docker](index.md#getting-started-with-docker) instructions to install the required software.

!!! important
    We advise to assign an **existing local database directory** to `$ROMI_DB`, it will be mounted at container startup.
    To see how to create a local database directory, look [here](/plant_imager/install/plantdb_setup/#initialize-a-romi-database).


## Start a container

Assuming you have a valid ROMI database directory under `/data/ROMI/DB`, you can easily download and start the
pre-built `roboticsmicrofarms/plantimager` docker image with one of the following command:

=== "run.sh & `ROMI_DB`"
    From the root directory of the repository, use the convenience `run.sh` script:
    ```shell
    export ROMI_DB=/data/ROMI/DB
    ./docker/run.sh
    ```
=== "run.sh & `-db`"
    From the root directory of the repository, use the convenience `run.sh` script:
    ```shell
    ./docker/run.sh -db /data/ROMI/DB
    ```
=== "docker run"
    From any directory, use the `docker run` command as follows:
    ```shell
    export ROMI_DB=/data/ROMI/DB
    docker run --runtime=nvidia --gpus all \
    --env PYOPENCL_CTX='0' \
    -v $ROMI_DB:/myapp/db \
    -it roboticsmicrofarms/plantimager:latest
    ```

This should start the latest pre-built `roboticsmicrofarms/plantimager` docker image in interactive mode.
The database location inside the docker container is `/myapp/db`.

!!! note
    - `-v $ROMI_DB:/myapp/db` performs a **bind mount** to enable access to the local database by the docker image.
    See the official [documentation](https://docs.docker.com/storage/bind-mounts/).
    - Use `./docker/run.sh -h` to get all details about how to use it.

## Build a docker image

If you do not wish to use one of the `roboticsmicrofarms/plantimager` pre-built image, you may build an image using
the `docker/Dockerfile` recipe accessible in the repository of `plantimager`.

We provide a convenience bash script to ease the build of `roboticsmicrofarms/plantimager` docker image.
You can choose to use this script OR to "manually" call the `docker build` command.

=== "build.sh"
    From the root directory of the repository, use the convenience `build.sh` script:
    ```shell
    ./docker/build.sh
    ```

=== "docker build"
    From the root directory of the repository, use the `docker build` command as follows:
    ```shell
    export VTAG="latest"
    docker build -t roboticsmicrofarms/plantimager:$VTAG .
    ```

!!! tips
    - By default, the image tag is 'latest', you can change it, _e.g._ to 'dev' with `-t dev`.
    - Use `./docker/build.sh -h` to get all details about how to use it.

You may want to **clean the build cache**, at least from time to time, with:
```shell
docker builder prune -a
```


## Publish docker image

To push a newly built image on docker hub:

```shell
export VTAG="latest"
docker push roboticsmicrofarms/plantdb:$VTAG
```

This requires a valid account & token on dockerhub!

## Example usage

### Test

You can test the creation of a virtual plant and its acquisition by the virtual scanner as follows:

```shell
./docker/run.sh --test
```

### Executing a ROMI task

To call a ROMI task, as defined in the `romitask` library, you should use the `romi_run_task` CLI.

For example to create a virtual plant and acquire it with the `VirtualScanner`, as `<my_vscan>`, using the **Blender server** , you may use the following command:
```shell
romi_run_task VirtualScan \
  /myapp/db/<my_scan>/ \
  --config plant-imager/configs/vscan_lpy_blender.toml
```

!!! important
    The previous command rely on the presence of a `vscan_data` directory, as it contains the LPY model, background and textures to use (as defined by the TOML configuration file). 
    It is accessible in the repository under `plant-imager/database_example/vscan_data`.
    
### TOML config

!!! todo
    The following subsections need to be reviewed!

#### VirtualPlant

To generate a virtual plant using LPY, the default configuration is as follows:
```toml
[VirtualPlant]
lpy_file_id = "arabidopsis_notex"

[VirtualPlant.lpy_globals]
BRANCHON = false
MEAN_NB_DAYS = 40
STDEV_NB_DAYS = 5
BETA = 51
INTERNODE_LENGTH = 1.3
STEM_DIAMETER = 0.25
```

#### VirtualScan

To perform a scan of a virtual plant, the default configuration is as follows:
```toml
[PaletteFileset]
scan_id = "vscan_data"

[HdriFileset]
scan_id = "vscan_data"

[LpyFileset]
scan_id = "vscan_data"

[ScanPath.kwargs]
center_x = 0
center_y = 0
z = 32
tilt = 3
radius = 40
n_points = 36

[ScanPath]
class_name = "Circle"

[VirtualScan]
load_scene = false
scene_file_id = ""
use_palette = true
use_hdri = true
obj_fileset = "VirtualPlant"
hdri_fileset = "HdriFileset"
scene_fileset = "SceneFileset"
palette_fileset = "PaletteFileset"
render_ground_truth = true
colorize = true

[VirtualScan.scanner]
width = 1440
height = 1080
focal = 16
flash = false
port = 9001
add_leaf_displacement = true
```