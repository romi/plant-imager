from romidata.task import RomiTask
from romidata import io
from romidata.task import FilesetExists

import tempfile
import luigi
import os

class LpyFileset(FilesetExists):
    scan_id = luigi.Parameter()
    fileset_id = "lpy"

class VirtualPlant(RomiTask):
    upstream_task = LpyFileset
    lpy_file_id = luigi.Parameter()
    metadata = luigi.ListParameter(default=["angles", "internodes"])

    def run(self):
        from openalea import lpy
        from openalea.plantgl import all

        with tempfile.TemporaryDirectory() as tmpdir:
            x = self.input().get().get_file(self.lpy_file_id)
            tmp_filename = os.path.join(tmpdir, "f.lpy")
            with open(tmp_filename, "wb") as f:
                f.write(x.read_raw())

            lsystem = lpy.Lsystem(tmp_filename)
            for lstring in lsystem:
                t = all.PglTurtle()
                lsystem.turtle_interpretation(lstring, t)
            scene = t.getScene()

            output_file = self.output_file()
            fname = os.path.join(tmpdir, "plant.obj")
            scene.save(fname)
            output_file.import_file(fname)

        for m in self.metadata:
            m_val = lsystem.context().globals()[m]
            output_file.set_metadata(m, m_val)

