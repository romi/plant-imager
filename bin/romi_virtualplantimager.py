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
from math import pi
from random import randint

import bpy
import imageio.v3 as iio
import numpy as np
from flask import Flask
from flask import jsonify
from flask import request
from flask import send_from_directory
from mathutils import Matrix
from mathutils import Vector
from werkzeug.utils import secure_filename

from plantimager.blender import _get_log_filepath
from plantimager.blender import check_engine
from romitask.log import configure_logger

logger = configure_logger(__name__)


# ---------------------------------------------------------------
#
# 3x4 P matrix from Blender camera
# ---------------------------------------------------------------

# BKE_camera_sensor_size
def get_sensor_size(sensor_fit, sensor_x, sensor_y):
    if sensor_fit == 'VERTICAL':
        return sensor_y
    return sensor_x


# BKE_camera_sensor_fit
def get_sensor_fit(sensor_fit, size_x, size_y):
    if sensor_fit == 'AUTO':
        if size_x >= size_y:
            return 'HORIZONTAL'
        else:
            return 'VERTICAL'
    return sensor_fit


image_extensions = [".png", ".jpg"]


class Camera():
    def __init__(self, scene, data, hdri_enabled=False):
        self.scene = scene
        self.cam = scene.camera
        self.render = scene.render
        self.data = data
        self.hdri_enabled = hdri_enabled
        if hdri_enabled:
            self.setup_hdri()
        else:
            self.setup_background()

    def get_K(self):
        camd = self.cam.data
        scene = self.scene
        f_in_mm = camd.lens
        scale = scene.render.resolution_percentage / 100
        resolution_x_in_px = scale * scene.render.resolution_x
        resolution_y_in_px = scale * scene.render.resolution_y
        sensor_size_in_mm = get_sensor_size(camd.sensor_fit, camd.sensor_width, camd.sensor_height)
        sensor_fit = get_sensor_fit(
            camd.sensor_fit,
            scene.render.pixel_aspect_x * resolution_x_in_px,
            scene.render.pixel_aspect_y * resolution_y_in_px
        )
        pixel_aspect_ratio = scene.render.pixel_aspect_y / scene.render.pixel_aspect_x
        if sensor_fit == 'HORIZONTAL':
            view_fac_in_px = resolution_x_in_px
        else:
            view_fac_in_px = pixel_aspect_ratio * resolution_y_in_px
        pixel_size_mm_per_px = sensor_size_in_mm / f_in_mm / view_fac_in_px
        s_u = 1 / pixel_size_mm_per_px
        s_v = 1 / pixel_size_mm_per_px / pixel_aspect_ratio

        # Parameters of intrinsic calibration matrix K
        u_0 = resolution_x_in_px / 2 - camd.shift_x * view_fac_in_px
        v_0 = resolution_y_in_px / 2 + camd.shift_y * view_fac_in_px / pixel_aspect_ratio
        skew = 0  # only use rectangular pixels

        K = [[s_u, skew, u_0],
             [0, s_v, v_0],
             [0, 0, 1]]
        return K

    def get_RT(self):
        # bcam stands for blender camera
        R_bcam2cv = Matrix(
            ((1, 0, 0),
             (0, -1, 0),
             (0, 0, -1)))

        # Use matrix_world instead to account for all constraints
        location, rotation = self.cam.matrix_world.decompose()[0:2]
        R_world2bcam = rotation.to_matrix().transposed()

        # Use location from matrix_world to account for constraints:     
        T_world2bcam = -1 * R_world2bcam @ location

        # Build the coordinate transform matrix from world to computer vision camera
        R_world2cv = R_bcam2cv @ R_world2bcam
        T_world2cv = R_bcam2cv @ T_world2bcam

        R = np.matrix(R_world2cv)
        T = np.array(T_world2cv)

        return R.tolist(), T.tolist()

    def set_intrinsics(self, width, height, focal):
        """
        :input w image width
        :input h image height
        :input f focal length (equiv. 35mm)
        """

        self.render.resolution_x = width
        self.render.resolution_y = height
        self.render.resolution_percentage = 100

        # Set camera fov in degrees
        self.cam.data.angle = 2 * np.arctan(35 / focal)
        self.cam.data.clip_end = 10000

    def move(self, tx=None, ty=None, tz=None, rx=None, ry=None, rz=None):
        self.cam.rotation_mode = 'XYZ'
        if tx is not None:
            self.cam.location[0] = float(tx)
        if ty is not None:
            self.cam.location[1] = float(ty)
        if tz is not None:
            self.cam.location[2] = float(tz)
        if rx is not None:
            self.cam.rotation_euler[0] = float(rx) * (pi / 180.0)
        if ry is not None:
            self.cam.rotation_euler[1] = float(ry) * (pi / 180.0)
        if rz is not None:
            self.cam.rotation_euler[2] = float(rz) * (pi / 180.0)

    def setup_background(self):
        world = bpy.data.worlds['World']
        world.use_nodes = True
        bg = world.node_tree.nodes['Background']
        bg.inputs[0].default_value[:3] = (0, 0, 0)
        bg.inputs[1].default_value = 1.0

    def setup_hdri(self):
        self.data.worlds["World"].use_nodes = True
        world_nodes = self.data.worlds["World"].node_tree.nodes
        for node in world_nodes:
            world_nodes.remove(node)

        node = world_nodes.new("ShaderNodeTexEnvironment")
        node.name = "Environment Texture"

        node = world_nodes.new("ShaderNodeBackground")
        node.name = "Background"

        node = world_nodes.new("ShaderNodeOutputWorld")
        node.name = "World Output"

        output = world_nodes["Environment Texture"].outputs["Color"]
        input = world_nodes["Background"].inputs["Color"]
        self.data.worlds["World"].node_tree.links.new(output, input)

        output = world_nodes["Background"].outputs["Background"]
        input = world_nodes["World Output"].inputs["Surface"]
        self.data.worlds["World"].node_tree.links.new(output, input)

        world = self.scene.world
        nodes_tree = self.data.worlds[world.name].node_tree
        self.env_text_node = nodes_tree.nodes["Environment Texture"]
        self.hdri_enabled = True

    def load_hdri(self, path):
        if not self.hdri_enabled:
            self.setup_hdri()
        current_bg_image = bpy.data.images.load(path)
        self.env_text_node.image = current_bg_image
        self.scene.render.film_transparent = False


