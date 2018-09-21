
from lettucethink import hal, utils, path
import os
import math
import time


def archive_scan(files, output="scan.zip"):
    utils.create_archive(files, output)
        
        
def animate_scan(files, output="scan.gif"):
    utils.create_gif(files, output)

    
class Scanner(object):
    def __init__(self, cnc, gimbal, camera, scan_dir="scan"):
        self.cnc = cnc
        self.gimbal = gimbal
        self.camera = camera
        self.set_scan_dir(scan_dir)
        self.reset_files()
        self.set_default_filetype("tif")
        
    def get_position(self):
        x, y, z = self.cnc.get_position()
        pan, tilt = self.gimbal.get_position()
        return {'x': x, 'y': y, 'z': z,
                'pan': pan, 'tilt': tilt}

    
    def set_scan_dir(self, d):
        self.scan_dir = d
        if not os.path.exists(self.scan_dir):
            os.mkdir(self.scan_dir)
        

    def get_scan_dir(self, d):
        return self.scan_dir
        

    def get_scan_files(self):
        return self.files
                

    def reset_files(self):
        self.files = []
        self.scan_count = 0
                

    def set_default_filetype(self, filetype):
        self.default_filetype = filetype

        
    def get_default_filetype(self):
        return self.default_filetype
                

    def do_circular_scan(self, xc, yc, radius, num_points, z=None, tilt=None, filetype=None):
        if z is None:
            x, y, z = self.cnc.get_position()
        if tilt is None:
            pan, tilt = self.gimbal.get_position()
        circle = path.circle(xc, yc, z, tilt, radius, num_points)
        return self.scan(circle, filetype=filetype)

        
    def scan(self, path, filetype=None):
        """
        Scans along a given path 
        :param path: list of 5-tuples (x,y,z,pan,tilt)
        :param filetype: file format to store the images. Default: "tif" (TIFF)
        """
        nc = len(path)
        csvpath = os.path.join(self.scan_dir, "scan.csv")
        csvfile = open(csvpath, mode = 'w') 
        csvfile.write(self._format_csv_header())

        for i in range(nc):
            (x, y, z, pan, tilt) = path[i]
            #x, y, z = self.xyz_clamp(x, y, z) TODO
            files = self.scan_at(x, y, z, pan, tilt, filetype=filetype)
            csvfile.write(self._format_csv_line(files))
            self.files.extend(files)
            self.scan_count += 1

        csvfile.close()
        self.files.append(csvpath)

        self.gimbal.moveto(0, 0) # FIXME
        self.cnc.moveto(*path[0][0:3])
        
        return self.files

    
    def scan_at(self, x, y, z, pan, tilt, filetype=None, suffix=None, wait_time=1):
        """
        Moves arm to position (x,y,z,pan,tilt) and acquire data from camera.
        :param x: position x
        :param y: position y
        :param z: position z
        :param pan: orientation pan
        :param tilt: orientation tilt
        :param filetype: file format to store the images. If not specified, the default file type is used.
        :param suffix: will be added to the file name
        :param wait_time: time to wait after movement before taking the shot
        """
        self.is_busy = True
        if self.cnc.async_enabled():
            self.cnc.moveto_async(x, y, z)
            self.gimbal.moveto_async(pan, tilt)
            self.cnc.wait()
            self.gimbal.wait()
        else:
            self.cnc.moveto(x, y, z)
            self.gimbal.moveto(pan, tilt)

        if filetype == None:
            filetype = self.default_filetype
        if suffix == None:
            suffix="%03d" % self.scan_count    

        time.sleep(wait_time)

        filelist = self.camera.store_views(self.scan_dir, filetype, suffix)

        self.is_busy = False
        return filelist

    
    def _format_csv_header(self):
        s = "x\ty\tz\tpan\ttilt\t"
        s += '\t'.join(v for v in self.camera.get_views())
        s += '\n'
        return s


    def _format_csv_line(self, files):
        d = self.get_position()
        s = (str(d['x']) + "\t"
             + str(d['y']) + "\t"
             + str(d['z']) + '\t'
             + str(d['pan']) + '\t'
             + str(d['tilt']) + '\t')
        s += '\t'.join(f for f in files)
        s += "\n"
        return s

