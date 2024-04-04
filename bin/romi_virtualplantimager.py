#!/usr/bin/env romi_bpy

import argparse
import distutils
import distutils.util
import glob
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr
from contextlib import redirect_stdout

import bpy
import numpy as np
from flask import Flask
from flask import jsonify
from flask import request
from flask import send_from_directory
from mathutils import Vector
from werkzeug.utils import secure_filename

from plantimager.blender import Camera
from plantimager.blender import VirtualPlant
from plantimager.blender import _get_log_filepath
from plantimager.blender import check_engine
from plantimager.log import configure_logger

logger = configure_logger("FlaskVPI")

image_extensions = [".png", ".jpg"]


def parsing():
    parser = argparse.ArgumentParser(description='Run a plant imaging task.')

    parser.add_argument('--data-dir', dest='data_dir', default='data',
                        help='location of obj and mtl files')
    parser.add_argument('--hdri-dir', dest='hdri_dir', default='hdri',
                        help='location of hdr files')
    parser.add_argument('--port', dest='port', default=5000,
                        help='port for flask server')
    parser.add_argument('--scene', dest='scene', default=None,
                        help='load blender scene')
    return parser.parse_args()


def main():
    check_engine()
    # Remove the cube object (automatically created by Blender when initializing a new scene):
    if 'Cube' in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects['Cube'], do_unlink=True)
    # Remove the light object (automatically created by Blender when initializing a new scene):
    if 'Light' in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects['Light'], do_unlink=True)

    # - Override system arguments:
    try:
        # Search for the index of the "--" marker (see `VirtualScannerRunner.start()`)
        idx = sys.argv.index('--')
        assert idx != len(sys.argv) - 2  # assert it is not found at the end of the str
    except ValueError or AssertionError:
        # If not found, remove all arguments
        sys.argv = ["null"]
    else:
        # If found
        sys.argv = ["null"] + sys.argv[idx + 1:]

    # - Parse arguments:
    args = parsing()
    data_dir = args.data_dir
    hdri_dir = args.hdri_dir
    # Gather the list of objects:
    object_list = glob.glob(os.path.join(data_dir, "*.obj"))
    object_list = [os.path.basename(o) for o in object_list]
    # Gather the list of backgrounds:
    background_list = glob.glob(os.path.join(hdri_dir, "*.hdr"))
    background_list = [os.path.basename(o) for o in background_list]
    L = len(background_list)
    # Open the Blender scene file, if any:
    if args.scene is not None:
        bpy.ops.wm.open_mainfile(filepath=args.scene)

    # -- Initialize a `Camera` instance:
    cam = Camera(bpy.context.scene, bpy.data, False)
    cam.set_intrinsics(1616, 1080, 24)
    cam.move(-100, 0, 50, 90, 0, -90)

    # -- Initialize a `VirtualPlant` instance:
    obj = VirtualPlant(bpy.context.scene, bpy.data)

    # The whole Flask app will run in a temporary directory.
    # When the app close, it will clean the whole temporary directory.
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize the Flask app:
        app = Flask(__name__)
        logfile = _get_log_filepath(tmpdir)

        @app.route('/hello_world', methods=['GET'])
        def hello_world():
            """Dummy test function returning some info about the server."""
            s = ["Hello World!"]
            s += [f"I am a Flask server named '{app.name}'."]
            # Get Blender version & build date:
            s += [f"I run Blender {bpy.app.version_string} built on {bpy.app.build_date.decode()}."]
            # Get Python version:
            pyv = subprocess.run(['python', '--version'], capture_output=True)
            pyv = pyv.stdout.decode().replace('\n', '')
            s += [f"I run {pyv}."]
            return jsonify(s)

        @app.route('/classes', methods=['GET'])
        def classes():
            """Returns the list of available classes."""
            return jsonify(obj.classes)

        @app.route('/bounding_box', methods=['GET'])
        def bounding_box():
            """Returns the objects bounding-box."""
            xmin, ymin, zmin = 10000, 10000, 10000
            xmax, ymax, zmax = -10000, -10000, -10000
            for o in obj.data.objects:
                m = o.matrix_world
                if o.name not in obj.scene_objects:
                    logger.debug(f"m = {m}")
                    for b in o.bound_box:
                        b1 = m @ Vector(b)
                        x, y, z = b1
                        xmin, ymin, zmin = np.minimum([xmin, ymin, zmin], [x, y, z])
                        xmax, ymax, zmax = np.maximum([xmax, ymax, zmax], [x, y, z])

            bbox = {
                "x": [xmin, xmax],
                "y": [ymin, ymax],
                "z": [zmin, zmax]
            }
            return jsonify(bbox)

        @app.route('/backgrounds', methods=['GET'])
        def backgrounds():
            """Returns the list of backgrounds."""
            return jsonify(background_list)

        @app.route('/camera_intrinsics', methods=['POST', 'GET'])
        def camera_intrinsics():
            """Set or returns the camera intrinsic parameters."""
            if request.method == 'POST':
                kwargs = request.form.to_dict()
                cam.set_intrinsics(int(kwargs["width"]), int(kwargs["height"]), float(kwargs["focal"]))
                return jsonify('OK')
            else:
                K = cam.get_K()
                camera_model = {
                    "width": cam.render.resolution_x,
                    "height": cam.render.resolution_y,
                    "model": "OPENCV",
                    "params": [K[0][0], K[1][1], K[0][2], K[1][2], 0.0, 0.0, 0.0, 0.0]
                }
                return jsonify(camera_model)

        @app.route('/camera_pose', methods=['POST', 'GET'])
        def camera_pose():
            """Set or get the camera position in space."""
            if request.method == 'POST':
                kwargs = request.form.to_dict()
                cam.move(**kwargs)
                return jsonify('OK')
            else:
                R, T = cam.get_RT()
                return jsonify({"rotmat": R, "tvec": T})

        @app.get('/upload_object')
        def upload_object_get():
            """Load the OBJ, MTL & palette files to Blender.

            Display a form to upload the OBJ, MTL & palette files to the server from a browser.
            """
            HTML = '''
                    <!doctype html>
                    <title>Upload mesh, material & palette files</title>
                    <h1>Upload mesh, material & palette files</h1>
                    <form method="post" class="upload-form" enctype=multipart/form-data>
                      <div class="form-example">
                        <label for="obj">Mesh file: </label>
                        <input type="file" name="obj" id="obj" accept=".obj">
                      </div>
                      <div class="form-example">
                        <label for="mtl">Material file: </label>
                        <input type="file" name="mtl" id="mtl" accept=".mtl">
                      </div>
                      <div class="form-example">
                        <label for="palette">Palette image file: </label>
                        <input type="file" name="palette" id="palette" accept="image/png, image/jpeg">
                      </div>
                      <div class="form-example">
                        <input type="submit" value="Upload">
                      </div>
                    </form>
                    '''
            return HTML

        @app.post('/upload_object')
        def upload_object_post():
            """Load the OBJ, MTL & palette files to Blender.

            Get the OBJ, MTL & palette files from the POST request and load them into Blender.
            """
            # - If no OBJ file is provided, return a message & error code
            if 'obj' not in request.files:
                return "No OBJ file found!", 501
            else:
                obj_file = request.files['obj']
            # - If the OBJ filename is empty, return a message & error code
            if obj_file.filename == '':
                return "No OBJ file name found!", 502
            # - Securely copy the OBJ file:
            obj_file_ext = os.path.splitext(obj_file.filename)[-1].lower()
            if obj_file_ext == ".obj":
                obj_filename = secure_filename(obj_file.filename)
                obj_file.save(os.path.join(tmpdir, obj_filename))
            else:
                return f"Wrong extension for OBJ file, expected '.obj' got '{obj_file_ext}'!", 503
            obj_location = os.path.join(tmpdir, obj_filename)

            # - Securely copy the MTL file:
            if 'mtl' in request.files:
                mtl_file = request.files['mtl']
                mtl_file_ext = os.path.splitext(mtl_file.filename)[-1].lower()
                # Check the MTL filename is not empty & has the right extension prior to saving:
                if mtl_file.filename != '' and mtl_file_ext == ".mtl":
                    mtl_filename = secure_filename(mtl_file.filename)
                    mtl_file.save(os.path.join(tmpdir, mtl_filename))

            # - Securely copy the PNG palette file, if requested:
            palette_location = None
            if "palette" in request.files and request.files['palette'] != "":
                palette_file = request.files['palette']
                palette_file_ext = os.path.splitext(palette_file.filename)[-1].lower()
                # Check then palette filename is not empty & is a valid image file prior to saving:
                if palette_file.filename != '' and palette_file_ext in image_extensions:
                    # Create a temporary copy of the PNG palette file
                    palette_filename = secure_filename(palette_file.filename)
                    palette_location = os.path.join(tmpdir, palette_filename)
                    palette_file.save(palette_location)

            # - Get XYZ displacements:
            dx = request.form.get('dx')
            dy = request.form.get('dy')
            dz = request.form.get('dz')
            # - Get 'colorize' argument:
            colorize = request.form.get('colorize')
            if colorize is not None:
                colorize = distutils.util.strtobool(colorize)
            else:
                colorize = False

            # - Load all that into Blender:
            obj.load_obj(obj_location, dx, dy, dz, colorize, palette_location)
            return "Successfully loaded all objects in Blender!"

        @app.get('/upload_background')
        def upload_background_get():
            """Load the HDRI background file to Blender.

            Display a form to upload the HDRI background file to the server from a browser.
            """
            HTML = '''
                    <!doctype html>
                    <title>Upload HDRI background</title>
                    <h1>Upload HDRI background</h1>
                    <form method="post" class="upload-form" enctype=multipart/form-data>
                    <div class="form-example">
                      <label for="hdr">HDRI file: </label>
                      <input type="file" name="hdr" id="hdr" accept=".hdr">
                    </div>
                    <div class="form-example">
                      <input type="submit" value="Upload">
                    </div>
                    </form>
                    '''
            return HTML

        @app.post('/upload_background')
        def upload_background_post():
            """Load the HDRI background file to Blender.

            Get the HDRI file from the POST request and load it into Blender
            """
            # - If no HDRI file is provided, return a message & error code
            if 'hdr' not in request.files:
                return "No HDRI file found!", 501
            else:
                hdr_file = request.files['hdr']
            # - If the HDRI filename is empty, return a message & error code
            if hdr_file.filename == '':
                return "No HDRI file name found!", 502
            # - Securely copy the HDRI file:
            hdr_file_ext = os.path.splitext(hdr_file.filename)[-1].lower()
            if hdr_file_ext == ".hdr":
                hdr_filename = secure_filename(hdr_file.filename)
                hdr_location = os.path.join(tmpdir, hdr_filename)
                hdr_file.save(hdr_location)
            else:
                return f"Wrong extension for HDRI file, expected '.hdr' got '{hdr_file_ext}'!", 503

            # - Load the HDRI into Blender:
            cam.load_hdri(hdr_location)
            return "Successfully loaded HDRI file in Blender!"

        @app.route("/add_random_displacement/<class_id>", methods=['GET'])
        def add_random_displacement(class_id):
            obj.add_leaf_displacement(class_id)
            return jsonify('OK')

        light_data = bpy.data.lights.new(type='POINT', name="flash")

        @app.route('/render', methods=['GET'])
        def render():
            flash = request.args.get('flash')
            light_obj = None
            if flash is not None:
                # energy = 0.3 * np.random.choice([0.1,0.1,0.1,0.1,0.1,1,2,3,4,5,6,7,8,9,10,20])*1e8
                energy = 0.3 * 1e8
                light_obj = bpy.data.objects.new(name='Flash', object_data=light_data)
                light_obj.location = cam.cam.location
                light_obj.rotation_euler = cam.cam.rotation_euler
                light_obj.data.energy = energy
                light_obj.data.shadow_soft_size = 1000
                view_layer = bpy.context.view_layer
                view_layer.active_layer_collection.collection.objects.link(light_obj)
                light_obj.select_set(True)
                view_layer.objects.active = light_obj
                logger.debug(light_obj)
            obj.show_all()

            bpy.context.scene.render.filepath = os.path.join(tmpdir, "plant.png")
            with open(logfile, mode="a") as f:
                # Redirect blender outputs to a log file:
                with redirect_stdout(f), redirect_stderr(f):
                    bpy.ops.render.render(write_still=True)
            if light_obj is not None:
                bpy.data.objects.remove(light_obj, do_unlink=True)

            return send_from_directory(tmpdir, "plant.png")

        @app.route('/render_class/<class_id>', methods=['GET'])
        def render_class(class_id):
            obj.show_class(class_id)
            bpy.context.scene.render.filepath = os.path.join(tmpdir, "plant.png")
            with open(logfile, mode="a") as f:
                # Redirect blender outputs to a log file:
                with redirect_stdout(f), redirect_stderr(f):
                    bpy.ops.render.render(write_still=True)
            return send_from_directory(tmpdir, "plant.png")

        # Detect available CUDA devices:
        cuda_dev = bpy.context.preferences.addons['cycles'].preferences.get_devices_for_type("CUDA")
        # Inform if CUDA compatible devices have been found:
        if len(cuda_dev) == 1:
            logger.info(f"Found a CUDA compatible device: {cuda_dev.name}")
        elif len(cuda_dev) > 1:
            logger.info(f"Found multiple CUDA compatible devices: {[', '.join([dev.name for dev in cuda_dev])]}")
        else:
            logger.warning("No CUDA devices found!")
            cuda_dev = None

        if cuda_dev is not None:
            # Activate "CYCLES" engine:
            # bpy.context.scene.render.engine = 'CYCLES'  # should be set with `-E CYCLES` when calling blender
            # Set the `compute_device_type` to "CUDA"
            bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
            # Use all CUDA compatible devices:
            for device in bpy.context.preferences.addons["cycles"].preferences.devices:
                device.use = 1
                logger.info(f"Using CUDA compatible device: {device.name}")
            # Activate GPU rendering for current scene:
            bpy.context.scene.cycles.device = 'GPU'
            # Activate GPU rendering for all scenes:
            for scene in bpy.data.scenes:
                scene.cycles.device = 'GPU'

        app.run(debug=False, host="0.0.0.0", port=int(args.port))


if __name__ == "__main__":
    main()