class MultiClassObject():
    def __init__(self, scene, data):
        self.data = data
        self.scene = scene
        self.objects = {}
        self.classes = []
        self.scene_materials = [m.name for m in self.data.materials]
        self.scene_objects = [o.name for o in self.data.objects]

    def show_class(self, class_name):
        for o in self.data.objects:
            try:
                m = o.data.materials[0]
                logger.debug("material = %s" % m.name)
                if class_name in m.name:
                    o.hide_render = False
                else:
                    o.hide_render = True
            except:
                o.hide_render = True
        self.scene.render.film_transparent = True

    def show_all(self):
        for o in self.data.objects:
            o.hide_render = False
        self.scene.render.film_transparent = False

    def clear_all_rotation(self):
        for x in self.objects.values():
            x.rotation_euler[0] = 0

    def update_classes(self, colorize: bool = False, palette_location: str = None):
        self.classes = []
        specular = np.random.rand() * 0.02

        if colorize:
            if palette_location is None:
                color = [np.random.rand(), np.random.rand(), np.random.rand()]
            else:
                im = iio.imread(palette_location)
                palette_width, palette_height, channels = im.shape
                color = (im[randint(0, palette_width - 1), randint(0, palette_height - 1)] / 255).tolist()

        for o in self.data.objects:
            if o.name not in self.scene_objects:
                for m in o.data.materials:
                    if m.name not in self.scene_materials:
                        self.classes.append(m.name)
                    if colorize:
                        if len(color) == 3:
                            color += [1.0]
                        # m.node_tree.nodes[1].inputs['Base Color'].default_value = color
                        # m.node_tree.nodes[1].inputs['Specular'].default_value = specular
                        m.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = color
                        m.node_tree.nodes["Principled BSDF"].inputs['Specular'].default_value = specular

    def load_obj(self, fname, dx=None, dy=None, dz=None, colorize=True, palette_location=None):
        """move object by dx, dy, dz if specified"""

        for o in self.objects.values():
            self.data.objects.remove(o, do_unlink=True)
        self.objects = {}

        for m in bpy.data.materials:
            if not m.name in self.scene_materials:
                bpy.data.materials.remove(m)

        bpy.ops.import_scene.obj(filepath=fname)
        self.update_classes(colorize, palette_location)

        for m in self.classes:
            for o in self.data.objects:
                if m in o.name:
                    self.objects[m] = o
                    break

        try:
            dx = float(dx)
        except:
            dx = 0.0
        try:
            dy = float(dy)
        except:
            dy = 0.0
        try:
            dz = float(dz)
        except:
            dz = 0.0

        for o in bpy.context.scene.objects:
            if o.name not in self.scene_objects:
                bpy.ops.object.select_all(action='DESELECT')
                # bpy.context.scene.objects.link(o)
                o.location.x = dx
                o.location.y = dy
                o.location.x = dz
                o.select_set(True)
                bpy.context.view_layer.objects.active = o
                logger.debug("transform %s" % o.name)
                bpy.ops.object.select_all(action='DESELECT')

        self.location = {
            "x": dx,
            "y": dy,
            "z": dz
        }

        # self.clear_all_rotation()


