#!/usr/bin/env romi_bpy

from sys import argv

from plantimager.blender import clean_mesh


def main():
    clean_mesh(argv[-2], argv[-1])


if __name__ == "__main__":
    main()
