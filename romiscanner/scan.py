import luigi

from romidata.tasks.db import FilesetExists


class ObjFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "data"


class HdriFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "hdri"


class SceneFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "scenes"


class PaletteFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "palette"


