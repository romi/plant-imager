import luigi


class VirtualPlantConfig(luigi.Config):
    classes = luigi.DictParameter(default={
        "Color_0" : "flower",
        "Color_1" : "leaf",
        "Color_2" : "pedicel",
        "Color_3" : "stem",
        "Color_4" : "fruit"
    })