import os
import cv2

_enabled = False
_root = "."
_image_index = 0
_history = {}

def set_root(rootdir):
    _root = rootdir
    if _root and not os.path.exists(_root):
            os.mkdir(_root)

def enable():
    _enabled = True

def disable():
    _enabled = False

def store_image(name, image):
    if _enabled and _root:
        filepath = _make_image_path(name)
        cv2.imwrite(filepath, image) # TODO: use imageio?
        _history[name] = path

def _make_image_path(name, ext="jpg"):
    path = "%s/%04d-%s.%s" % (_root, _image_index, name, ext)
    _image_index += 1
    return path

def _make_file_path(name, ext="txt"):
    return "%s/%s.%s" % (_root, name, ext)
        
def get_lastpath(name):
    return _history[name]

def write(name, line):
    if _enabled and _root:
        with open(_make_file_path(name), 'a') as f:
            f.write(line)
            f.write("\n")

