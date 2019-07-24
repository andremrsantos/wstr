from statistics import mean

class QFile (object):
    def __init__(self):
        self._samples = []
        self._data = None
        self._n = 0
    
    def add(self, name, ancestry):
        if self._n == 0:
            self._n = len(ancestry)
            self._data = [[] for _ in range(self._n)]
        elif self._n != len(ancestry):
            raise ValueError()

        self._samples.append(name)
        for i in range(self._n):
            self._data[i].append(ancestry[i])

    def write(self, stream):
        for sample, genotype in self:
            print(sample, *genotype, sep="\t", file=stream)

    def to_barplot(self):
        if self._data is None:
            return []
        names = self._samples
        return [
            dict(x=names, y=self._data[i], type="bar", name="Pop #%03d" % i)
            for i in range(self.n_ancestries)
        ]

    def summarise(self, labels, ranges, func=mean):
        to_exclude = set([])
        for j in range(len(labels)):
            rg = ranges[j]
            to_exclude = to_exclude.union(list(range(*rg)))
            ancestry = [
                func(self._data[i][rg[0]:rg[1]])
                for i in range(self.n_ancestries)
            ]
            self.add(labels[j], ancestry)
        new_data = [[] for _ in range(self.n_ancestries)]
        new_sample = []
        for i in range(self.n_samples):
            if i in to_exclude:
                continue
            new_sample.append(self._samples[i])
            for j in range(self.n_ancestries):
                new_data[j].append(self._data[j][i])
        self._data = new_data
        self._samples = new_sample
        return self

    @property
    def samples(self):
        return self._samples

    @property
    def n_samples(self):
        return len(self._samples)

    @property
    def n_ancestries(self):
        return self._n

    def get_ancestry(self, i):
        if i >= self._n:
            raise IndexError()
        return self._data[i]

    def __iter__(self):
        for i in range(self.n_samples):
            yield (
                self._samples[i],
                [self._data[j][i] for j in range(self.n_ancestries)]
            )

    @classmethod
    def parse(cls, stream):
        qfile = cls()
        # Skip until ancestry table
        while not next(stream).startswith("Inferred ancestry"):
            pass
        next(stream) # skip header
        line = next(stream)
        while line != "":
            values = line.rstrip().split()
            if len(values) == 0:
                break
            name = values[1]
            ancestry = [float(v) for v in values[4:]]
            qfile.add(name, ancestry)
            # Move to next line
            line = next(stream)
        return qfile

    @classmethod
    def open(cls, stream):
        qfile = cls()
        for line in stream:
            values = line.rstrip().split("\t")
            name = values[0]
            ancestry = [float(v) for v in values[1:]]
            qfile.add(name, ancestry)
        return qfile