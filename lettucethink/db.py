class DB(object):
    def __init__(self):
        pass

    def connect(self, login_data=None):
        raise NotImplmentedError

    def disconnect(self):
        raise NotImplmentedError

    def get_scans(self):
        raise NotImplmentedError

    def get_scan(self, id):
        raise NotImplmentedError

    def create_scan(self, id):
        raise NotImplmentedError


class Scan(object):
    def __init__(self, db, id):
        self.db = db
        self.id = id

    def get_id(self):
        return self.id

    def get_filesets(self):
        raise NotImplmentedError

    def get_fileset(self, id):
        raise NotImplmentedError

    def get_metadata(self, key=None):
        raise NotImplmentedError

    def set_metadata(self, data, value=None):
        raise NotImplmentedError

    def create_fileset(self, id):
        raise NotImplmentedError

    
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
        raise NotImplmentedError

    def get_metadata(self, key=None):
        raise NotImplmentedError

    def set_metadata(self, data, value=None):
        raise NotImplmentedError

    def create_file(self, id):
        raise NotImplmentedError
    
    
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
        raise NotImplmentedError

    def set_metadata(self, data, value=None):
        raise NotImplmentedError

    def write_image(self, type, image):
        raise NotImplmentedError
        
    def write_text(self, type, string):
        raise NotImplmentedError

    def write_bytes(self, type, buffer):
        raise NotImplmentedError

    def import_file(self, path):
        raise NotImplmentedError

    def read_image(self):
        raise NotImplmentedError

    def read_text(self):
        raise NotImplmentedError

    def read_bytes(self):
        raise NotImplmentedError

