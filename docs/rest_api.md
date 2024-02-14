# VirtualPlantImager REST API

The Python implementation is done in the `bin/romi_virtualplantimager.py` file, that is also used to start a Flask server.

Hereafter we list the GET/POST requests that can be made and give some examples.


## REST URLs

### Objects

* `/objects` (GET): retrieve the list of `obj` files in the data folder that can be loaded.
* `/load_object/<object_id>` (GET) load the given object in the scene. Takes a translation vector as URL parameters (`dx`, `dy`, `dz`)

### Classes

* `/classes` (GET): retrieve the list of classes.

### Backgrounds

* `/backgrounds` (GET): retrieve the list of `hdr` files in the `hdri` folder that can be loaded.
* `/load_background/<background_id>` (GET) load the given background in the scene.

### Camera

* `/camera_intrinsics` (POST): set camera intrinsics. Keys: `width`, `height`, `focal`
* `/camera_pose` (POST): set camera pose. Keys: `tx`, `ty`, `tz`, `rx`, `ry`, `rz`

### Rendering

* `/render` (GET): gets the rendering of the scene
* `/render_class/<class_id>` (GET) renders the scene, with everything transparent except the given class

!!! todo
    Missing endpoints.

## Examples
Using a browser to send HTTP requests is not too convenient.
Instead, you may use [httpie](https://httpie.org/) to send HTTP commands from a terminal.

To easily adapt to other configurations, we define the `$VPI_HOST` & `$VPI_PORT` variables.
For example, matching the example given above, we define:
```shell
export VPI_HOST='172.17.0.2'
export VPI_PORT='9001'
```

### Setup camera
```shell
http -f post "http://$VPI_HOST:$VPI_PORT/camera_intrinsics width=1920 height=1080 focal=35"
```

### Load `arabidopsis_0` OBJ
```shell
http get "http://$VPI_HOST:$VPI_PORT/load_object/arabidopsis_0.obj?dx=10&dy=20&dz=1"
```

### Load "old tree in the park" background
```shell
http get "http://127.0.0.1:$VPI_PORT/load_background/old_tree_in_city_park_8k.hdr"
```

### Move camera
```shell
http -f post "http://$VPI_HOST:$VPI_PORT/camera_pose tx=-60 ty=0 tz=50 rx=60 ry=0 rz=-90"
```

### Render scene and download image
```shell
http --download get "http://$VPI_HOST:$VPI_PORT/render"
```

### Render only leaves
```shell
http --download get "http://$VPI_HOST:$VPI_PORT/render_class/Color_7"
```
