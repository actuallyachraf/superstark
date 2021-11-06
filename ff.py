"""
FieldElement : Implementation of Finite Fields.
"""
from __future__ import annotations
from fastmath import xgcd


class FieldElement(object):
    def __init__(self, value: int, field: FiniteField) -> None:
        self.value = value
        self.field = field

    def __add__(self, right: FieldElement):
        return self.field.add(self, right)

    def __mul__(self, right: FieldElement):
        return self.field.mul(self, right)

    def __sub__(self, right: FieldElement):
        return self.field.sub(self, right)

    def __truediv__(self, right: FieldElement):
        return self.field.div(self, right)

    def __neg__(self):
        return self.field.neg(self)

    def inv(self):
        return self.field.inv(self)

    # modular exponentiation -- be sure to encapsulate in parentheses!
    def __xor__(self, exponent: int):
        acc = FieldElement(1, self.field)
        val = FieldElement(self.value, self.field)
        for i in reversed(range(len(bin(exponent)[2:]))):
            acc = acc * acc
            if (1 << i) & exponent != 0:
                acc = acc * val
        return acc

    def __eq__(self, other: FieldElement):
        return self.value == other.value

    def __neq__(self, other: FieldElement):
        return self.value != other.value

    def __str__(self):
        return str(self.value)

    def __bytes__(self):
        return bytes(str(self).encode())

    def is_zero(self):
        if self.value == 0:
            return True
        else:
            return False


class FiniteField(object):
    def __init__(self, p) -> None:
        self.p = p

    def zero(self) -> FieldElement:
        return FieldElement(0, self)

    def one(self) -> FieldElement:
        return FieldElement(1, self)

    def mul(self, l: FieldElement, r: FieldElement) -> FieldElement:
        return FieldElement((l.value * r.value) % self.p, self)

    def add(self, l: FieldElement, r: FieldElement) -> FieldElement:
        return FieldElement((l.vaue + r.value) % self.p, self)

    def sub(self, l: FieldElement, r: FieldElement) -> FieldElement:
        return FieldElement((self.p + l.value - r.value) % self.p, self)

    def neg(self, operand: FieldElement) -> FieldElement:
        return FieldElement((self.p - operand.value) % self.p, self)

    def inv(self, operand: FieldElement) -> FieldElement:
        a, b, g = xgcd(operand.value, self.p)
        return FieldElement(a, self)

    def div(self, l: FieldElement, r: FieldElement) -> FieldElement:
        assert not r.is_zero()
        a, b, g = xgcd(r.value, self.p)
        return FieldElement((l.value * a % self.p), self)

    def generator(self):
        assert self.p == 1 + 407 * (
            1 << 119
        ), "Do not know generator for other fields beyond 1+407*2^119"
        return FieldElement(85408008396924667383611388730472331217, self)

    def primitive_nth_root(self, n: FieldElement):
        if self.p == 1 + 407 * (1 << 119):
            assert (
                n <= 1 << 119 and (n & (n - 1)) == 0
            ), "Field does not have nth root of unity where n > 2^119 or not power of two."
            root = FieldElement(85408008396924667383611388730472331217, self)
            order = 1 << 119
            while order != n:
                root = root ^ 2
                order = order / 2
            return root
        else:
            assert False, "Unknown field, can't return root of unity."

    def sample(self, byte_array):
        acc = 0
        for b in byte_array:
            acc = (acc << 8) ^ int(b)
        return FieldElement(acc % self.p, self)
