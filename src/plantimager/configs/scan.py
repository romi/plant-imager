import luigi


class ScanPath(luigi.Config):
    module = luigi.Parameter(default="plantimager.path")
    class_name = luigi.Parameter()
    kwargs = luigi.DictParameter()