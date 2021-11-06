"""
FRI : Fast Reed Solomon Interactive Oracle Proofs of Proximity

FRI is a polynomial commitment scheme that establishes that a polynomial
has bounded degree.
While the FRI protocol is defined in terms of codewords the verifier only
establishes oracle queries on said codewords.
Reed-Solomin codewords are values of the evaluation of a low-degree
polynomial over a domain.
    omega : generator of the subgroup domain using powers of two.
    offset: a generator of the multiplicative subgroup used to generate coset domains.
    expansion_factor: blowup factor of the domain.
    num_colinearity_tests: a security parameter.
"""
from ff import FieldElement
from merkle import Merkle
from poly import Univariate


class FRI:
    def __init__(
        self,
        offset,
        omega,
        initial_domain_length,
        expansion_factor,
        num_colinearity_tests,
    ):
        self.offset = offset
        self.omega = omega
        self.domain_length = initial_domain_length
        self.field = omega.field
        self.expansion_factor = expansion_factor
        self.num_colinearity_tests = num_colinearity_tests

    def num_rounds(self):
        codeword_length = self.domain_length
        num_rounds = 0
        while (
            codeword_length > self.expansion_factor
            and 4 * self.num_colinearity_tests < codeword_length
        ):
            codeword_length /= 2
            num_rounds += 1

            return num_rounds

    def eval_domain(self):
        return [self.offset * (self.omega ^ i) for i in range(self.domain_length)]
