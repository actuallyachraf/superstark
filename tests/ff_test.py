import unittest

from superstark import ff

_PRIME = 18446744073709551557


class TestFiniteFields(unittest.TestCase):
    def test_field_constructor(self):
        f = ff.FiniteField(_PRIME)
        assert type(f) is ff.FiniteField

    def test_field_ops(self):
        f = ff.FiniteField(_PRIME)
        a = ff.FieldElement(5, f)
        b = ff.FieldElement(10, f)

        assert a + b == f.add(a, b)
        assert a - b == f.sub(a, b)
        assert a * b == f.mul(a, b)
        assert a * a.inv() == f.one()
