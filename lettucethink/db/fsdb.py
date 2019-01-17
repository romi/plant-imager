# -*- python -*-
# -*- coding: utf-8 -*-
#
#       File author(s):
#           Peter Hanappe <peter@hanappe.com>
#
#       File contributor(s):
#           Peter Hanappe <peter@hanappe.com>
#           Jonathan Legrand <jonathan.legrand@ens-lyon.fr>
#
#       File maintainer(s):
#           Peter Hanappe <peter@hanappe.com>
#
#       Distributed under XXXXX license.
#
# ------------------------------------------------------------------------------

"""Implementation of a database as a local file structure.

Assuming the following file structure:

2018/
2018/images/
2018/images/rgb0001.jpg
2018/images/rgb0002.jpg

The 2018/files.json file then contains the following structure:

{
    "filesets": [
        {
            "id": "images",
            "files": [
                {
                    "id": "rgb00001",
                    "file": "rgb00001.jpg"
                },
                {
                    "id": "rgb00002",
                    "file": "rgb00002.jpg"
                }
            ]
        }
    ]
}

The metadata of the scan, filesets, and images are stored all as
json objects in a separate directory:

2018/metadata/
2018/metadata/metadata.json
2018/metadata/images.json
2018/metadata/images/rgb0001.json
2018/metadata/images/rgb0002.json
"""

import copy
import json
import os
from shutil import copyfile

import imageio

from lettucethink import error
from lettucethink.db import db_api as db


class DB(db.DB):
    """Class defining the database object `DB`.

    Implementation of a database as a simple file structure with:
      * `images` folder containing image files
      * `metadata` folder containing JSON metadata associated to image files

    Attributes
    ----------
    basedir : str
        path to the base directory containing the database
    scans : list
        list of `Scan` objects found in the database

    Methods
    -------
    connect:
        no connection required here
    disconnect:
        no connection required here
    get_scans:
        get the list of scans saved in the database
    get_scan:
        get a scan save in the database
    create_scan:
        create a new scan object in the database
    """

    def __init__(self, basedir):
        """Database constructor.

        Check given ``basedir`` directory exists and load accessible ``Scan``
        objects.

        Parameters
        ----------
        basedir : str
            root directory of the database

        Examples
        --------
        >>> from lettucethink.fsdb import DB
        >>> db = DB('$HOME/example_path/')

        """
        if not os.path.isdir(basedir):
            raise error.Error("Not a directory: %s" % basedir)
        self.basedir = basedir
        self.scans = _load_scans(self)

    def connect(self, login_data=None):
        """No need to connect to HDD."""
        pass

    def disconnect(self):
        """No need to disconnect from HDD."""
        pass

    def get_scans(self):
        """Get the list of scans saved in the database.

        Returns
        -------
        scans : list
            list of `Scan` objects found in the database
        """
        return self.scans

    def get_scan(self, id):
        """Get a scan saved in the database under given `id`.

        Parameters
        ----------
        id : int
            identifier of the scan to get

        Returns
        -------
        scan : Scan
            `Scan` object associated to given `id`
        """
        for scan in self.scans:
            if scan.get_id() == id:
                return scan
        return None

    def create_scan(self, id):
        """Create a new scan object in the database.

        Parameters
        ----------
        id : int
            identifier of the scan to create

        Returns
        -------
        scan: Scan
            a new scan object from the database
        """
        if not _is_valid_id(id):
            raise error.Error("Invalid id")
        if self.get_scan(id) != None:
            raise error.Error("Duplicate scan name: %s" % id)
        scan = Scan(self, id)
        _make_scan(scan)
        self.scans.append(scan)
        return scan


class Scan(db.Scan):
    """Class defining the scan object `Scan`.

    Implementation of a scan as a list of files with attached metadata.

    Attributes
    ----------
    db : DB
        database where to find the scan
    id : int
        id of the scan in the database `DB`
    metadata : dict
        dictionary of metadata attached to `Scan` object
    filesets : list
        list of `Fileset` attached to `Scan` object

    """

    def __init__(self, db, id):
        super().__init__(db, id)
        self.metadata = None
        self.filesets = []

    def get_filesets(self):
        return self.filesets  # Copy?

    def get_fileset(self, id):
        for fileset in self.filesets:
            if fileset.get_id() == id:
                return fileset
        return None

    def get_metadata(self, key=None):
        return _get_metadata(self.metadata, key)

    def set_metadata(self, data, value=None):
        if self.metadata == None:
            self.metadata = {}
        _set_metadata(self.metadata, data, value)
        _store_scan_metadata(self)

    def create_fileset(self, id):
        if not _is_valid_id(id):
            raise error.Error("Invalid id")
        if self.get_fileset(id) != None:
            raise error.Error("Duplicate fileset name: %s" % id)
        fileset = Fileset(self.db, self, id)
        _make_fileset(fileset)
        self.filesets.append(fileset)
        self.store()
        return fileset

    def store(self):
        _store_scan(self)


