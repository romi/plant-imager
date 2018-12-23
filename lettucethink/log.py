"""

    lettucethink-python - Python tools the LettuceThink robot

    Copyright (C) 2018 Sony Computer Science Laboratories
    Authors: D. Colliaux, T. Wintz, P. Hanappe
  
    This file is part of lettucethink-python.

    lettucethink-python is free software: you can redistribute it
    and/or modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation, either
    version 3 of the License, or (at your option) any later version.

    lettucethink-python is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied
    warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with lettucethink-python.  If not, see
    <https://www.gnu.org/licenses/>.

"""    
import os
import cv2

_enabled = False
_root = "."
_image_index = 0
_history = {}

def set_root(rootdir):
    global _root
    _root = rootdir
    if _root and not os.path.exists(_root):
        os.mkdir(_root)

def is_enabled():
    global _enabled
    return _enabled

def enable():
    global _enabled
    _enabled = True

def disable():
    global _enabled
    _enabled = False

def store_image(name, image):
    global _enabled, _root, _history
    if _enabled and _root:
        filepath = make_image_path(name)
        cv2.imwrite(filepath, image) # TODO: use imageio?
        _history[name] = filepath
        print("Log: wrote %s" % filepath)

def make_image_path(name, ext="jpg"):
    global _root, _image_index
    path = "%s/%04d-%s.%s" % (_root, _image_index, name, ext)
    _image_index += 1
    return path

def make_file_path(name, ext="txt"):
    global _root
    return "%s/%s.%s" % (_root, name, ext)
        
def get_last_path(name):
    global _history
    return _history[name]

def write(name, line):
    global _enabled, _root
    if _enabled and _root:
        with open(make_file_path(name), 'a') as f:
            f.write(line)
            f.write("\n")

