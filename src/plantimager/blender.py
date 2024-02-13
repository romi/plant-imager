#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from contextlib import redirect_stderr
from contextlib import redirect_stdout

import bpy

from romitask.log import configure_logger

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
