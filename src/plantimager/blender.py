#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from contextlib import redirect_stderr
from contextlib import redirect_stdout
from math import pi
from random import randint

import bpy
import numpy as np
from imageio import v3 as iio
from mathutils import Matrix

from plantimager.log import configure_logger

logger = configure_logger(__name__)


def _get_log_filepath(path):
    """Returns a path for the blender log file.

    Parameters
    ----------
    path : str
        A file path or directory to use as blender log file location.

    Returns
    -------
    str
        The blender log file path.
    """
    from pathlib import Path
    path = Path(path)
    if path.is_file():
        path = path.parent
    return str(path.joinpath('blender.log'))


def check_engine(engine="CYCLES"):
    """Check the rendering engine.

    Parameters
    ----------
    engine : {"CYCLES", "BLENDER_EEVEE", "BLENDER_WORKBENCH"}, optional
        The name of the rendering engine to use.
        Defaults to ``CYCLES``.
    """
    engine = engine.upper()
    try:
        assert bpy.context.scene.render.engine == engine
    except AssertionError:
        logger.warning(f"The selected engine is not '{engine}', it is '{bpy.context.scene.render.engine}'!")
    return


def load_obj(fname, log=None):
    """Load a mesh in Blender.

    Parameters
    ----------
    fname : str
        The file path to the mesh object to load in Blender.
    log : str, optional
        The blender log file path.
    """
    if log is None:
        log = _get_log_filepath(fname)

    def _clean_scene():
        # Start by selecting all objects from initialized scene (with a cube) and remove them all:
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

    def _open_obj(fname):
        # Load the mesh in Blender:
        bpy.ops.import_scene.obj(filepath=fname)

    with open(log, mode="a") as f:
        # Redirect blender outputs to a log file:
        with redirect_stdout(f), redirect_stderr(f):
            _clean_scene()
            _open_obj(fname)

    # List all imported objects & set them as active:
    o = bpy.data.objects[list(bpy.data.objects.keys())[0]]
    bpy.context.view_layer.objects.active = o
    return


def split_by_material(fname, out, material_class_corres):
    """Mesh splitting function.

    Parameters
    ----------
    fname : str
        The file path to the mesh object to load in Blender.
    out : str
        The file path to us to export the cleaned mesh object.
    material_class_corres : dict
        A renaming dictionary, map LPY class names to semantic class names.
    """
    check_engine()
    log = _get_log_filepath(fname)
    load_obj(fname, log=log)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='MATERIAL')
    bpy.ops.object.mode_set(mode='OBJECT')

    # After separating, all pieces are selected and named accordingly:
    for o in bpy.context.selected_objects:
        # Remove x rotation from LPY
        o.rotation_euler[0] = 0
        # Rename object by the material applied to it
        if o.active_material.name in material_class_corres:
            class_name = material_class_corres[o.active_material.name]
            o.name = class_name
            o.active_material.name = class_name
        else:
            o.name = o.active_material.name

    # Export the mesh:
    with open(log, mode="a") as f:
        with redirect_stdout(f), redirect_stderr(f):
            bpy.ops.export_scene.obj(filepath=out)

    return


def clean_mesh(fname, out):
    """Mesh cleaning function.

    Parameters
    ----------
    fname : str
        The file path to the mesh object to load in Blender.
    out : str
        The file path to us to export the cleaned mesh object.
    """
    check_engine()
    log = _get_log_filepath(fname)
    load_obj(fname, log=log)

    def _clean_obj(out):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        # Remove vertices that are too close:
        bpy.ops.mesh.remove_doubles(threshold=0.01)
        # Close any hole in the mesh:
        bpy.ops.mesh.fill_holes(0)
        bpy.ops.mesh.set_normals_from_faces()
        # Export the mesh:
        bpy.ops.export_scene.obj(filepath=out)

    # Redirect blender outputs to a log file:
    with open(log, mode="a") as f:
        with redirect_stdout(f), redirect_stderr(f):
            _clean_obj(out)

    return


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
    def add_displacement(self, class_name):
        for o in self.data.objects:
            if class_name in o.name:
                displace_modifier = o.modifiers.new(name="Displace.01", type='DISPLACE')
                tex = self.data.textures.new("Displace.01", 'CLOUDS')
                tex.noise_scale = 2.0
                displace_modifier.texture = tex
