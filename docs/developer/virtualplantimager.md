# VirtualPlantImager specifications

## Start the Blender server
There are many ways to do this, but the simplest & fastest option is to use the Docker image `roboticsmicrofarms/virtualplantimager`.

!!! note
    We make use of the `$ROMI_DB` environment variable.
    If not done yet, you may want to set it with `export ROMI_DB=/path/to/database`.
    Or replace it with the path to use.

### 1. Start a container
=== "Docker CLI"
    Start a container and open a bash shell:
    ```shell
    docker run -it --gpus all roboticsmicrofarms/virtualplantimager:latest -v $ROMI_DB:/myapp/db bash
    ```

=== "`run.sh` script"
    Start a container and open a bash shell:
    ```shell
    ./docker/virtualplantimager/run.sh -db $ROMI_DB
    ```

### 2. Start the Blender Flask server
Then start the Blender server (listening to port `9001`) with:
```shell
romi_bpy plant-imager/bin/romi_virtualplantimager -- --port 9001
```

When the server is up and running you should get something like:
```
 * Serving Flask app 'romi_virtualplantimager'
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:9001
 * Running on http://172.17.0.2:9001
```

!!! note
    The first HTTP address is accessible from within the container.
    The second HTTP address is accessible from the host running the container.

## Test the server

=== "From the host"
    You may now use a web browser to submit a `/hello_world` request at `http://172.17.0.2:9001`.
    
    To do so, just copy/paste `http://172.17.0.2:9001/hello_world` to the URL bar.

=== "From the container"
    You may use Python to submit a request at `http://172.0.0.1:9001`.

    For example, you may get info by submitting a `/hello_world` request as follows:

    1. Open a new shell in the running container with (do not forget to replace the `CONTAINER_ID`):
    ```shell
    docker exec -it CONTAINER_ID bash
    ```
    2. Then use Python to send a GET request:
    ```shell
    python -c "import requests
    res = requests.get('http://127.0.0.1:9001/hello_world')
    print(res.content.decode())"
    ```

You should get a JSON response similar to this:
```
"Hello World!"
"I am a Flask server named 'romi_virtualplantimager'."
"I run Blender 2.93.16 built on 2023-03-21."
"I run Python 3.9.16."
```
