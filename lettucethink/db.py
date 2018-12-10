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


"""
API for the database module in the ROMI project.
"""


class DB(object):
    """Class defining the database object `DB`.

    Abstract class defining the API used to communicate with a database in the
    ROMI project.

    Methods
    -------
    connect:
        connect to the database
    disconnect:
        disconnect from the database
    get_scans:
        get a list of scans save in the database
    get_scan:
        get a scan save in the database
    create_scan:
        create a new scan object in the database
    """

    def __init__(self):
        pass

    def connect(self, login_data=None):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def get_scans(self):
        raise NotImplementedError

    def get_scan(self, id):
        raise NotImplementedError

    def create_scan(self, id):
        raise NotImplementedError


class Scan(object):
    """Class defining the scan object `Scan`.

    Abstract class defining the API used to represent a scan in the ROMI project.

    Attributes
    ----------
    db : DB
        database where to find the scan
    id : int
        id of the scan in the database `DB`

    Methods
    -------

    """

    def __init__(self, db, id):
        self.db = db
        self.id = id

    def get_id(self):
        return self.id

    def get_filesets(self):
        raise NotImplementedError

    def get_fileset(self, id):
        raise NotImplementedError

    def get_metadata(self, key=None):
        raise NotImplementedError

    def set_metadata(self, data, value=None):
        raise NotImplementedError

    def create_fileset(self, id):
        raise NotImplementedError


class Fileset(object):
    """Class defining a set of files `Fileset` contained in a `Scan`.

    Abstract class defining the API used to represent a set of files in the ROMI
    project.

    Attributes
    ----------
    db : DB
        database where to find the scan
    id : int
        id of the scan in the database `DB`
    scan : Scan
        scan containing the set of files

    Notes
    -----
    Files can be 2D images, RGB pictures, ...
    """

    def __init__(self, db, scan, id):
        self.db = db
        self.scan = scan
        self.id = id

    def get_id(self):
        return self.id

    def get_db(self):
        return self.db

    def get_scan(self):
        return self.scan

    def get_files(self):
        raise NotImplementedError

    def get_metadata(self, key=None):
        raise NotImplementedError

    def set_metadata(self, data, value=None):
        raise NotImplementedError

    def create_file(self, id):
        raise NotImplementedError


class File(object):
    """Class defining a file `File` contained in a `Fileset`.

    Abstract class defining the API used to represent a file in the ROMI project.

    Attributes
    ----------
    db : DB
        database where to find the scan
    id : int
        id of the scan in the database `DB`
    fileset : Fileset
        set of file containing the file
    """

    def __init__(self, db, fileset, id):
        self.db = db
        self.fileset = fileset
        self.id = id

    def get_id(self):
        return self.id

    def get_db(self):
        return self.db

    def get_fileset(self):
        return self.fileset

    def get_metadata(self, key=None):
        raise NotImplementedError

    def set_metadata(self, data, value=None):
        raise NotImplementedError

    def write_image(self, type, image):
        raise NotImplementedError

    def write_text(self, type, string):
        raise NotImplementedError

    def write_bytes(self, type, buffer):
        raise NotImplementedError

    def import_file(self, path):
        raise NotImplementedError

    def read_image(self):
        raise NotImplementedError

    def read_text(self):
        raise NotImplementedError

    def read_bytes(self):
        raise NotImplementedError
