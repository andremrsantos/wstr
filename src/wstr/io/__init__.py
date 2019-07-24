from os.path import join

from .genotype import Genotype
from .reference import Reference
from .qfile import QFile


def get_std_references(resources):
    ancestry_stream = open(join(resources, "ancestry.str"))
    return dict(
        ancestry=Reference(
            Genotype.parse_file(ancestry_stream, "str"),
            groups=["European", "Nat. American", "African"],
            sizes=[290, 246, 200])
    )
