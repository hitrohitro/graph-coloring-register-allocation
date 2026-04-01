"""Research-grade multi-epoch analysis for register-allocation benchmarking.

Adds:
- confidence intervals and standard deviation reporting
- paired sign tests on per-run quality scores
- register-budget sweep (2, 4, 8, 16)
- focused workload bars with 95% CI for a selected budget
"""

from collections import defaultdict
from math import comb, sqrt
import statistics

import matplotlib.pyplot as plt

from benchmark import _build_cpu_like_interference_graph, benchmark_algorithms


EPOCHS = 2
REGISTER_BUDGETS = [2, 4, 8, 16]
FOCUS_BUDGET = 4

ALGORITHMS = {
    "greedy": {"label": "Greedy", "color": "#1f77b4"},
    "fpt": {"label": "FPT Random Walk", "color": "#ff7f0e"},
    "dp": {"label": "DP B&B", "color": "#2ca02c"},
}

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


def _run_epoch(epoch_index, num_registers, seed_offset=0):
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
        epoch_results.append(
            benchmark_algorithms(graph, num_registers=num_registers, name=name)
        )

    return epoch_results


def _init_series_store():
    return defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )
    )


def _append_epoch_results(series_store, epoch_results, num_registers):
    for result in epoch_results:
        name = result["name"]
        for algorithm in ALGORITHMS:
            series_store[num_registers][name][algorithm]["time"].append(
                result[algorithm]["time"]
            )
            series_store[num_registers][name][algorithm]["colored"].append(
                result[algorithm]["colored"]
            )
            series_store[num_registers][name][algorithm]["spills"].append(
                result[algorithm]["spills"]
            )
            series_store[num_registers][name][algorithm]["colors"].append(
                result[algorithm]["colors"]
            )
            score = _score(result[algorithm]["colored"], result[algorithm]["spills"])
            series_store[num_registers][name][algorithm]["score"].append(score)


def _mean_std_ci95(values):
    n = len(values)
    if n == 0:
        return {"mean": 0.0, "std": 0.0, "ci95": 0.0, "n": 0}

    mean = statistics.mean(values)
    if n == 1:
        return {"mean": mean, "std": 0.0, "ci95": 0.0, "n": 1}

    std = statistics.stdev(values)
    ci95 = 1.96 * std / sqrt(n)
    return {"mean": mean, "std": std, "ci95": ci95, "n": n}


def _aggregate_results(series_store):
    summary = defaultdict(lambda: defaultdict(dict))
    for num_registers in REGISTER_BUDGETS:
        for name, _, _, _, _, _, _ in WORKLOADS:
            for algorithm in ALGORITHMS:
                summary[num_registers][name][algorithm] = {
                    metric: _mean_std_ci95(
                        series_store[num_registers][name][algorithm][metric]
                    )
                    for metric in ("time", "colored", "spills", "colors", "score")
                }
    return summary


def _paired_sign_test(series_a, series_b):
    wins_a = 0
    wins_b = 0
    for a_value, b_value in zip(series_a, series_b):
        if a_value > b_value:
            wins_a += 1
        elif b_value > a_value:
            wins_b += 1

    non_ties = wins_a + wins_b
    if non_ties == 0:
        return 1.0, wins_a, wins_b, non_ties

    smaller_tail = min(wins_a, wins_b)
    tail_prob = 0.0
    for i in range(smaller_tail + 1):
        tail_prob += comb(non_ties, i) * (0.5 ** non_ties)

    p_value = min(1.0, 2.0 * tail_prob)
    return p_value, wins_a, wins_b, non_ties


def _run_significance_report(series_store):
    print("\nPaired Sign Tests on Quality Score (higher score is better)")
    print("-" * 100)
    comparisons = [("dp", "fpt"), ("fpt", "greedy"), ("dp", "greedy")]

    for num_registers in REGISTER_BUDGETS:
        print(f"Register budget {num_registers}:")
        for better, worse in comparisons:
            better_values = []
            worse_values = []
            for name, _, _, _, _, _, _ in WORKLOADS:
                better_values.extend(series_store[num_registers][name][better]["score"])
                worse_values.extend(series_store[num_registers][name][worse]["score"])

            p_value, wins_better, wins_worse, non_ties = _paired_sign_test(
                better_values, worse_values
            )
            print(
                f"  {ALGORITHMS[better]['label']} vs {ALGORITHMS[worse]['label']}: "
                f"wins={wins_better}-{wins_worse}, n={non_ties}, p={p_value:.6f}"
            )


def _print_workload_report(summary, num_registers):
    print(f"\nDetailed workload report for register budget {num_registers}")
    print("-" * 100)
    for name, _, _, _, _, _, _ in WORKLOADS:
        line_parts = [name + ":"]
        for algorithm in ALGORITHMS:
            spills = summary[num_registers][name][algorithm]["spills"]
            runtime = summary[num_registers][name][algorithm]["time"]
            line_parts.append(
                f"{ALGORITHMS[algorithm]['label']}(spills={spills['mean']:.2f}±{spills['ci95']:.2f}, "
                f"time={runtime['mean']:.6f}s±{runtime['ci95']:.6f})"
            )
        print(" ".join(line_parts))


