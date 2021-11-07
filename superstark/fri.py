"""
FRI : Fast Reed-Solomon Interactive Oracle Proofs of Proximity

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
from superstark.fs import ProofStream


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

    def commit(self, codeword, proof_stream: ProofStream, round_index=0):
        one = self.field.one()
        two = FieldElement(2, self.field)
        omega = self.omega
        offset = self.offset
        codewords = []

        # for each round run the commit loop
        for round in range(self.num_rounds()):
            # compute and write the merkle root to the fs transcript
            root = Merkle.commit(codeword)
            proof_stream.push(root)

            # check if last round
            if round == self.num_rounds() - 1:
                break
            # prepare next round

            # sample challenge scalar using the transcript
            # as source of randomness
            alpha = self.field.sample(proof_stream.prover())
            # collect round codeword
            codewords.append([codeword])
            # run the split and fold routine
            codeword = [
                two.inv()
                * (
                    (one + alpha / (offset * (omega ^ i))) * codeword[i]
                    + (one - alpha / (offset * omega ^ i))
                )
                * codeword[len(codeword) // 2 + i]
                for i in range(len(codeword) // 2)
            ]
            omega = omega ^ 2
            offset = offset ^ 2
        # send the last codeword
        proof_stream.push(codeword)
        # collect final codeword
        codewords.append([codeword])
        return codewords

    def prove(self, codeword, proof_stream: ProofStream):
        assert self.domain_length == len(
            codeword
        ), "initial domain length does not match codeword length"

        # commit
        codewords = self.commit(codeword, proof_stream)

        # sample indices
        top_lvl_indices = self.sample_indices(
            proof_stream.prover(),
            len(codewords[1]),
            len(codewords[-1]),
            self.num_colinearity_tests,
        )
        indices = [index for index in top_lvl_indices]

        # query
        for i in range(len(codewords) - 1):
            # indices are re-used modulo codeword size as a security feature
            indices = [index % len(codewords[i]) // 2 for index in indices]
            self.query(codewords[i], codewords[i + 1], indices, proof_stream)
        return top_lvl_indices
