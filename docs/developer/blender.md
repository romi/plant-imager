# Blender

We use Blender 2.93 LTS to generate.
It can be downloaded as follows:
```shell
BLENDER_URL="https://ftp.halifax.rwth-aachen.de/blender/release/Blender2.93/blender-2.93.16-linux-x64.tar.xz"
wget --progress=bar:force:noscroll ${BLENDER_URL}
```

## Requirements
To use the GPU with CUDA, you will need the `nvidia-cuda-toolkit`.
On Ubuntu22.04, it can be installed as follows:
```shell
sudo apt install nvidia-cuda-toolkit
```

!!! note
    There is no need to install it in the docker image, it will use the system install.

## Quick start

```shell
BLENDER_PATH="~/Softwares/blender-2.93"
mkdir -p ${BLENDER_PATH}
tar -xJf blender-2.93.16-linux-x64.tar.xz --directory ${BLENDER_PATH} --strip-components=1
```

## Start a Blender Python console
You can start a Blender Python console using the `blender` binary in the extraction folder as follows:
```shell
cd ${BLENDER_PATH}
./blender -E CYCLES -b --python-console
```

!!! note
    The `-b` option start Blender in the background, this way you only get the Python console and not the Blender GUI.


### Check GPU access
Once you have access to a Python console you can check the GPU accessibility with:
```shell
import bpy
devices = bpy.context.preferences.addons['cycles'].preferences.get_devices()
cuda_devices = bpy.context.preferences.addons['cycles'].preferences.get_devices_for_type("CUDA")
print(len(cuda_devices))
```

If the number is zero, make sure you have installed the `nvidia-cuda-toolkit` library.