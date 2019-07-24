class Reference(object):
    def __init__(self, genotype, groups, sizes):
        if len(groups) != len(sizes):
            raise ValueError("Inconsistent group and sizes length")
        self._genotype = genotype
        self._groups = groups
        self._ranges = []
        to_skip = 0
        maximum = self._genotype.n_samples
        for size in sizes:
            self._ranges.append((to_skip, min(to_skip + size, maximum)))
            to_skip += size

    @property
    def genotype(self):
        return self._genotype

    @property
    def groups(self):
        return self._groups

    @property
    def ranges(self):
        return self._ranges
