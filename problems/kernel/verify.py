"""Oracle for kernel optimization: checks correctness and reports cycle count."""

import random
import sys

from problem import (
    Machine,
    Tree,
    Input,
    N_CORES,
    build_mem_image,
    reference_kernel2,
)
from solution import KernelBuilder

BASELINE = 147734

# Test parameters
FOREST_HEIGHT = 10
ROUNDS = 16
BATCH_SIZE = 256
N_CORRECTNESS_CHECKS = 8


def build_kernel(forest_height, n_nodes, batch_size, rounds):
    kb = KernelBuilder()
    kb.build_kernel(forest_height, n_nodes, batch_size, rounds)
    return kb


def run_kernel(forest_height, rounds, batch_size):
    forest = Tree.generate(forest_height)
    inp = Input.generate(forest, batch_size, rounds)
    mem = build_mem_image(forest, inp)

    kb = build_kernel(forest.height, len(forest.values), len(inp.indices), rounds)

    machine = Machine(mem, kb.instrs, kb.debug_info(), n_cores=N_CORES)
    machine.enable_pause = False
    machine.enable_debug = False
    machine.run()

    for ref_mem in reference_kernel2(mem):
        pass

    inp_values_p = ref_mem[6]
    if (
        machine.mem[inp_values_p : inp_values_p + len(inp.values)]
        != ref_mem[inp_values_p : inp_values_p + len(inp.values)]
    ):
        return None  # incorrect

    return machine.cycle


def main():
    # Correctness: run multiple random tests
    for i in range(N_CORRECTNESS_CHECKS):
        result = run_kernel(FOREST_HEIGHT, ROUNDS, BATCH_SIZE)
        if result is None:
            print("WRONG: incorrect output values", file=sys.stderr)
            sys.exit(1)

    # Score: report cycles from last run
    print(f"score={result}")


if __name__ == "__main__":
    main()
