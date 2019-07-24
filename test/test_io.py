import pytest

from io import StringIO
from wstr import io

EXPECTED = dict(
    X=dict(
        A=('1', '1'), B=('1', '1'), C=('2', '2'),
        D=('1', '2'), E=('-9', '-9')),
    Y=dict(
        A=('2', '2'), B=('1', '1'), C=('1', '2'),
        D=('-9', '-9'), E=('1', '2'))
)
## File Streams
STR_STREAM = [
    " A B C D E\n",
    "X 1 1 2 1 -9\n",
    "X 1 1 2 2 -9\n",
    "Y 2 1 1 -9 1\n",
    "Y 2 1 2 -9 2\n"
]
CSV_STREAM = [
    "S,A,B,C,D,E\n",
    "X,11,11,22,12,\n",
    "Y,22,11,12,,12\n"
]
TSV_STREAM = [
    "S\tA\tB\tC\tD\tE\n",
    "X\t11\t11\t22\t12\t\n",
    "Y\t22\t11\t12\t\t12\n"
]


class TestGenotype(object):
    def test_create_empty(self):
        genotype = io.Genotype()
        assert genotype.n_loci == 0
        assert genotype.n_samples == 0

    def test_add_loci(self):
        genotype = io.Genotype()
        loci = ["A", "B", "C", "D"]

        genotype.add_loci(loci)
        # Check includes all
        for locus in loci:
            assert locus in genotype.loci

    def test_add_unique_loci(self):
        genotype = io.Genotype()
        loci = ["A", "B", "C", "D"]

        genotype.add_loci(loci)
        genotype.add_loci(loci)
        assert genotype.n_loci == 4

    def test_add(self):
        genotype = io.Genotype()
        sample = "S0"
        loci = ["A", "B", "C", "D"]
        data = [[0, 1], [0, 2], [0, 1], [0,2]]

        genotype.add(sample, loci, data)
        assert genotype.n_samples == 1
        assert genotype.n_loci == 4

    def test_iterate_genotypes(self):
        genotype = io.Genotype()
        name = "S0"
        loci = ["A", "B", "C", "D"]
        data = [[1, 1], [1, 2], [1, 1], [2, 2]]
        genotype.add(name, loci, data)

        count = 0
        for sample, genotype in genotype:
            assert sample == name # assert sample is the given
            assert genotype == dict(A=[1, 1], B=[1, 2], C=[1, 1], D=[2, 2])
            count += 1
        assert count == 1 # Iterates over one item

    def test_parse_file_raise_error(self):
        with pytest.raises(ValueError):
            io.Genotype.parse_file(iter([]), format = "invalid")

    def check_parsed(self, genotype):
        assert genotype.n_loci == 5
        assert genotype.n_samples == 2
        for sample, genotype in genotype:
            assert sample in EXPECTED
            assert genotype == EXPECTED[sample]

    def test_parse_str(self):
        genotype = io.Genotype.parse_file(iter(STR_STREAM), 'str')
        self.check_parsed(genotype)

    def test_parse_csv(self):
        genotype = io.Genotype.parse_file(iter(CSV_STREAM), 'csv')
        self.check_parsed(genotype)
    
    def test_parse_tsv(self):
        genotype = io.Genotype.parse_file(iter(TSV_STREAM), 'tsv')
        self.check_parsed(genotype)

    def test_write(self):
        genotype = io.Genotype()
        loci = ["A", "B", "C", "D", "E"]
        genotype.add("X", loci, [('1', '1'), ('1', '1'),
                                 ('2', '2'), ('1', '2'), ('-9', '-9')])
        genotype.add("Y", loci, [('2', '2'), ('1', '1'), ('1', '2'),
                                 ('-9', '-9'), ('1', '2')])
        stream = StringIO("")
        expected = "".join(STR_STREAM)
        genotype.write(stream)
        assert stream.getvalue() == expected

    def test_merge_genotype_raises_error(self):
        genotype = io.Genotype()
        with pytest.raises(ValueError):
            genotype.merge(1)
    
    def test_merge_genotypes(self):
        expected = dict(
            X=dict(A=('1', '1'), B=('1', '2'), C=('2', '2')),
            Y=dict(A=('1', '1'), D=('1', '2'), E=('2', '2'))
        )
        one = io.Genotype()
        one.add('X', ['A', 'B', 'C'], [('1', '1'), ('1', '2'), ('2', '2')])
        other = io.Genotype()
        other.add('Y', ['A', 'D', 'E'], [('1', '1'), ('1', '2'), ('2', '2')])

        one.merge(other)
        assert one.n_loci == 5
        assert one.n_samples == 2
        for sample, geno in one:
            assert sample in expected
            assert geno == expected[sample]

    def test_combine(self):
        expected = dict(
            X=dict(A=('1', '1'), B=('1', '2'), C=('2', '2')),
            Y=dict(A=('1', '1'), D=('1', '2'), E=('2', '2'))
        )
        one = io.Genotype()
        one.add('X', ['A', 'B', 'C'], [('1', '1'), ('1', '2'), ('2', '2')])
        other = io.Genotype()
        other.add('Y', ['A', 'D', 'E'], [('1', '1'), ('1', '2'), ('2', '2')])

        merged = io.Genotype.combine(one, other)
        # Check for side effects
        assert one.n_loci == 3 and other.n_loci == 3
        assert one.n_samples == 1 and other.n_samples == 1
        assert merged.n_loci == 5
        assert merged.n_samples == 2
        for sample, geno in merged:
            assert sample in expected
            assert geno == expected[sample]


