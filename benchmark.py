"""Benchmark suite for register-allocation graph coloring.

The benchmark intentionally mimics CPU-like pressure patterns:
1) live ranges over an instruction timeline
2) loop-heavy regions (longer live intervals)
3) branch fanout (concentrated local interference)
4) call clobber pressure bursts
"""

import random
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"

import matplotlib.pyplot as plt

from src.ir_parser import parse_ir_from_text
from src.liveness import compute_liveness
from src.interference_graph import build_interference_graph
from src.greedy_coloring import greedy_graph_coloring
from src.fpt_random_walk_coloring import fpt_random_walk_coloring_enhanced
from src.dp_coloring import dp_branch_and_bound_coloring


def _build_cpu_like_intervals(
    num_virtual_registers,
    num_instructions,
    loop_regions,
    branch_probability,
    call_frequency,
    seed,
):
    """Construct synthetic live intervals that mimic register pressure."""
    rng = random.Random(seed)
    vars_list = [f"v{i}" for i in range(num_virtual_registers)]

    # Create loop regions where values typically stay live longer.
    loops = []
    for _ in range(loop_regions):
        start = rng.randint(0, max(1, num_instructions - 15))
        length = rng.randint(8, min(40, num_instructions - start))
        loops.append((start, start + length))

    def in_loop(point):
        return any(lo <= point < hi for lo, hi in loops)

    # Generate live intervals per virtual register.
    intervals = {}
    for vr in vars_list:
        start = rng.randint(0, max(0, num_instructions - 4))

        base_span = rng.randint(2, 10)
        if in_loop(start):
            base_span += rng.randint(4, 18)

        # Branches tend to widen overlap windows due to join points.
        if rng.random() < branch_probability:
            base_span += rng.randint(2, 8)

        end = min(num_instructions, start + base_span)
        intervals[vr] = (start, max(start + 1, end))

    # Inject call-pressure bursts where many temporaries overlap briefly.
    call_sites = []
    if call_frequency > 0:
        for i in range(call_frequency):
            anchor = int((i + 1) * num_instructions / (call_frequency + 1))
            jitter = rng.randint(-4, 4)
            call_sites.append(max(0, min(num_instructions - 1, anchor + jitter)))

    for site in call_sites:
        burst_size = max(2, num_virtual_registers // 6)
        burst_vars = rng.sample(vars_list, min(len(vars_list), burst_size))
        for vr in burst_vars:
            s, e = intervals[vr]
            intervals[vr] = (min(s, site), max(e, min(num_instructions, site + 3)))

    return vars_list, intervals


def _build_cpu_like_ir_lines(vars_list, intervals, num_instructions, seed):
    """Generate synthetic IR text lines from live intervals."""
    rng = random.Random(seed + 7919)
    lines = []

    # Seed with one definition per virtual register in IR form.
    for var in vars_list:
        lines.append(f"load {var}")

    for t in range(num_instructions):
        active = [v for v, (s, e) in intervals.items() if s <= t < e]

        if not active:
            # Keep instruction index progression with a harmless use.
            lines.append(f"use {rng.choice(vars_list)}")
            continue

        defined = rng.choice(active)
        other_active = [v for v in active if v != defined]

        if other_active:
            use_count = min(len(other_active), rng.randint(1, 3))
            used = rng.sample(other_active, use_count)
        else:
            used = []

        if used:
            op_names = ["add", "sub", "mul", "div"]
            op = rng.choice(op_names)
            if len(used) == 1:
                lines.append(f"{defined} = {used[0]} {op} {used[0]}")
            else:
                lines.append(f"{defined} = {used[0]} {op} {used[1]}")
        else:
            lines.append(f"load {defined}")

    return lines


def _build_cpu_like_interference_graph(
    num_virtual_registers,
    num_instructions,
    loop_regions,
    branch_probability,
    call_frequency,
    seed,
):
    """Build interference graph directly from generated IR (in-memory, no file writes)."""
    vars_list, intervals = _build_cpu_like_intervals(
        num_virtual_registers=num_virtual_registers,
        num_instructions=num_instructions,
        loop_regions=loop_regions,
        branch_probability=branch_probability,
        call_frequency=call_frequency,
        seed=seed,
    )
    ir_lines = _build_cpu_like_ir_lines(
        vars_list=vars_list,
        intervals=intervals,
        num_instructions=num_instructions,
        seed=seed,
    )

    # Parse IR directly from in-memory lines (no file I/O)
    ir_text = "\n".join(ir_lines) + "\n"
    instructions = parse_ir_from_text(ir_text)
    _, live_out = compute_liveness(instructions)
    graph = build_interference_graph(instructions, live_out)

    # Keep isolated virtual registers in the graph for realistic allocation counts.
    for var in vars_list:
        graph.add_node(var)

    return graph

def benchmark_algorithms(graph, num_registers=4, name=""):
    """Benchmark all three algorithms on a given graph."""
    
    # Greedy
    start = time.perf_counter()
    greedy_assign, greedy_spills = greedy_graph_coloring(graph, num_registers)
    greedy_time = time.perf_counter() - start
    
    # FPT
    start = time.perf_counter()
    fpt_assign, fpt_spills = fpt_random_walk_coloring_enhanced(
        graph, num_registers, num_iterations=15
    )
    fpt_time = time.perf_counter() - start
    
    # DP Branch-and-Bound
    start = time.perf_counter()
    dp_assign, dp_spills = dp_branch_and_bound_coloring(graph, num_registers)
    dp_time = time.perf_counter() - start
    
    return {
        "name": name,
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "max_degree": max(dict(graph.degree()).values()) if graph.number_of_nodes() > 0 else 0,
        "greedy": {
            "time": greedy_time,
            "colored": len(greedy_assign),
            "spills": len(greedy_spills),
            "colors": len(set(greedy_assign.values())) if greedy_assign else 0,
        },
        "fpt": {
            "time": fpt_time,
            "colored": len(fpt_assign),
            "spills": len(fpt_spills),
            "colors": len(set(fpt_assign.values())) if fpt_assign else 0,
        },
        "dp": {
            "time": dp_time,
            "colored": len(dp_assign),
            "spills": len(dp_spills),
            "colors": len(set(dp_assign.values())) if dp_assign else 0,
        }
    }

def _plot_benchmark_results(results):
    """Visual summary of runtime and spill behavior across workloads."""
    names = [r["name"] for r in results]

    greedy_time = [r["greedy"]["time"] for r in results]
    fpt_time = [r["fpt"]["time"] for r in results]
    dp_time = [r["dp"]["time"] for r in results]

    greedy_spills = [r["greedy"]["spills"] for r in results]
    fpt_spills = [r["fpt"]["spills"] for r in results]
    dp_spills = [r["dp"]["spills"] for r in results]

    x = range(len(names))
    width = 0.24

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9))

    # Runtime chart (log scale since algorithms differ by orders of magnitude)
    ax1.bar([i - width for i in x], greedy_time, width=width, label="Greedy", color="#1f77b4")
    ax1.bar(x, fpt_time, width=width, label="FPT Random Walk", color="#ff7f0e")
    ax1.bar([i + width for i in x], dp_time, width=width, label="DP B&B", color="#2ca02c")
    ax1.set_yscale("log")
    ax1.set_ylabel("Runtime (seconds, log scale)")
    ax1.set_title("Algorithm Runtime on CPU-Like Interference Workloads")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(names, rotation=20, ha="right")
    ax1.grid(axis="y", alpha=0.25)
    ax1.legend(frameon=False)

    # Spill chart
    ax2.bar([i - width for i in x], greedy_spills, width=width, label="Greedy", color="#1f77b4")
    ax2.bar(x, fpt_spills, width=width, label="FPT Random Walk", color="#ff7f0e")
    ax2.bar([i + width for i in x], dp_spills, width=width, label="DP B&B", color="#2ca02c")
    ax2.set_ylabel("Spills (lower is better)")
    ax2.set_title("Spill Counts on CPU-Like Interference Workloads")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(names, rotation=20, ha="right")
    ax2.grid(axis="y", alpha=0.25)
    ax2.legend(frameon=False)

    plt.tight_layout()
    plt.show()


