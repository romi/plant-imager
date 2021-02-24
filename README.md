# ROMI Scanner
Gather hardware control of the ROMI 3D scanner as well as the virtual scanner.

### Virtual Scanner
The romi virtual scanner is based on Blender. We recommend to use it inside a docker container.

#### Building the Docker image
In this repository, you will find a script `build.sh` in the `docker` directory.

```
    git clone https://github.com/romi/romiscanner.git
    cd romiscanner/
    cd docker/
    ./build.sh
```
This will create by default a docker image `romiscanner:latest`.
Inside the docker image, a user is created and named as the one currently used by your system.
If you want more build options (specific branches, tags...etc), type `./build.sh --help`.

#### Running the docker container
In the docker directory, you will find also a script named `run.sh`.

To show more options, type `./run.sh --help`

##### Example: generating a virtual plant dataset with lpy and Blender
In this example, you only have to replace path values and `cd` to whose defined in your own system:
```
cp -r romiscanner/database_example /home/host/path/ # Copy the database_example to avoid generating the dataset in the git repository
cd romiscanner/docker
./run.sh -t latest -db /my/host/path/database_example # This will map to `db` directory located in the the docker's user home
>>>(lpyEnv) user@5c9e389f223d  romi_run_task --config romiscanner/config/vscan_lpy_blender.toml VirtualScan db/generated_dataset # Run VirtualScan as usual by specifying your own generated_dataset
```
After a while, if the generation has succeeded, you can check the generated dataset on your mapped host machine directory `/my/host/path/database_example/generated_dataset`
