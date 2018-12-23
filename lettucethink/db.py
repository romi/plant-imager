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
class DB(object):
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

    def get_file(self, id):
        raise NotImplementedError

    def get_metadata(self, key=None):
        raise NotImplementedError

    def set_metadata(self, data, value=None):
        raise NotImplementedError

    def create_file(self, id):
        raise NotImplementedError
    
    
class File(object):
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

