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
from hashlib import blake2b
from superstark.ff import FieldElement
from superstark.merkle import Merkle
from superstark.poly import Univariate
from superstark.fs import ProofStream


class FRI:
    def __init__(
        self,
        offset,
        omega: FieldElement,
        initial_domain_length,
        expansion_factor,
        num_colinearity_tests,
    ):
        self.offset = offset
        self.omega: FieldElement = omega
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
            N = len(codeword)
            print("Omega^(n-1) :", omega ^ (N - 1))
            print("Omega.inv()", omega.inv())
            # make sure omega has the right order
            assert (
                omega ^ (N - 1) == omega.inv()
            ), "error in commit: omega does not have the right order!"
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
            codewords += [codeword]
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
        codewords += [codeword]
        return codewords

    def query(
        self, current_codeword, next_codeword, c_indices, proof_stream: ProofStream
    ):
        # extract a and b indices
        a_indices = [index for index in c_indices]
        b_indices = [index + len(current_codeword) // 2 for index in c_indices]

        # reveal leafs
        for s in range(self.num_colinearity_tests):
            proof_stream.push(
                (
                    current_codeword[a_indices[s]],
                    current_codeword[b_indices[s]],
                    next_codeword[c_indices[s]],
                )
            )
        # reveal authentication paths
        for s in range(self.num_colinearity_tests):
            proof_stream.push(Merkle.open(a_indices[s], current_codeword))
            proof_stream.push(Merkle.open(b_indices[s], current_codeword))
            proof_stream.push(Merkle.open(c_indices), next_codeword)

        return a_indices + b_indices

    def sample_index(bs, size):
        acc = 0
        for b in bs:
            acc = (acc << 8) ^ int(b)
        return acc % size

    def sample_indices(self, seed, size, reduced_size, number):
        assert number <= reduced_size
        assert number <= 2 * reduced_size
        indices = []
        reduced_indices = []
        counter = 0
        while len(indices) < number:
            index = FRI.sample_index(blake2b(seed + bytes(counter)).digest(), size)
            reduced_index = index % reduced_size
            counter += 1
            if reduced_index not in reduced_indices:
                indices += [index]
                reduced_indices += [reduced_index]
        return indices

    def prove(self, codeword, proof_stream: ProofStream):
        assert self.domain_length == len(
            codeword
        ), "initial domain length does not match codeword length"

        # commit
        codewords = self.commit(codeword, proof_stream)
        # sample indices
        top_lvl_indices = self.sample_indices(
            proof_stream.prover(),
            len(codewords[0]),
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

    def verify(self, proof_stream, polynomial_values):
        omega = self.omega
        offset = self.offset

        # extract all roots and alphas
        roots = []
        alphas = []
        for r in range(self.num_rounds()):
            roots += [proof_stream.pull()]
            alphas += [self.field.sample(proof_stream.verifier())]

        # extract last codeword
        last_codeword = proof_stream.pull()

        # check if it matches the given root
        if roots[-1] != Merkle.commit(last_codeword):
            print("last codeword is not well formed")
            return False

        # check if it is low degree
        degree = (len(last_codeword) // self.expansion_factor) - 1
        last_omega = omega
        last_offset = offset
        for r in range(self.num_rounds() - 1):
            last_omega = last_omega ^ 2
            last_offset = last_offset ^ 2

        # assert that last_omega has the right order
        assert last_omega.inv() == last_omega ^ (
            len(last_codeword) - 1
        ), "omega does not have right order"

        # compute interpolant
        last_domain = [
            last_offset * (last_omega ^ i) for i in range(len(last_codeword))
        ]
        poly = Univariate.interpolate_domain(last_domain, last_codeword)
        # coefficients = intt(last_omega, last_codeword)
        # poly = Polynomial(coefficients).scale(last_offset.inverse())

        # verify by  evaluating
        assert (
            poly.evaluate_domain(last_domain) == last_codeword
        ), "re-evaluated codeword does not match original!"
        if poly.degree() > degree:
            print(
                "last codeword does not correspond to polynomial of low enough degree"
            )
            print("observed degree:", poly.degree())
            print("but should be:", degree)
            return False

        # get indices
        top_level_indices = self.sample_indices(
            proof_stream.verifier(),
            self.domain_length >> 1,
            self.domain_length >> (self.num_rounds() - 1),
            self.num_colinearity_tests,
        )

        # for every round, check consistency of subsequent layers
        for r in range(0, self.num_rounds() - 1):

            # fold c indices
            c_indices = [
                index % (self.domain_length >> (r + 1)) for index in top_level_indices
            ]

            # infer a and b indices
            a_indices = [index for index in c_indices]
            b_indices = [index + (self.domain_length >> (r + 1)) for index in a_indices]

            # read values and check colinearity
            aa = []
            bb = []
            cc = []
            for s in range(self.num_colinearity_tests):
                (ay, by, cy) = proof_stream.pull()
                aa += [ay]
                bb += [by]
                cc += [cy]

                # record top-layer values for later verification
                if r == 0:
                    polynomial_values += [(a_indices[s], ay), (b_indices[s], by)]

                # colinearity check
                ax = offset * (omega ^ a_indices[s])
                bx = offset * (omega ^ b_indices[s])
                cx = alphas[r]
                if Univariate.test_colinearity([(ax, ay), (bx, by), (cx, cy)]) == False:
                    print("colinearity check failure")
                    return False

            # verify authentication paths
            for i in range(self.num_colinearity_tests):
                path = proof_stream.pull()
                if Merkle.verify(roots[r], a_indices[i], path, aa[i]) == False:
                    print("merkle authentication path verification fails for aa")
                    return False
                path = proof_stream.pull()
                if Merkle.verify(roots[r], b_indices[i], path, bb[i]) == False:
                    print("merkle authentication path verification fails for bb")
                    return False
                path = proof_stream.pull()
                if Merkle.verify(roots[r + 1], c_indices[i], path, cc[i]) == False:
                    print("merkle authentication path verification fails for cc")
                    return False

            # square omega and offset to prepare for next round
            omega = omega ^ 2
            offset = offset ^ 2

        # all checks passed
        return True
