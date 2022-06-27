#!/usr/bin/env python3 romi_bpy
import bpy
import sys
import argparse
import json


def load_obj(fname):
    bpy.ops.object.select_all( action = 'SELECT' )
    bpy.data.objects['Cube']
    bpy.ops.object.delete()

    # Import obj file and make sure it is not splitted by groups or by objects in order to perform
    # further a split by materials
    bpy.ops.import_scene.obj(filepath=fname, use_split_objects=False, use_split_groups=False)
    o = bpy.data.objects[list(bpy.data.objects.keys())[0]]
    bpy.context.view_layer.objects.active = o

def main(fname, out, material_class_corres):

    load_obj(fname)

    bpy.ops.object.mode_set( mode = 'EDIT' )
    bpy.ops.mesh.select_all( action = 'SELECT' )
    bpy.ops.mesh.separate( type = 'MATERIAL' )
    bpy.ops.object.mode_set( mode = 'OBJECT' )

    # After separating, all pieces are selected
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


    bpy.ops.export_scene.obj(filepath=out)

def run():
    try:
        idx = sys.argv.index('--')
        sys.argv = ["null"] + sys.argv[idx+1:]
    except:
        sys.argv = ["null"]
    parser = argparse.ArgumentParser(description='Split an obj file into submeshes')

    parser.add_argument('--classes', dest='classes', default="{}", type=str,
            help='JSON string of the form { "mat_id" : "class_name" }. Renames the materials to selected class names.')

    parser.add_argument('input', metavar='input_file', help="Input file")
    parser.add_argument('output', metavar='output_file', help="Output file")
    args = parser.parse_args()

    args.classes = json.loads(args.classes)
    main(args.input, args.output, args.classes)

if __name__ == "__main__":
    run()
