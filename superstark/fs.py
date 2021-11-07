"""
FS: Implementation of Fiat-Shamir Transform.
"""

from hashlib import shake_256
import pickle


class ProofStream:
    """
    A ProofStream generalizes the concept of Fiat-Shamir transcripts.
    """

    def __init__(self) -> None:
        self.objects = []
        self.read_index = 0

    def push(self, obj):
        self.objects.append(obj)

    def pull(self):
        assert self.read_index < len(self.objects)
        obj = self.objects[self.read_index]
        self.read_index += 1
        return obj

    def serialize(self):
        return pickle.dumps(self.objects)

    def deserialize(self, bb):
        ps = ProofStream()
        ps.objects = pickle.loads(bb)
        return ps

    def prover(self, num_bytes=32):
        return shake_256(self.serialize()).digest(num_bytes)

    def verifier(self, num_bytes=32):
        return shake_256(pickle.dumps(self.objects[: self.read_index])).digest(
            num_bytes
        )
