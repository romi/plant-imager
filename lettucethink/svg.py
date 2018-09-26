import xml.etree.ElementTree as ET

class SVGDocument(object):
    def __init__(self, path, width, height):
        self.path = path
        self.print_header(width, height)
        

    def print_header(self, width, height):
        with open(self.path, "w") as f:
            f.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?><svg xmlns:svg=\"http://www.w3.org/2000/svg\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" version=\"1.0\" width=\"%dpx\" height=\"%dpx\">\n" % (width, height))

            
    def add_image(self, href, x, y, width, height, translate=False, rotate=False):
        transform = ""
        if translate:
            transform = "translate(%f, %f)" % (translate[0], translate[1])
        if rotate:
            transform = transform + " rotate(%f, %f, %f) " % (rotate[0], rotate[1], rotate[2])
        with open(self.path, "a") as f:
            f.write("    <image xlink:href=\"%s\" x=\"%dpx\" y=\"%dpx\" width=\"%dpx\" height=\"%dpx\" transform=\"%s\" />\n" % (href, x, y, width, height, transform))

            
    def add_path(self, x, y):
        path = "M %f,%f L" % (x[0], y[0])
        for i in range(1, len(x)):
            path += " %f,%f" % (x[i], y[i])
        with open(self.path, "a") as f:
            f.write("    <path d=\"%s\" id=\"path\" style=\"fill:none;stroke:#0000ce;stroke-width:2;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:4;stroke-opacity:1;stroke-dasharray:none\" />" % path)

            
    def close(self):
        self.print_footer()

        
    def print_footer(self):
        with open(self.path, "a") as f:
            f.write("</svg>\n")


def extract_path(file):
    tree = ET.parse(file)
    root = tree.getroot()
    path = root.find('{http://www.w3.org/2000/svg}path')
    d = path.attrib['d']
    components = d.split()

    state = 0
    xi, yi = 0, 0
    x, y = [], []
    for component in components:
        if component == 'M':
            state = "M"
        elif component == 'm':
            state = "m"
        elif component == 'L':
            state = "L"
        elif component == 'l':
            state = "l"
        elif component == 'H':
            state = "H"
        elif component == 'h':
            state = "h"
        elif component == 'V':
            state = "V"
        elif component == 'v':
            state = "v"
        elif component == 'Z':
            state = "Z"
        elif component == 'z':
            state = "z"
        elif component == 'C':
            state = -1
        elif component == 'c':
            state = -1
        elif component == 'S':
            state = -1
        elif component == 's':
            state = -1
        elif component == 'T':
            state = -1
        elif component == 't':
            state = -1
        elif component == 'Q':
            state = -1
        elif component == 'q':
            state = -1
        elif component == 'A':
            state = -1
        elif component == 'a':
            state = -1
        else:
            numbers = component.split(",")
            coordinates = [float(i) for i in numbers]
            if state == "M":
                xi = coordinates[0]
                yi = coordinates[1]
            elif state == "m":
                xi = xi + coordinates[0]
                yi = yi + coordinates[1]
            elif state == "L":
                xi = coordinates[0]
                yi = coordinates[1]
            elif state == "l":
                xi = xi + coordinates[0]
                yi = yi + coordinates[1]
            elif state == "H":
                xi = coordinates[0]
            elif state == "h":
                xi = xi + coordinates[0]
            elif state == "V":
                yi = coordinates[0]
            elif state == "v":
                yi = yi + coordinates[0]
            elif state == "Z" or state == "z":
                xi = x[0]
                yi = y[0]
            x.append(xi)
            y.append(yi)
        if state == -1:
            print("An error occured")

    return x, y
