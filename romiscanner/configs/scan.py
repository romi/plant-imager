import luigi


class ScanPath(luigi.Config):
    module = luigi.Parameter(default="romiscanner.path")
    class_name = luigi.Parameter()
    kwargs = luigi.DictParameter()