class TestReference(object):
    def test_create_empty(self):
        reference = io.Reference(io.Genotype(), [], [])
        assert reference.genotype.n_loci == 0
        assert reference.genotype.n_samples == 0
        assert reference.groups == []
        assert reference.ranges == []

    def test_limit_range(self):
        genotype = io.Genotype.parse_str(iter(STR_STREAM))
        groups = ["A", "B"]
        sizes = [1,2]
        ranges = [(0, 1), (1, 2)]
        reference = io.Reference(genotype, groups, sizes)
        assert reference.groups == groups
        assert reference.ranges == ranges


class TestQFile(object):
    def test_create_empty(self):
        qfile = io.QFile()
        assert qfile.n_samples == 0
        assert qfile.n_ancestries == 0

    def test_get_ancestry_raise_error(self):
        qfile = io.QFile()
        with pytest.raises(IndexError):
            qfile.get_ancestry(1)

    def test_add(self):
        qfile = io.QFile()
        qfile.add("X", [0, 1, 2])
        assert qfile.n_ancestries == 3
        assert qfile.n_samples == 1

    def test_iterate_ancestry(self):
        qfile = io.QFile()
        qfile.add("X", [0, 1, 2])
        for sample, ancestry in qfile:
            assert sample == "X"
            assert ancestry == [0, 1, 2]

    def test_write(self):
        qfile = io.QFile()
        qfile.add("A", [1, 1, 1])
        qfile.add("B", [1, 1, 1])
        qfile.add("C", [1, 1, 1])
        
        stream = StringIO("")
        qfile.write(stream)
        expected = "A\t1\t1\t1\nB\t1\t1\t1\nC\t1\t1\t1\n"
        assert stream.getvalue() == expected

    def test_barplot(self):
        qfile = io.QFile()
        qfile.add("A", [1, 1, 1])
        qfile.add("B", [2, 2, 2])
        qfile.add("C", [3, 3, 3])
        barplot = qfile.to_barplot()
        expected = [
            dict(x=["A", "B", "C"], y=[1, 2, 3], type="bar", name="Pop #000"),
            dict(x=["A", "B", "C"], y=[1, 2, 3], type="bar", name="Pop #001"),
            dict(x=["A", "B", "C"], y=[1, 2, 3], type="bar", name="Pop #002")
        ]
        for i in range(3):
            assert barplot[i] == expected[i]

    def test_summarise(self):
        qfile = io.QFile()
        qfile.add("A", [1, 1, 1])
        qfile.add("B", [1, 1, 1])
        qfile.add("C", [1, 1, 1])
        qfile.add("D", [1, 1, 1])
        qfile.add("E", [1, 1, 1])
        qfile.add("F", [1, 1, 1])
        qfile = qfile.summarise(["GA", "GB"], [(1,3), (4, 6)])

        assert qfile.samples == ["A", "D", "GA", "GB"]
        assert qfile.get_ancestry(0) == [1, 1, 1, 1]
        assert qfile.get_ancestry(1) == [1, 1, 1, 1]
        assert qfile.get_ancestry(2) == [1, 1, 1, 1]