def run_benchmarks(num_registers=4, show_plots=True):
    """Run benchmark scenarios that mimic practical CPU register allocation.
    
    Generates IR in-memory (no file writes); processes all workloads directly.
    """
    
    print("\n" + "="*100)
    print("GRAPH COLORING REGISTER ALLOCATION: ALGORITHM BENCHMARK")
    print("="*100 + "\n")
    
    results = []

    workloads = [
        # name, virtual regs, instructions, loop regions, branch prob, call freq, seed
        ("BasicBlock-Light", 24, 90, 1, 0.10, 1, 101),
        ("Branchy-Medium", 40, 140, 2, 0.35, 2, 202),
        ("Loop-Heavy", 56, 200, 4, 0.18, 2, 303),
        ("Call-Intensive", 72, 220, 2, 0.22, 6, 404),
        ("HotPath-Large", 96, 300, 5, 0.28, 5, 505),
    ]

    for idx, (name, regs, inst, loops, branch_p, call_f, seed) in enumerate(workloads, start=1):
        print(
            f"Test {idx}: {name} "
            f"(vregs={regs}, instr={inst}, loops={loops}, branch_p={branch_p}, calls={call_f})..."
        )
        graph = _build_cpu_like_interference_graph(
            num_virtual_registers=regs,
            num_instructions=inst,
            loop_regions=loops,
            branch_probability=branch_p,
            call_frequency=call_f,
            seed=seed,
        )
        results.append(benchmark_algorithms(graph, num_registers=num_registers, name=name))
    
    # Print results table
    print("\n" + "="*130)
    print("BENCHMARK RESULTS")
    print("="*130 + "\n")
    
    print(f"{'Test':<18} | {'Greedy':<35} | {'FPT Random Walk':<35} | {'DP B&B':<35}")
    print(f"{'':<18} | {'Time(s)':<10} {'Colored':<10} {'Spills':<10} {'Colors':<4} | {'Time(s)':<10} {'Colored':<10} {'Spills':<10} {'Colors':<4} | {'Time(s)':<10} {'Colored':<10} {'Spills':<10} {'Colors':<4}")
    print("-"*130)
    
    for r in results:
        print(f"{r['name']:<18} | "
              f"{r['greedy']['time']:<10.6f} {r['greedy']['colored']:<10} {r['greedy']['spills']:<10} {r['greedy']['colors']:<4} | "
              f"{r['fpt']['time']:<10.6f} {r['fpt']['colored']:<10} {r['fpt']['spills']:<10} {r['fpt']['colors']:<4} | "
              f"{r['dp']['time']:<10.6f} {r['dp']['colored']:<10} {r['dp']['spills']:<10} {r['dp']['colors']:<4}")
    
    # Analysis
    print("\n" + "="*130)
    print("ANALYSIS")
    print("="*130 + "\n")
    
    greedy_wins = 0
    fpt_wins = 0
    dp_wins = 0
    
    for r in results:
        greedy_score = r['greedy']['colored'] - 3 * r['greedy']['spills']
        fpt_score = r['fpt']['colored'] - 3 * r['fpt']['spills']
        dp_score = r['dp']['colored'] - 3 * r['dp']['spills']
        
        scores = [("Greedy", greedy_score), ("FPT", fpt_score), ("DP", dp_score)]
        winner = max(scores, key=lambda x: x[1])[0]
        
        if winner == "Greedy":
            greedy_wins += 1
        elif winner == "FPT":
            fpt_wins += 1
        else:
            dp_wins += 1
        
        print(f"{r['name']}:")
        print(f"  Greedy: score={greedy_score}, time={r['greedy']['time']:.6f}s, spills={r['greedy']['spills']}")
        print(f"  FPT:    score={fpt_score}, time={r['fpt']['time']:.6f}s, spills={r['fpt']['spills']}")
        print(f"  DP:     score={dp_score}, time={r['dp']['time']:.6f}s, spills={r['dp']['spills']}")
        print(f"  → Winner: {winner}\n")
    
    print(f"Summary: Greedy {greedy_wins}, FPT {fpt_wins}, DP {dp_wins}")
    
    print("\n" + "="*100 + "\n")

    if show_plots:
        _plot_benchmark_results(results)

    return results

if __name__ == "__main__":
    run_benchmarks()
