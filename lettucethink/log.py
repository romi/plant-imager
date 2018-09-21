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