class VirtualPlant(MultiClassObject):
    def add_leaf_displacement(self, leaf_class_name):
        for o in self.data.objects:
            if leaf_class_name in o.name:
                displace_modifier = o.modifiers.new(name="Displace.01", type='DISPLACE')
                tex = self.data.textures.new("Displace.01", 'CLOUDS')
                tex.noise_scale = 2.0
                displace_modifier.texture = tex


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
    parser = argparse.ArgumentParser(description='Run a plant imaging task.')

    parser.add_argument('--data-dir', dest='data_dir', default='data',
                        help='location of obj and mtl files')
    parser.add_argument('--hdri-dir', dest='hdri_dir', default='hdri',
                        help='location of hdr files')
    parser.add_argument('--port', dest='port', default=5000,
                        help='port for flask server')
    parser.add_argument('--scene', dest='scene', default=None,
                        help='load blender scene')

    args = parser.parse_args()

    data_dir = args.data_dir
    hdri_dir = args.hdri_dir

    object_list = glob.glob(os.path.join(data_dir, "*.obj"))
    object_list = [os.path.basename(o) for o in object_list]

    background_list = glob.glob(os.path.join(hdri_dir, "*.hdr"))
    background_list = [os.path.basename(o) for o in background_list]
    L = len(background_list)

    if args.scene is not None:
        bpy.ops.wm.open_mainfile(filepath=args.scene)

    cam = Camera(bpy.context.scene, bpy.data, False)
    cam.set_intrinsics(1616, 1080, 24)
    cam.move(-100, 0, 50, 90, 0, -90)

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

        # Detect available devices
        cuda_devs, cl_devs = bpy.context.preferences.addons['cycles'].preferences.get_devices()
        # Activate "CYCLES" engine and GPU rendering:
        for scene in bpy.data.scenes:
            bpy.context.scene.render.engine = 'CYCLES'
            bpy.data.scenes["Scene"].cycles.device = 'GPU'
            bpy.context.scene.cycles.device = 'GPU'
        # Set the `compute_device_type` and use it
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = "CUDA"
        bpy.context.preferences.addons['cycles'].preferences.devices[0].use = True

        app.run(debug=False, host="0.0.0.0", port=int(args.port))


if __name__ == "__main__":
    main()
