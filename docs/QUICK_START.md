# Quick Start Guide

## Run Everything

### Full Pipeline (Recommended)

```bash
python main.py
```

This will:

1. Use `ir.txt` based on the selected IR mode (`auto` or `custom`)
2. Parse IR code and compute liveness
3. Build interference graph
4. Run Greedy, FPT, and DP allocation
5. Display detailed comparison metrics
6. Show allocation visualization (interactive session)
7. Stop after the single-IR allocation run

### Run with Custom IR File

```bash
python main.py --ir-mode custom --ir-file ir.txt
```

### Auto-Generate IR First, Then Allocate

```bash
python main.py --ir-mode auto
```

This writes generated IR to `ir.txt` first, then runs allocation.

### Auto-Generate IR with Custom Settings

```bash
python main.py --ir-mode auto --auto-instructions 30 --auto-variables 8 --auto-seed 11
```

### Run Benchmarks on Synthetic Graphs

```bash
python benchmark.py
```

This will:

1. Generate graphs of increasing size
2. Run Greedy, FPT, and DP on each
3. Display scaling analysis
4. Print per-workload comparison metrics

### Run Multi-Epoch Analysis

```bash
python analysis.py
```

This will:

1. Run the synthetic benchmark for 20 epochs by default
2. Average runtime and spill metrics across seeds
3. Display a final summary graph

## Understanding the Output

### Comparison Metrics Example

```
Metric                         Greedy               FPT Random Walk
----------------------------------------------------------------------
Time (seconds)                 0.000043             0.033528
Nodes Colored                  12                   11
Spills                         1                    2
Colors Used                    4                    4
Quality Score                  10                   7
```

**What it means:**

- **Time**: Execution speed (Greedy is ~800x faster)
- **Nodes Colored**: Variables assigned to registers successfully
- **Spills**: Variables that had to use memory instead (overhead)
- **Colors Used**: Number of distinct registers needed
- **Quality Score**: Custom metric favoring fewer spills

### Result Selection

- Lower spills = better (preferred 3x more than extra colored nodes)
- Time matters for real-world compilation
- Quality Score = colored_nodes - 3×spills

## Algorithm Quick Comparison

| Feature       | Greedy                 | FPT Random Walk         |
| ------------- | ---------------------- | ----------------------- |
| Speed         | ⚡ 1-2 microseconds    | 🐢 10-100+ milliseconds |
| Quality       | ⭐⭐⭐⭐⭐ (Excellent) | ⭐⭐⭐⭐ (Good)         |
| Deterministic | ✓ Yes                  | ✗ No (stochastic)       |
| Best For      | Production use         | Research/comparison     |
| Graph size    | < 1000 nodes           | < 500 nodes             |
| Code clarity  | Simple                 | More complex            |

## When to Use Each

### Use Greedy for:

```python
from greedy_coloring import greedy_graph_coloring

assignment, spills = greedy_graph_coloring(graph, num_registers=4)
# Fastest option, excellent results
```

- Compilers (needs to be fast)
- Large graphs (1000+ nodes)
- Production code
- When speed matters

### Use FPT for:

```python
from fpt_random_walk_coloring import fpt_random_walk_coloring_enhanced

assignment, spills = fpt_random_walk_coloring_enhanced(
    graph, num_registers=4, num_iterations=15, seed=42
)
# Slower but explores solution space
```

- Research/academic work
- Small to medium graphs (< 500 nodes)
- Offline optimization
- When quality matters more than speed

### Compare Both:

```python
from algorithm_comparison import compare_algorithms

results = compare_algorithms(graph, num_registers=4, verbose=True)

# Results has both algorithms' outputs and metrics
greedy_spills = results["greedy"]["num_spills"]
fpt_spills = results["fpt_random_walk"]["num_spills"]
```

## Customizing the FPT Algorithm

### Make it Faster (fewer iterations)

```python
# Default is 10 iterations - reduce for speed
assignment, spills = fpt_random_walk_coloring_enhanced(
    graph, num_registers=4, num_iterations=5, seed=42
)
```

### Make it More Thorough (more iterations)

```python
# More iterations = better quality but slower
assignment, spills = fpt_random_walk_coloring_enhanced(
    graph, num_registers=4, num_iterations=30, seed=None
)
```

### Make it Reproducible

```python
# Use a seed for consistent results
assignment, spills = fpt_random_walk_coloring_enhanced(
    graph, num_registers=4, seed=42
)
```

### Adjust Number of Registers

```python
# Available registers in your system
assignment, spills = greedy_graph_coloring(graph, num_registers=8)

# More registers = fewer spills but less pressure
```

## Example Workflow

```python
# Step 1: Parse IR and build interference graph
from ir_parser import parse_ir
from liveness import compute_liveness
from interference_graph import build_interference_graph

instructions = parse_ir("ir.txt")
live_in, live_out = compute_liveness(instructions)
G = build_interference_graph(instructions, live_out)

# Step 2: Run both algorithms
from algorithm_comparison import compare_algorithms

results = compare_algorithms(G, num_registers=4)

# Step 3: Choose the better result
if results["greedy"]["num_spills"] <= results["fpt_random_walk"]["num_spills"]:
    print("Use Greedy algorithm results")
    assignment = results["greedy"]["assignment"]
else:
    print("Use FPT algorithm results")
    assignment = results["fpt_random_walk"]["assignment"]

# Step 4: Visualize (if needed)
from visualize import draw_comparison

draw_comparison(
    G,
    results["greedy"]["assignment"],
    results["greedy"]["spills"],
    results["fpt_random_walk"]["assignment"],
    results["fpt_random_walk"]["spills"]
)
```

## Key Insights from Benchmarks

1. **Greedy dominates runtime** on all test cases
2. **FPT can reduce spills** on some medium/hard graphs
3. **DP is strongest on quality** but costs much more time
4. **Analysis.py is the best way** to compare averaged behavior across seeds

## Troubleshooting

### Visualization Not Showing

- Running in non-interactive mode? That's normal
- Script will skip plotting automatically
- Use `benchmark.py` for complete testing instead

### Too Many Spills

- Reduce number of registers? That's expected trade-off
- Try FPT algorithm for harder instances
- Check if graph is highly connected (chaotic interference)

### Algorithm Taking Too Long

- Using FPT? Reduce `num_iterations` parameter
- Graph too large? Stick with Greedy
- Using on laptop? Greedy is still very fast

## File Reference

**Run these:**

- `python main.py` - Main comparison
- `python benchmark.py` - Performance analysis
- `python analysis.py` - Multi-epoch averaged benchmark analysis

**Import from:**

```python
from greedy_coloring import greedy_graph_coloring
from fpt_random_walk_coloring import fpt_random_walk_coloring_enhanced
from algorithm_comparison import compare_algorithms
from visualize import draw_comparison
```

**Read these:**

- `IMPLEMENTATION_SUMMARY.md` - What was added
- `README_ALGORITHMS.md` - Deep dive into algorithms

---

**Need Help?** Run `python -c "from fpt_random_walk_coloring import fpt_random_walk_coloring_enhanced; help(fpt_random_walk_coloring_enhanced)"`