class Fileset(db.Fileset):

    def __init__(self, db, scan, id):
        super().__init__(db, scan, id)
        self.metadata = None
        self.files = []

    def get_files(self):
        return self.files

    def get_file(self, id):
        ids = [f.id for f in self.files]
        if id not in ids:
            return None
        return self.files[ids.index(id)]

    def get_metadata(self, key):
        return _get_metadata(self.metadata, key)

    def set_metadata(self, data, value=None):
        if self.metadata == None:
            self.metadata = {}
        _set_metadata(self.metadata, data, value)
        _store_fileset_metadata(self)

    def create_file(self, id):
        file = File(self.db, self, id, None)
        self.files.append(file)
        self.store()
        return file

    def store(self):
        self.scan.store()


class File(db.File):

    def __init__(self, db, fileset, id, filename):
        super().__init__(db, fileset, id)
        self.filename = filename
        self.metadata = None

    def get_metadata(self, key):
        return _get_metadata(self.metadata, key)

    def set_metadata(self, data, value=None):
        if self.metadata == None:
            self.metadata = {}
        _set_metadata(self.metadata, data, value)
        _store_file_metadata(self)

    def write_image(self, type, image):
        filename = _get_filename(self, type)
        path = _file_path(self, filename)
        imageio.imwrite(path, image)
        self.filename = filename
        self.store()

    def write_text(self, type, string):
        filename = _get_filename(self, type)
        path = _file_path(self, filename)
        with open(path, "w") as f:
            f.write(string)
        self.filename = filename
        self.store()

    def write_bytes(self, type, buffer):
        filename = _get_filename(self, type)
        path = _file_path(self, filename)
        with open(path, "wb") as f:
            f.write(buffer)
        self.filename = filename
        self.store()

    def import_file(self, path):
        filename = os.path.basename(path)
        newpath = _file_path(self, filename)
        copyfile(path, newpath)
        self.filename = filename
        self.store()

    def read_image(self):
        path = _file_path(self, self.filename)
        return imageio.imread(path)

    def read_text(self):
        path = _file_path(self, self.filename)
        with open(path, "r") as f:
            return f.read()

    def read_bytes(self):
        path = _file_path(self, self.filename)
        with open(path, "rb") as f:
            return f.read()

    def store(self):
        self.fileset.store()


##################################################################
#
# the ugly stuff...
#

# load the database

def _load_scans(db):
    """Load defined scans in given database object.

    List sub-directories of ``db.basedir``
    """
    scans = []
    names = os.listdir(db.basedir)
    for name in names:
        scan = Scan(db, name)
        if (os.path.isdir(_scan_path(scan))
                and os.path.isfile(_scan_files_json(scan))):
            scan.filesets = _load_scan_filesets(scan)
            scan.metadata = _load_scan_metadata(scan)
            scans.append(scan)
    return scans


def _load_scan_filesets(scan):
    filesets = []
    files_json = _scan_files_json(scan)
    with open(files_json, "r") as f:
        structure = json.load(f)
    filesets_info = structure["filesets"]
    if isinstance(filesets_info, list):
        for fileset_info in filesets_info:
            fileset = _load_fileset(scan, fileset_info)
            filesets.append(fileset)
    else:
        raise error.Error("%s: filesets is not a list" % files_json)
    return filesets


def _load_fileset(scan, fileset_info):
    fileset = _parse_fileset(scan.db, scan, fileset_info)
    fileset.files = _load_fileset_files(fileset, fileset_info)
    fileset.metadata = _load_fileset_metadata(fileset)
    return fileset


def _parse_fileset(db, scan, fileset_info):
    id = fileset_info.get("id")
    if id == None:
        raise error.Error("Fileset: No ID")
    fileset = Fileset(db, scan, id)
    path = _fileset_path(fileset)
    if not os.path.isdir(path):
        raise error.Error(
            "Fileset: Fileset directory doesn't exists: %s" % path)
    return fileset


def _load_fileset_files(fileset, fileset_info):
    files = []
    files_info = fileset_info.get("files", [])
    if isinstance(files_info, list):
        for file_info in files_info:
            file = _load_file(fileset, file_info)
            files.append(file)
    else:
        raise error.Error("files.json: expected a list for files")
    return files


def _load_file(fileset, file_info):
    file = _parse_file(fileset, file_info)
    file.metadata = _load_file_metadata(file)
    return file


def _parse_file(fileset, file_info):
    id = file_info.get("id")
    if id == None:
        raise error.Error("File: No ID")
    filename = file_info.get("file")
    if filename == None:
        raise error.Error("File: No filename")
    file = File(fileset.db, fileset, id, filename)
    path = _file_path(file, filename)
    if not os.path.isfile(path):
        raise error.Error("File: File doesn't exists: %s" % path)
    return file


# load/store metadata from disk

def _load_metadata(path):
    if os.path.isfile(path):
        with open(path, "r") as f:
            r = json.load(f)
        if not isinstance(r, dict):
            raise error.Error("Not a JSON object: %s" % path)
        return r
    else:
        return {}


