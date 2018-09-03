import cv2
import os

class ImageLogger(object):
    def __init__(self, root=False):
        self.root = root
        self.index = 0
        self.history = {}
        if root and not os.path.exists(root):
            os.mkdir(root)

    def storeImage(self, name, image):
        if self.root:
            filepath = self.makePath(name)
            cv2.imwrite(filepath, image)

    def makePath(self, name, ext="jpg"):
        if self.root:
            path = "%s/%02d-%s.%s" % (self.root, self.index, name, ext)
            self.index += 1
            self.history[name] = path
            return path
        else:
            return None

    def getPath(self, name):
        return self.history[name]

    def isLogging(self):
        return self.root != False

    def setRoot(self, root):
        self.root = root

    def reset(self):
        this.index = 0

    def incrementIndex(self):
        this.index += 1