def _print_budget_summary(summary):
    print("\nBudget sweep summary (means across workloads)")
    print("-" * 100)
    for num_registers in REGISTER_BUDGETS:
        print(f"Registers={num_registers}")
        for algorithm in ALGORITHMS:
            mean_spills = statistics.mean(
                summary[num_registers][name][algorithm]["spills"]["mean"]
                for name, _, _, _, _, _, _ in WORKLOADS
            )
            mean_time = statistics.mean(
                summary[num_registers][name][algorithm]["time"]["mean"]
                for name, _, _, _, _, _, _ in WORKLOADS
            )
            print(
                f"  {ALGORITHMS[algorithm]['label']}: "
                f"avg_spills={mean_spills:.2f}, avg_time={mean_time:.6f}s"
            )


def _plot_focus_budget(summary, num_registers, epochs):
    names = [name for name, _, _, _, _, _, _ in WORKLOADS]
    x = list(range(len(names)))
    width = 0.24

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9))

    for idx, algorithm in enumerate(ALGORITHMS):
        offset = (idx - 1) * width
        means_time = [summary[num_registers][name][algorithm]["time"]["mean"] for name in names]
        ci_time = [summary[num_registers][name][algorithm]["time"]["ci95"] for name in names]
        means_spills = [
            summary[num_registers][name][algorithm]["spills"]["mean"] for name in names
        ]
        ci_spills = [
            summary[num_registers][name][algorithm]["spills"]["ci95"] for name in names
        ]
        positions = [value + offset for value in x]

        ax1.bar(
            positions,
            means_time,
            width=width,
            label=ALGORITHMS[algorithm]["label"],
            color=ALGORITHMS[algorithm]["color"],
            yerr=ci_time,
            capsize=3,
        )
        ax2.bar(
            positions,
            means_spills,
            width=width,
            label=ALGORITHMS[algorithm]["label"],
            color=ALGORITHMS[algorithm]["color"],
            yerr=ci_spills,
            capsize=3,
        )

    ax1.set_yscale("log")
    ax1.set_ylabel("Runtime mean ± 95% CI (seconds, log scale)")
    ax1.set_title(
        f"Runtime by Workload at {num_registers} Registers ({epochs} Epochs, 95% CI)"
    )
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, rotation=20, ha="right")
    ax1.grid(axis="y", alpha=0.25)
    ax1.legend(frameon=False)

    ax2.set_ylabel("Spills mean ± 95% CI (lower is better)")
    ax2.set_title(
        f"Spills by Workload at {num_registers} Registers ({epochs} Epochs, 95% CI)"
    )
    ax2.set_xticks(x)
    ax2.set_xticklabels(names, rotation=20, ha="right")
    ax2.grid(axis="y", alpha=0.25)
    ax2.legend(frameon=False)

    plt.tight_layout()


def _plot_budget_sweep(summary, epochs):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    for algorithm in ALGORITHMS:
        mean_runtime_by_budget = []
        mean_spills_by_budget = []
        for num_registers in REGISTER_BUDGETS:
            mean_runtime_by_budget.append(
                statistics.mean(
                    summary[num_registers][name][algorithm]["time"]["mean"]
                    for name, _, _, _, _, _, _ in WORKLOADS
                )
            )
            mean_spills_by_budget.append(
                statistics.mean(
                    summary[num_registers][name][algorithm]["spills"]["mean"]
                    for name, _, _, _, _, _, _ in WORKLOADS
                )
            )

        ax1.plot(
            REGISTER_BUDGETS,
            mean_runtime_by_budget,
            marker="o",
            linewidth=2,
            label=ALGORITHMS[algorithm]["label"],
            color=ALGORITHMS[algorithm]["color"],
        )
        ax2.plot(
            REGISTER_BUDGETS,
            mean_spills_by_budget,
            marker="o",
            linewidth=2,
            label=ALGORITHMS[algorithm]["label"],
            color=ALGORITHMS[algorithm]["color"],
        )

    ax1.set_title(f"Runtime Scaling vs Register Budget ({epochs} Epochs)")
    ax1.set_xlabel("Physical registers available")
    ax1.set_ylabel("Mean runtime across workloads (seconds)")
    ax1.set_yscale("log")
    ax1.grid(alpha=0.25)
    ax1.legend(frameon=False)

    ax2.set_title(f"Spill Scaling vs Register Budget ({epochs} Epochs)")
    ax2.set_xlabel("Physical registers available")
    ax2.set_ylabel("Mean spills across workloads")
    ax2.grid(alpha=0.25)
    ax2.legend(frameon=False)

    plt.tight_layout()


def main():
    print("\n" + "=" * 100)
    print(f"RESEARCH-GRADE MULTI-EPOCH ANALYSIS ({EPOCHS} epochs)")
    print(f"Register budgets: {REGISTER_BUDGETS}")
    print("=" * 100 + "\n")

    series_store = _init_series_store()
    for epoch_index in range(EPOCHS):
        print(f"Epoch {epoch_index + 1}/{EPOCHS}")
        for num_registers in REGISTER_BUDGETS:
            epoch_results = _run_epoch(epoch_index, num_registers=num_registers)
            _append_epoch_results(series_store, epoch_results, num_registers)

    summary = _aggregate_results(series_store)

    _print_workload_report(summary, num_registers=FOCUS_BUDGET)
    _print_budget_summary(summary)
    _run_significance_report(series_store)

    _plot_focus_budget(summary, num_registers=FOCUS_BUDGET, epochs=EPOCHS)
    _plot_budget_sweep(summary, epochs=EPOCHS)
    plt.show()


if __name__ == "__main__":
    main()