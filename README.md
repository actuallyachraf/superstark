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

This part of the implementation handles the core verifier-prover process.

## Making sense of AIR

As we've mentionned before our goal is to prove the integrity of a computation.
If we consider the computation to be a function F(x) that for e.g computes the
hash value of x then the integrity of the computation is essentially
the verification of the property that F(x) = y.
We can consider various computations, but the arithmetization process will often
be done on **pure computation** that can be reduced to basic arithmetic operations.

AIR or Algebraic Intermediate Representation is one of many arithmetization processes like R1CS that **encode** computation (algorithms) into a set
of algebraic equations that we call **constraint system**.

In AIR the encoding assumes as input a computation done on a register
based machine with random access memory.

AIR essentially records the executation of the register based VM
into a table called a **trace** where columns depicts the state
of a register W and rows depict the state of a register W at time t.

Accompagning the trace is a set of boundary constraints such as register W(0)
is equal to 7.

The trace and boundary constraint constitute the **arithmetized** computation
that we prove things about.

As an example consider a dummy arithmetic hash function.

```python

_EXP = 37

def hash(x):
    y1 = x * x # x squared
    y2 = y1 * x # x cube
    y3 = y2 + y2 # double y2
    y4 = y3 * y3 # square it
    return y4
```

If we consider a simple virtual machine _VM_ with 2 registers r0,r1 and a few
opcodes LOAD,STORE,RET,ADD and MUL then we can translate the computation into bytecode.

```asm
_HASH
    load r0,x
    mul r0,x
    mul r0,x
    add r1,r0
    add r1,r0
    mul r1,r1
    ret
```

Running this computation explicitly and store the states of registers r0 and r1
would yield a table such as this for input x = 4 :

| r0  | r1     |
| --- | ------ |
| 7   | 0      |
| 49  | 0      |
| 343 | 0      |
| 343 | 343    |
| 343 | 686    |
| 343 | 470596 |
