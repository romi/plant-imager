#!/usr/bin/env python3 romi_bpy
print("hello")
import bpy
from sys import argv


def load_obj(fname):
    bpy.ops.object.select_all( action = 'SELECT' )
    bpy.data.objects['Cube']
    bpy.ops.object.delete()
   
    bpy.ops.import_scene.obj(filepath=fname)
    o = bpy.data.objects[list(bpy.data.objects.keys())[0]]
    bpy.context.view_layer.objects.active = o

def main(fname, out):
    load_obj(fname)
    bpy.ops.object.select_all( action = 'SELECT' )

    for o in bpy.data.objects.values():
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.mode_set( mode = 'EDIT' )
        bpy.ops.mesh.select_all( action = 'SELECT' )
        bpy.ops.mesh.remove_doubles(threshold=0.01)
        bpy.ops.mesh.fill_holes(0)
        bpy.ops.mesh.set_normals_from_faces()
    bpy.ops.export_scene.obj(filepath=out)

def run():
    main(argv[-2], argv[-1])

if __name__ == "__main__":
    run()
