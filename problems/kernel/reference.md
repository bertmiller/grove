# Kernel Optimization Challenge

Optimize `build_kernel()` in `solution.py` to minimize clock cycles on a simulated VLIW SIMD machine.

## The problem

The kernel performs a parallel tree traversal: a batch of 256 inputs traverses a binary tree of height 10 for 16 rounds. At each node, the input value is XORed with the node value, hashed through a 6-stage hash function, and the hash result determines left/right branching. If the traversal reaches a leaf, it wraps back to the root.

## The machine

The simulated machine is a VLIW (Very Long Instruction Word) SIMD architecture defined in `problem.py`:

- **Engines (execute in parallel each cycle):**
  - `alu` — 12 slots, scalar arithmetic/logic ops
  - `valu` — 6 slots, SIMD vector ops (VLEN=8 elements)
  - `load` — 2 slots, memory reads and constants
  - `store` — 2 slots, memory writes
  - `flow` — 1 slot, control flow (jumps, selects, halt)
- **Memory model:** All inputs are read before any writes land (end-of-cycle commit)
- **Scratch space:** 1536 words (registers, constants, cache)
- **Single core** (N_CORES=1)

## Key instructions

- **Scalar ALU:** `(op, dest, a1, a2)` — ops: `+`, `-`, `*`, `//`, `%`, `^`, `&`, `|`, `<<`, `>>`, `<`, `==`, `cdiv`
- **Vector ALU:** `(op, dest, a1, a2)` — same ops on VLEN elements; also `("vbroadcast", dest, src)`, `("multiply_add", dest, a, b, c)`
- **Load:** `("load", dest, addr_reg)`, `("vload", dest, addr_reg)`, `("const", dest, val)`
- **Store:** `("store", addr_reg, src)`, `("vstore", addr_reg, src)`
- **Flow:** `("select", dest, cond, a, b)`, `("vselect", ...)`, `("cond_jump", cond, pc)`, `("jump", pc)`, `("halt",)`, `("add_imm", dest, a, imm)`

## Optimization strategies

The baseline is a naive scalar implementation — one batch element at a time, no parallelism, fully unrolled. Key optimization axes:

1. **VLIW packing** — pack multiple independent ops into one instruction bundle to use all engine slots per cycle
2. **SIMD vectorization** — process VLEN=8 batch elements per vector instruction
3. **Loop constructs** — use `cond_jump`/`jump` instead of unrolling to reduce program size
4. **Memory access patterns** — minimize loads by caching values in scratch space
5. **Instruction scheduling** — account for the 1-cycle latency between write and read

## Baseline

The starter code runs in **147,734 cycles**. Run `python verify.py` to check your score.
