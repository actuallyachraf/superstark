"""
Merkle: Implementation of Merkle Trees over Blake2
"""
from typing import List, Any
from hashlib import blake2b


class Merkle:
    """
    We consider the merkle tree as a commitment protocol implementing
    the interface:
    * commit_() : commits to a list by computing the merkle tree.
    * open_() : opens the commitment by computing the authentification path.
    * verify_() : verify that a value is commited by checking that its a leaf.
    """

    H = blake2b

    def commit_(leafs):
        assert len(leafs) & (len(leafs) - 1) == 0, "List must be of a power two length"
        if len(leafs) == 1:
            return leafs[0]
        return Merkle.H(
            Merkle.commit_(leafs[: (len(leafs) // 2)])
            + Merkle.commit_(leafs[(len(leafs) // 2) :])
        ).digest()

    def open_(index, leafs):
        assert len(leafs) & (len(leafs) - 1) == 0, "List must be of a power two length"
        assert 0 <= index and index < len(leafs)
        if len(leafs) == 2:
            return [leafs[1 - index]]
        elif index < (len(leafs) / 2):
            return Merkle.open_(index, leafs[: (len(leafs) // 2)]) + [
                Merkle.commit_(leafs[(len(leafs) // 2) :])
            ]
        else:
            return Merkle.open_(index - len(leafs) // 2, leafs[len(leafs) // 2 :]) + [
                Merkle.commit_(leafs[: len(leafs) // 2])
            ]

    def verify_(root, index, path, leaf):
        assert 0 <= index and index < (1 << len(path)), "cannot verify invalid index"
        if len(path) == 1:
            if index == 0:
                return root == Merkle.H(leaf + path[0]).digest()
            else:
                return root == Merkle.H(path[0] + leaf).digest()
        else:
            if index % 2 == 0:
                return Merkle.verify_(
                    root, index >> 1, path[1:], Merkle.H(leaf + path[0]).digest()
                )
            else:
                return Merkle.verify_(
                    root, index >> 1, path[1:], Merkle.H(path[0] + leaf).digest()
                )

    # The following functions expose the API and compute hashes of leafs before
    # calling the underlying code.
    def commit(leafs: List[Any]):
        return Merkle.commit_([Merkle.H(bytes(leaf)).digest() for leaf in leafs])

    def open(index: int, leafs: List[Any]):
        return Merkle.open_(index, [Merkle.H(bytes(leaf)).digest() for leaf in leafs])

    def verify(root: bytes, index: int, path: List[List[Any]], leaf: List[Any]):
        return Merkle.verify_(root, index, path, Merkle.H(bytes(leaf)).digest())
