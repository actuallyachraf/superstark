# superstark

Superstark is a pure Python 3 implementation of zkSTARKs with support of Fast Fourier Transforms and RESCUE Hash.

## What is a STARK ?

- **tl:dr**: the main takeaway is that a STARK is a proof that transition between registers are correct given an execution trace.

A STARK (Succint-Transparent ARgument of Knowledge) a transparent (no trusted setup, no assumptions beyond hash functions) proof system
for relations and computations.

What a STARK does essentially is trace the some computation (program P running on inputs X) where the trace is essentially
a timestamped record of all register states. By encoding register transitions (opcodes) as algebraic operations, we endup
with an algebraic intermediate representation that encapsulates the entire execution of the program.

By encoding this execution trace as a polynomial sequence we can commit to it and provide oracle access to polynomial
evaluations using merkle trees and Fiat-Shamir transforms.

What the **IOP** part of the proof means is that the verifier only queries the prover for random locations, byu using Reed-Solomon codes
the IOP protocol allows us to build a polynomial commitment that essentially plays the role of oracle access.
