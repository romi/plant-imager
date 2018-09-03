

class Document(object):
    def __init__(self, path, width, height):
        self.path = path
        self.printHeader(width, height)
        
    def printHeader(self, width, height):
        with open(self.path, "w") as f:
            f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?><svg xmlns:svg=\"http://www.w3.org/2000/svg\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" version=\"1.0\" width=\"%dpx\" height=\"%dpx\">\n" % (width, height))

    def addImage(self, href, x, y, width, height):
        with open(self.path, "a") as f:
            f.write("    <image xlink:href=\"%s\" x=\"%dpx\" y=\"%dpx\" width=\"%dpx\" height=\"%dpx\" />\n" % (href, x, y, width, height))

    def addPath(self, x, y):
        path = "M %f,%f L" % (x[0], y[0])
        for i in range(1, len(x)):
            path += " %f,%f" % (x[i], y[i])
        with open(self.path, "a") as f:
            f.write("    <path d=\"%s\" id=\"path\" style=\"fill:none;stroke:#0000ce;stroke-width:2;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none\" />" % path)
            
    def close(self):
        self.printFooter()
        
    def printFooter(self):
        with open(self.path, "a") as f:
            f.write("</svg>\n")


   
