"""Multi-epoch benchmark analysis for register-allocation graph coloring.

Runs the synthetic benchmark multiple times with different seeds, averages the
results, and displays summary graphs for runtime and spill behavior.
"""

from collections import defaultdict

import matplotlib.pyplot as plt

from benchmark import _build_cpu_like_interference_graph, benchmark_algorithms


EPOCHS = 20
NUM_REGISTERS = 4

WORKLOADS = [
    # name, virtual regs, instructions, loop regions, branch prob, call freq, seed
    ("BasicBlock-Light", 24, 90, 1, 0.10, 1, 101),
    ("Branchy-Medium", 40, 140, 2, 0.35, 2, 202),
    ("Loop-Heavy", 56, 200, 4, 0.18, 2, 303),
    ("Call-Intensive", 72, 220, 2, 0.22, 6, 404),
    ("HotPath-Large", 96, 300, 5, 0.28, 5, 505),
]


def _score(colored, spills):
    return colored - 3 * spills


def _run_epoch(epoch_index, seed_offset=0):
    epoch_results = []

    for name, regs, inst, loops, branch_p, call_f, base_seed in WORKLOADS:
        seed = base_seed + seed_offset + epoch_index * 9973
        graph = _build_cpu_like_interference_graph(
            num_virtual_registers=regs,
            num_instructions=inst,
            loop_regions=loops,
            branch_probability=branch_p,
            call_frequency=call_f,
            seed=seed,
        )
        epoch_results.append(benchmark_algorithms(graph, num_registers=NUM_REGISTERS, name=name))

    return epoch_results


def _aggregate_results(all_epoch_results):
    totals = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    counts = defaultdict(int)

    for epoch_results in all_epoch_results:
        for result in epoch_results:
            name = result["name"]
            counts[name] += 1
            for algorithm in ("greedy", "fpt", "dp"):
                totals[name][algorithm]["time"] += result[algorithm]["time"]
                totals[name][algorithm]["colored"] += result[algorithm]["colored"]
                totals[name][algorithm]["spills"] += result[algorithm]["spills"]
                totals[name][algorithm]["colors"] += result[algorithm]["colors"]

    averaged = []
    for name, _, _, _, _, _, _ in WORKLOADS:
        count = counts[name]
        averaged.append(
            {
                "name": name,
                "greedy": {
                    "time": totals[name]["greedy"]["time"] / count,
                    "colored": totals[name]["greedy"]["colored"] / count,
                    "spills": totals[name]["greedy"]["spills"] / count,
                    "colors": totals[name]["greedy"]["colors"] / count,
                },
                "fpt": {
                    "time": totals[name]["fpt"]["time"] / count,
                    "colored": totals[name]["fpt"]["colored"] / count,
                    "spills": totals[name]["fpt"]["spills"] / count,
                    "colors": totals[name]["fpt"]["colors"] / count,
                },
                "dp": {
                    "time": totals[name]["dp"]["time"] / count,
                    "colored": totals[name]["dp"]["colored"] / count,
                    "spills": totals[name]["dp"]["spills"] / count,
                    "colors": totals[name]["dp"]["colors"] / count,
                },
            }
        )

    return averaged


def _plot_average_results(averaged_results, epochs):
    names = [result["name"] for result in averaged_results]
    x = range(len(names))
    width = 0.24

    greedy_time = [result["greedy"]["time"] for result in averaged_results]
    fpt_time = [result["fpt"]["time"] for result in averaged_results]
    dp_time = [result["dp"]["time"] for result in averaged_results]

    greedy_spills = [result["greedy"]["spills"] for result in averaged_results]
    fpt_spills = [result["fpt"]["spills"] for result in averaged_results]
    dp_spills = [result["dp"]["spills"] for result in averaged_results]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9))

    ax1.bar([i - width for i in x], greedy_time, width=width, label="Greedy", color="#1f77b4")
    ax1.bar(x, fpt_time, width=width, label="FPT Random Walk", color="#ff7f0e")
    ax1.bar([i + width for i in x], dp_time, width=width, label="DP B&B", color="#2ca02c")
    ax1.set_yscale("log")
    ax1.set_ylabel("Average runtime (seconds, log scale)")
    ax1.set_title(f"Average Runtime Across {epochs} Epochs")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(names, rotation=20, ha="right")
    ax1.grid(axis="y", alpha=0.25)
    ax1.legend(frameon=False)

    ax2.bar([i - width for i in x], greedy_spills, width=width, label="Greedy", color="#1f77b4")
    ax2.bar(x, fpt_spills, width=width, label="FPT Random Walk", color="#ff7f0e")
    ax2.bar([i + width for i in x], dp_spills, width=width, label="DP B&B", color="#2ca02c")
    ax2.set_ylabel("Average spills (lower is better)")
    ax2.set_title(f"Average Spill Counts Across {epochs} Epochs")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(names, rotation=20, ha="right")
    ax2.grid(axis="y", alpha=0.25)
    ax2.legend(frameon=False)

    plt.tight_layout()
    plt.show()


def main():
    print("\n" + "=" * 100)
    print(f"MULTI-EPOCH ANALYSIS ({EPOCHS} epochs)")
    print("=" * 100 + "\n")

    all_epoch_results = []
    for epoch_index in range(EPOCHS):
        print(f"Epoch {epoch_index + 1}/{EPOCHS}")
        all_epoch_results.append(_run_epoch(epoch_index))

    averaged_results = _aggregate_results(all_epoch_results)

    print("\nAveraged Results")
    print("-" * 100)
    for result in averaged_results:
        print(
            f"{result['name']}: "
            f"Greedy(spills={result['greedy']['spills']:.2f}, time={result['greedy']['time']:.6f}s), "
            f"FPT(spills={result['fpt']['spills']:.2f}, time={result['fpt']['time']:.6f}s), "
            f"DP(spills={result['dp']['spills']:.2f}, time={result['dp']['time']:.6f}s)"
        )
        greedy_score = _score(result["greedy"]["colored"], result["greedy"]["spills"])
        fpt_score = _score(result["fpt"]["colored"], result["fpt"]["spills"])
        dp_score = _score(result["dp"]["colored"], result["dp"]["spills"])
        winner = max(
            [("Greedy", greedy_score), ("FPT", fpt_score), ("DP", dp_score)],
            key=lambda item: item[1],
        )[0]
        print(f"  Average winner: {winner}")

    _plot_average_results(averaged_results, EPOCHS)


if __name__ == "__main__":
    main()