def _load_scan_metadata(scan):
    return _load_metadata(_scan_metadata_path(scan))


def _load_fileset_metadata(fileset):
    return _load_metadata(_fileset_metadata_path(fileset))


def _load_file_metadata(file):
    return _load_metadata(_file_metadata_path(file))


def _mkdir_metadata(path):
    dir = os.path.dirname(path)
    if not os.path.isdir(dir):
        os.makedirs(dir)


def _store_metadata(path, metadata):
    _mkdir_metadata(path)
    with open(path, "w") as f:
        json.dump(metadata, f, sort_keys=True,
                  indent=4, separators=(',', ': '))


def _store_scan_metadata(scan):
    _store_metadata(_scan_metadata_path(scan),
                    scan.metadata)


def _store_fileset_metadata(fileset):
    _store_metadata(_fileset_metadata_path(fileset),
                    fileset.metadata)


def _store_file_metadata(file):
    _store_metadata(_file_metadata_path(file),
                    file.metadata)


#

def _get_metadata(metadata, key):
    # Do a deepcopy of the return value because we don't want to
    # caller the inadvertedly change the values.
    if metadata == None:
        return {}
    elif key == None:
        return copy.deepcopy(metadata)
    else:
        return copy.deepcopy(metadata.get(str(key)))


def _set_metadata(metadata, data, value):
    if isinstance(data, str):
        if value == None:
            raise error.Error("No value given for key %s" % data)
        # Do a deepcopy of the value because we don't want to caller
        # the inadvertedly change the values.
        metadata[data] = copy.deepcopy(value)
    elif isinstance(data, dict):
        for key, value in data.items():
            _set_metadata(metadata, key, value)
    else:
        raise error.Error("Invalid key: ", data)


#

def _make_fileset(fileset):
    path = _fileset_path(fileset)
    if not os.path.isdir(path):
        os.makedirs(path)


def _make_scan(scan):
    path = _scan_path(scan)
    if not os.path.isdir(path):
        os.makedirs(path)


# paths

def _get_filename(file, type):
    return file.id + "." + type


def _scan_path(scan):
    return os.path.join(scan.db.basedir,
                        scan.id)


def _fileset_path(fileset):
    return os.path.join(fileset.db.basedir,
                        fileset.scan.id,
                        fileset.id)


def _file_path(file, filename):
    return os.path.join(file.db.basedir,
                        file.fileset.scan.id,
                        file.fileset.id,
                        filename)


def _scan_files_json(scan):
    return os.path.join(scan.db.basedir,
                        scan.id,
                        "files.json")


def _scan_metadata_path(scan):
    return os.path.join(scan.db.basedir,
                        scan.id,
                        "metadata",
                        "metadata.json")


def _fileset_metadata_path(fileset):
    return os.path.join(fileset.db.basedir,
                        fileset.scan.id,
                        "metadata",
                        fileset.id + ".json")


def _file_metadata_path(file):
    return os.path.join(file.db.basedir,
                        file.fileset.scan.id,
                        "metadata",
                        file.fileset.id,
                        file.id + ".json")


# store a scan to disk

def _file_to_dict(file):
    return {"id": file.get_id(), "file": file.filename}


def _fileset_to_dict(fileset):
    files = []
    for f in fileset.get_files():
        files.append(_file_to_dict(f))
    return {"id": fileset.get_id(), "files": files}


def _scan_to_dict(scan):
    filesets = []
    for fileset in scan.get_filesets():
        filesets.append(_fileset_to_dict(fileset))
    return {"filesets": filesets}


def _store_scan(scan):
    structure = _scan_to_dict(scan)
    files_json = _scan_files_json(scan)
    with open(files_json, "w") as f:
        json.dump(structure, f, sort_keys=True,
                  indent=4, separators=(',', ': '))


#

def _is_valid_id(id):
    return True  # haha  (FIXME!)


##################################################################
if __name__ == '__main__':
    # Test
    import sys
    import datetime

    db = DB(sys.argv[1])

    for scan in db.get_scans():
        print("Scan '%s'" % scan.get_id())
        for fileset in scan.get_filesets():
            print("- Fileset '%s'" % fileset.get_id())
            for file in fileset.get_files():
                print("      File '%s'" % file.get_id())
                file.set_metadata("foo", "bar")
                print(file.get_metadata("foo"))
                print(file.get_metadata("fox"))

    now = datetime.datetime.now()
    id = now.strftime("%Y%m%d-%H%M%S")

    scan = db.create_scan(id)
    scan.set_metadata("hardware",
                      {"version": "0.1", "camera": "RX0",
                       "gimbal": "dynamixel"})
    scan.set_metadata("biology", {"species": "A. thaliana", "plant": "GT1"})
    fileset = scan.create_fileset("images")
    file = fileset.create_file("00001")
    file.write_text("jpg", "tada")
