from sortedcontainers import SortedSet

FORMAT_DELIMITER = dict(csv=",", txt="\t", tsv="\t")
FIX_LOCUS = dict(
    MID675="MID675", MDI1391="MID1391",
    MDI1785="MID1785", MID1636="MID1632")


def _sanitize_locus(locus):
    if locus in FIX_LOCUS:
        return FIX_LOCUS[locus]
    return locus


def _sanitize_name(name):
    return name.replace(" ", "_")


def _sanitize_genotype(geno):
    geno = geno.strip()
    if len(geno) == 2:
        return (geno[0], geno[1])
    elif geno == "-9" or geno == "":
        return ("-9", "-9")
    else:
        raise ValueError("Invalid genotype format")


class Genotype(object):
    def __init__(self):
        self._samples = []
        self._loci = SortedSet([])
        self._data = dict()

    def add_loci(self, loci):
        self._loci = self._loci.union(loci)
        return self

    def add(self, sample, loci, genotype):
        if len(loci) != len(genotype):
            raise ValueError("Inconsistent loci and genotype sizes")
        self.add_loci(loci)  # append loci if necessary
        self._samples.append(sample)
        self._data[sample] = dict()
        for i in range(len(loci)):
            self._data[sample][loci[i]] = genotype[i]
        return self

    def merge(self, other):
        if type(self) != type(other):
            raise ValueError("Must be of type `Genotype` to merge")
        self._loci = self._loci.union(other.loci)
        self._samples += other.samples
        self._data.update(other._data)
        return self

    @property
    def loci(self):
        return self._loci

    @property
    def n_loci(self):
        return len(self._loci)

    @property
    def samples(self):
        return self._samples

    @property
    def n_samples(self):
        return len(self._samples)

    def get(self, sample, loci):
        if (sample not in self._samples) or (loci not in self._loci):
            raise KeyError()
        return self._data[sample].get(loci, ("-9", "-9"))

    def write(self, stream):
        print("", " ".join(self.loci), file=stream)
        for sample, geno in self:
            line0 = [sample]
            line1 = [sample]
            for locus in self.loci:
                if locus not in geno:
                    line0.append("-9")
                    line1.append("-9")
                    continue
                line0.append(geno[locus][0])
                line1.append(geno[locus][1])
            print(" ".join(line0), file=stream)
            print(" ".join(line1), file=stream)

    def __iter__(self):
        for sample in self._samples:
            yield sample, self._data[sample]

    @classmethod
    def combine(cls, one, other):
        return cls().merge(one).merge(other)

    @classmethod
    def parse_str(cls, stream):
        genotype = cls()
        loci = next(stream).rstrip().split()
        loci = [_sanitize_locus(l) for l in loci]
        while True:
            line0 = next(stream, None)
            line1 = next(stream, None)
            if line0 is None or line1 is None:
                break
            name, *gen0 = line0.rstrip().split()
            gen1 = line1.rstrip().split()[1:]
            name = _sanitize_name(name)
            geno = [value for value in zip(gen0, gen1)]
            genotype.add(name, loci, geno)
        return genotype

    @classmethod
    def parse_delim(cls, stream, delimiter=None):
        genotype = cls()
        loci = next(stream).rstrip("\n").split(delimiter)[1:]
        loci = [_sanitize_locus(l) for l in loci]
        for line in stream:
            name, *geno = line.strip("\n").split(delimiter)
            name = _sanitize_name(name)
            geno = [_sanitize_genotype(g) for g in geno]
            genotype.add(name, loci, geno)
        return genotype

    @classmethod
    def parse_file(cls, stream, format="txt"):
        if format == "str":
            return cls.parse_str(stream)
        elif format in FORMAT_DELIMITER:
            return cls.parse_delim(stream, FORMAT_DELIMITER[format])
        else:
            raise ValueError("Invalid file format")
