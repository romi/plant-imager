# Welcome to PlantImager

![ROMI_ICON2_greenB.png](assets/images/ROMI_ICON2_greenB.png)

For full documentation of the ROMI project visit [docs.romi-project.eu](https://docs.romi-project.eu/).

## About

To be as clear as possible, we first define the following names:

- _PlantImager_: hardware control of the ROMI _3D plant imager_.
- _VirtualPlantImager_: simulate the _3D plant imager_ using [LPY](https://github.com/fredboudon/lpy) to generate virtual plants and [Blender](https://www.blender.org/) for rendering RGB images.

**We recommend using the _VirtualPlantImager_ with a docker container.**

## Getting started

### Create a local database
If not done yet, start by creating a local `plantdb` database, whose path will be known as `$ROMI_DB`:
```shell
export ROMI_DB="/data/ROMI/"
mkdir -p "${ROMI_DB}"
touch "${ROMI_DB}/romidb"
```

To use the _VirtualPlantImager_, yu will also need the `vscan_data` folder accessible under `plant-imager/database_example`.

### Set the permissions
Create a `romi` group and give it rights over the local `plantdb` database

1. Create the `romi` group with `2020` as GID:
   ```shell
   sudo addgroup romi --gid 2020
   ```
2. Add the current user to the `romi` group:
   ```shell
   sudo usermod -a -G romi $USER
   ```
3. Change the group of the local database:
   ```shell
   sudo chown -R :romi $ROMI_DB
   ```
4. Check the rights with:
   ```shell
   ls -al $ROMI_DB
   ```
   This should yield something like:
   ```
   drwxrwxr-x  2 myuser romi     4096 nov.  21 12:00 .
   drwxrwxrwx 31 myuser myuser   4096 nov.  21 12:00 ..
   -rw-rw-r--  1 myuser romi        0 nov.  21 12:00 romidb
   ```
   Where `myuser` is your username.

!!! note
    After step 2 you will need to re-open a terminal to belong to the `romi` group.


## Getting started with Docker
We strongly recommend using the docker images to use this library.

### PlantImager docker image

#### Pull a pre-built image
The simplest way to use the docker image is to pull the pre-built `roboticsmicrofarms/plantimager` docker image as follows:
```shell
docker pull roboticsmicrofarms/plantimager:latest
```

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


### VirtualPlantImager docker image

#### Pull a pre-built image
The simplest way to use the docker image is to pull the pre-built `roboticsmicrofarms/virtualplantimager` docker image as follows:
```shell
docker pull roboticsmicrofarms/virtualplantimager:latest
```

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
