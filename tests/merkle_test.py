import unittest

from superstark import merkle


class TestMerkleCommitments(unittest.TestCase):
    def test_merkle_commitment(self):
        objects = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        root = merkle.Merkle.commit(objects)
        print(root)
        for index in range(len(objects)):
            ap = merkle.Merkle.open(index, objects)
            assert merkle.Merkle.verify(root, index, ap, objects[index]) is True
