#!/usr/bin/env romi_bpy

import argparse
import json
import sys

from plantimager.blender import split_by_material


def parsing():
    # - Override system arguments positions:
    # Search for the index of the "--" marker (see `VirtualScannerRunner.start()`)
    try:
        idx = sys.argv.index('--')
        sys.argv = ["null"] + sys.argv[idx + 1:]
    except:
        sys.argv = ["null"]
    # Instantiate argument parser:
    parser = argparse.ArgumentParser(description='Split an OBJ mesh file into sub-meshes with Blender.')
    parser.add_argument('input', metavar='input_file', help="Input file")
    parser.add_argument('output', metavar='output_file', help="Output file")
    parser.add_argument('--classes', dest='classes', default="{}", type=str,
                        help='Renames the materials to selected class names with a JSON string as "{"mat_id": "class_name"}".')
    return parser


def main():
    args = parsing().parse_args()
    args.classes = json.loads(args.classes)  # parse the mapping string with JSON parser into a dictionary
    split_by_material(args.input, args.output, args.classes)


if __name__ == "__main__":
    main()
