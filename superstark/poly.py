"""
Poly: Implementation of Univariate and Multivariate Polynomials on Finite Fields.
"""

from typing import List
from superstark.ff import FieldElement


class Univariate:
    def __init__(self, coefficients):
        self.coefficients: List[FieldElement] = [c for c in coefficients]

    def degree(self):
        if self.coefficients == []:
            return -1
        zero = self.coefficients[0].field.zero()
        if self.coefficients == [zero] * len(self.coefficients):
            return -1
        maxindex = 0
        for i in range(len(self.coefficients)):
            if self.coefficients[i] != zero:
                maxindex = i
        return maxindex

    def __neg__(self):
        return Univariate([-c for c in self.coefficients])

    def __add__(self, other):
        if self.degree() == -1:
            return other
        elif other.degree() == -1:
            return self
        field = self.coefficients[0].field
        coeffs = [field.zero()] * max(len(self.coefficients), len(other.coefficients))
        for i in range(len(self.coefficients)):
            coeffs[i] = coeffs[i] + self.coefficients[i]
        for i in range(len(other.coefficients)):
            coeffs[i] = coeffs[i] + other.coefficients[i]
        return Univariate(coeffs)

    def __sub__(self, other):
        return self.__add__(-other)

    def __mul__(self, other):
        if self.coefficients == [] or other.coefficients == []:
            return Univariate([])
        zero = self.coefficients[0].field.zero()
        buf = [zero] * (len(self.coefficients) + len(other.coefficients) - 1)
        for i in range(len(self.coefficients)):
            if self.coefficients[i].is_zero():
                continue  # optimization for sparse polynomials
            for j in range(len(other.coefficients)):
                buf[i + j] = buf[i + j] + self.coefficients[i] * other.coefficients[j]
        return Univariate(buf)

    def __eq__(self, other):
        if self.degree() != other.degree():
            return False
        if self.degree() == -1:
            return True
        return all(
            self.coefficients[i] == other.coefficients[i]
            for i in range(len(self.coefficients))
        )

    def __neq__(self, other):
        return not self.__eq__(other)

    def is_zero(self):
        if self.degree() == -1:
            return True
        return False

    def leading_coefficient(self):
        return self.coefficients[self.degree()]

    def divide(numerator, denominator):
        if denominator.degree() == -1:
            return None
        if numerator.degree() < denominator.degree():
            return (Univariate([]), numerator)
        field = denominator.coefficients[0].field
        remainder = Univariate([n for n in numerator.coefficients])
        quotient_coefficients = [
            field.zero() for i in range(numerator.degree() - denominator.degree() + 1)
        ]
        for i in range(numerator.degree() - denominator.degree() + 1):
            if remainder.degree() < denominator.degree():
                break
            coefficient = (
                remainder.leading_coefficient() / denominator.leading_coefficient()
            )
            shift = remainder.degree() - denominator.degree()
            subtractee = (
                Univariate([field.zero()] * shift + [coefficient]) * denominator
            )
            quotient_coefficients[shift] = coefficient
            remainder = remainder - subtractee
        quotient = Univariate(quotient_coefficients)
        return quotient, remainder

    def __truediv__(self, other):
        quo, rem = Univariate.divide(self, other)
        assert (
            rem.is_zero()
        ), "cannot perform polynomial division because remainder is not zero"
        return quo

    def __mod__(self, other):
        quo, rem = Univariate.divide(self, other)
        return rem

    def __xor__(self, exponent):
        if self.is_zero():
            return Univariate([])
        if exponent == 0:
            return Univariate([self.coefficients[0].field.one()])
        acc = Univariate([self.coefficients[0].field.one()])
        for i in reversed(range(len(bin(exponent)[2:]))):
            acc = acc * acc
            if (1 << i) & exponent != 0:
                acc = acc * self
        return acc

    def evaluate(self, point):
        xi = point.field.one()
        value = point.field.zero()
        for c in self.coefficients:
            value = value + c * xi
            xi = xi * point
        return value

    def evaluate_domain(self, domain):
        return [self.evaluate(d) for d in domain]

    def interpolate_domain(domain, values):
        assert len(domain) == len(
            values
        ), "number of elements in domain does not match number of values -- cannot interpolate"
        assert len(domain) > 0, "cannot interpolate between zero points"
        field = domain[0].field
        x = Univariate([field.zero(), field.one()])
        acc = Univariate([])
        for i in range(len(domain)):
            prod = Univariate([values[i]])
            for j in range(len(domain)):
                if j == i:
                    continue
                prod = (
                    prod
                    * (x - Univariate([domain[j]]))
                    * Univariate([(domain[i] - domain[j]).inv()])
                )
            acc = acc + prod
        return acc

    # zerofier or vanishing polynomial is the unique monic that takes 0
    #  on all points in the domain
    def zerofier_domain(domain):
        field = domain[0].field
        x = Univariate([field.zero(), field.one()])
        acc = Univariate([field.one()])
        for d in domain:
            acc = acc * (x - Univariate([d]))
        return acc

    def scale(self, factor):
        return Univariate(
            [(factor ^ i) * self.coefficients[i] for i in range(len(self.coefficients))]
        )

    # colinearity tests whether three points fall on the same line
    # a line being a polynomial of degree 1 (ax+b)
    def test_colinearity(points):
        domain = [p[0] for p in points]
        values = [p[1] for p in points]
        polynomial = Univariate.interpolate_domain(domain, values)
        return polynomial.degree() == 1


