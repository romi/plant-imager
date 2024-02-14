# Welcome to PlantImager

![ROMI_ICON2_greenB.png](assets/images/ROMI_ICON2_greenB.png)

For full documentation of the ROMI project visit [docs.romi-project.eu](https://docs.romi-project.eu/).

## About

To be as clear as possible, we first define the following names:
- _PlantImager_: hardware control of the ROMI _3D plant imager_.
- _VirtualPlantImager_: simulate the plant imager using [LPY](https://github.com/fredboudon/lpy) to generate virtual plants and [Blender](https://www.blender.org/) for rendering. **We recommend using it inside a docker container.**


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
