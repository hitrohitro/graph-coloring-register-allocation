import argparse
from pathlib import Path
import random
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

from src.ir_parser import parse_ir
from src.liveness import compute_liveness
from src.interference_graph import build_interference_graph
from src.algorithm_comparison import compare_algorithms
from src.visualize import draw_comparison

NUM_REGISTERS = 4


def generate_auto_ir(num_instructions=20, num_variables=6, seed=42):
    """Generate synthetic IR text lines for register-allocation experiments."""
    rng = random.Random(seed)

    base_vars = [chr(ord("a") + i) for i in range(max(2, num_variables))]
    lines = []

    # Seed definitions.
    for var in base_vars:
        lines.append(f"load {var}")

    available = list(base_vars)
    op_names = ["add", "sub", "mul", "div"]

    temp_idx = 1
    body_len = max(1, num_instructions - len(lines))
    for _ in range(body_len):
        # Occasionally emit a pure use to extend liveness.
        if rng.random() < 0.2 and available:
            lines.append(f"use {rng.choice(available)}")
            continue

        left = rng.choice(available)
        right = rng.choice(available)
        op = rng.choice(op_names)
        target = f"t{temp_idx}"
        temp_idx += 1

        lines.append(f"{target} = {left} {op} {right}")
        available.append(target)

        # Keep pressure but avoid unbounded symbol growth.
        if len(available) > (num_variables + 10) and rng.random() < 0.35:
            drop = rng.randint(0, len(base_vars) - 1)
            available.pop(drop)

    return lines


def write_ir_file(ir_file, lines):
    with open(ir_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def run_allocation_pipeline(ir_file):
    instructions = parse_ir(ir_file)
    live_in, live_out = compute_liveness(instructions)

    print("Liveness Results\n")

    for i in range(len(instructions)):
        print(f"Instruction {i}")
        print("LIVE_IN :", live_in[i])
        print("LIVE_OUT:", live_out[i])
        print()

    graph = build_interference_graph(instructions, live_out)

    print("Interference Graph Edges\n")
    for edge in graph.edges():
        print(edge)

    results = compare_algorithms(graph, NUM_REGISTERS, verbose=True)

    print("\nGreedy Register Allocation\n")
    greedy_assignment = results["greedy"]["assignment"]
    greedy_spills = results["greedy"]["spills"]

    for node in sorted(greedy_assignment):
        print(f"{node} -> {greedy_assignment[node]}")

    if greedy_spills:
        print("\nSpills")
        for node in greedy_spills:
            print(node)
    else:
        print("\nSpills\nNone")

    print("\n" + "=" * 70)
    print("\nFPT Random Walk Register Allocation\n")
    fpt_assignment = results["fpt_random_walk"]["assignment"]
    fpt_spills = results["fpt_random_walk"]["spills"]

    for node in sorted(fpt_assignment):
        print(f"{node} -> {fpt_assignment[node]}")

    if fpt_spills:
        print("\nSpills")
        for node in fpt_spills:
            print(node)
    else:
        print("\nSpills\nNone")

    print("\n" + "=" * 70)
    print("\nDP Branch-and-Bound Register Allocation\n")
    dp_assignment = results["dp"]["assignment"]
    dp_spills = results["dp"]["spills"]

    for node in sorted(dp_assignment):
        print(f"{node} -> {dp_assignment[node]}")

    if dp_spills:
        print("\nSpills")
        for node in dp_spills:
            print(node)
    else:
        print("\nSpills\nNone")

    try:
        import matplotlib.pyplot as plt
        if sys.stdin.isatty():
            draw_comparison(
                graph,
                greedy_assignment,
                greedy_spills,
                fpt_assignment,
                fpt_spills,
                dp_assignment,
                dp_spills,
            )
    except:
        print("\n[Visualization skipped - running in non-interactive mode]")


def parse_args():
    parser = argparse.ArgumentParser(description="Graph-coloring register allocation driver")
    parser.add_argument("--ir-mode", choices=["custom", "auto"], default="auto")
    parser.add_argument("--ir-file", default=str(DATA_DIR / "ir.txt"))
    parser.add_argument("--auto-instructions", type=int, default=20)
    parser.add_argument("--auto-variables", type=int, default=6)
    parser.add_argument("--auto-seed", type=int, default=42)
    return parser.parse_args()


def main():
    args = parse_args()

    if args.ir_mode == "auto":
        generated_lines = generate_auto_ir(
            num_instructions=args.auto_instructions,
            num_variables=args.auto_variables,
            seed=args.auto_seed,
        )
        write_ir_file(args.ir_file, generated_lines)
        print(f"Generated IR written to {args.ir_file} ({len(generated_lines)} lines).\n")
    else:
        print(f"Using custom IR from {args.ir_file}.\n")

    run_allocation_pipeline(args.ir_file)


if __name__ == "__main__":
    main()