class Multivariate:
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def zero():
        return Multivariate(dict())

    def __add__(self, other):
        dictionary = dict()
        num_variables = max(
            [len(k) for k in self.dictionary.keys()]
            + [len(k) for k in other.dictionary.keys()]
        )
        for k, v in self.dictionary.items():
            pad = list(k) + [0] * (num_variables - len(k))
            pad = tuple(pad)
            dictionary[pad] = v
        for k, v in other.dictionary.items():
            pad = list(k) + [0] * (num_variables - len(k))
            pad = tuple(pad)
            if pad in dictionary.keys():
                dictionary[pad] = dictionary[pad] + v
            else:
                dictionary[pad] = v
        return Multivariate(dictionary)

    def __mul__(self, other):
        dictionary = dict()
        num_variables = max(
            [len(k) for k in self.dictionary.keys()]
            + [len(k) for k in other.dictionary.keys()]
        )
        for k0, v0 in self.dictionary.items():
            for k1, v1 in other.dictionary.items():
                exponent = [0] * num_variables
                for k in range(len(k0)):
                    exponent[k] += k0[k]
                for k in range(len(k1)):
                    exponent[k] += k1[k]
                exponent = tuple(exponent)
                if exponent in dictionary.keys():
                    dictionary[exponent] = dictionary[exponent] + v0 * v1
                else:
                    dictionary[exponent] = v0 * v1
        return Multivariate(dictionary)

    def __sub__(self, other):
        return self + (-other)

    def __neg__(self):
        dictionary = dict()
        for k, v in self.dictionary.items():
            dictionary[k] = -v
        return Multivariate(dictionary)

    def __xor__(self, exponent):
        if self.is_zero():
            return Multivariate(dict())
        field = list(self.dictionary.values())[0].field
        num_variables = len(list(self.dictionary.keys())[0])
        exp = [0] * num_variables
        acc = Multivariate({tuple(exp): field.one()})
        for b in bin(exponent)[2:]:
            acc = acc * acc
            if b == "1":
                acc = acc * self
        return acc

    def constant(element):
        return Multivariate({tuple([0]): element})

    def is_zero(self):
        if not self.dictionary:
            return True
        else:
            for v in self.dictionary.values():
                if v.is_zero() == False:
                    return False
            return True

    def variables(num_variables, field):
        variables = []
        for i in range(num_variables):
            exponent = [0] * i + [1] + [0] * (num_variables - i - 1)
            variables = variables + [Multivariate({tuple(exponent): field.one()})]
        return variables

    def lift(polynomial, variable_index):
        if polynomial.is_zero():
            return Multivariate({})
        field = polynomial.coefficients[0].field
        variables = Multivariate.variables(variable_index + 1, field)
        x = variables[-1]
        acc = Multivariate({})
        for i in range(len(polynomial.coefficients)):
            acc = acc + Multivariate.constant(polynomial.coefficients[i]) * (x ^ i)
        return acc

    def evaluate(self, point):
        acc = point[0].field.zero()
        for k, v in self.dictionary.items():
            prod = v
            for i in range(len(k)):
                prod = prod * (point[i] ^ k[i])
            acc = acc + prod
        return acc

    def evaluate_symbolic(self, point):
        acc = Univariate([])
        for k, v in self.dictionary.items():
            prod = Univariate([v])
            for i in range(len(k)):
                prod = prod * (point[i] ^ k[i])
            acc = acc + prod
        return acc
