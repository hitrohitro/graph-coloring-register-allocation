import random

from .greedy_coloring import greedy_graph_coloring

def fpt_random_walk_coloring(graph, num_registers=4, num_walks=5, walk_length=None):
    """Two-phase FPT approximation using random walks and greedy completion.

    Phase 1 (first k/2 colors):
        - non-monotone VCALP-style random-walk independent-set construction
    Phase 2 (remaining k/2 colors):
        - deterministic greedy coloring on residual graph

    This trades exactness for speed while preserving a strong baseline in phase 2.
    """
    if num_registers <= 0:
        return {}, sorted(graph.nodes())

    if not graph.nodes():
        return {}, []

    register_names = [f"R{i + 1}" for i in range(num_registers)]

    if walk_length is None:
        walk_length = max(3, int(graph.number_of_nodes() ** 0.5))

    # Approximate until k/2, then use a stronger known baseline for the rest.
    first_phase_colors = max(1, num_registers // 2)
    second_phase_colors = num_registers - first_phase_colors

    assignment = {}
    uncolored = set(graph.nodes())

    # --- Phase 1: non-monotone walk approximation for first k/2 colors ---
    for color_idx in range(first_phase_colors):
        if not uncolored:
            break

        register = register_names[color_idx]
        subgraph = graph.subgraph(uncolored)
        independent_set = _find_independent_set_vcalp_non_monotone(
            subgraph, uncolored, num_walks, walk_length
        )

        for node in independent_set:
            assignment[node] = register
            uncolored.discard(node)

    # --- Phase 2: complete with greedy on remaining k/2 colors ---
    if uncolored and second_phase_colors > 0:
        residual = graph.subgraph(uncolored).copy()
        greedy_assignment, greedy_spills = greedy_graph_coloring(residual, second_phase_colors)

        # Remap residual registers R1..Rm to global register names R(first_phase+1)..Rk
        remap = {
            f"R{i + 1}": register_names[first_phase_colors + i]
            for i in range(second_phase_colors)
        }

        for node, reg in greedy_assignment.items():
            assignment[node] = remap.get(reg, reg)

        uncolored = set(greedy_spills)

    spills = sorted(uncolored)
    return assignment, spills


def _find_independent_set_vcalp_non_monotone(graph, available_nodes, num_walks, walk_length):
    """Approximate independent set using non-monotone random walks.

    VCALP-style non-monotone behavior: allow temporary regressions (remove/add)
    to escape local optima instead of only monotonically growing the candidate set.
    """
    if not available_nodes:
        return set()

    best_independent_set = set()

    greedy_set = _greedy_independent_set(graph, available_nodes)
    if len(greedy_set) > len(best_independent_set):
        best_independent_set = greedy_set

    for _ in range(num_walks):
        start_node = random.choice(list(available_nodes))
        independent_set = _single_non_monotone_walk(graph, start_node, available_nodes, walk_length)

        if len(independent_set) > len(best_independent_set):
            best_independent_set = independent_set

    return best_independent_set


def _greedy_independent_set(graph, available_nodes):
    """Greedily construct an independent set by selecting low-degree nodes first."""
    independent_set = set()
    candidates = set(available_nodes)

    sorted_nodes = sorted(candidates, key=lambda n: graph.degree(n))

    for node in sorted_nodes:
        neighbors_in_set = {n for n in independent_set if graph.has_edge(node, n)}

        if not neighbors_in_set:
            independent_set.add(node)

    return independent_set


def _single_non_monotone_walk(graph, start_node, available_nodes, walk_length):
    """Non-monotone walk: allows temporary remove/add moves to escape local optima."""
    current_set = set()
    best_set = set()
    current = start_node
    visited = set()

    for _ in range(walk_length):
        if current in available_nodes:
            conflicts = {node for node in current_set if graph.has_edge(current, node)}

            if not conflicts:
                current_set.add(current)
            else:
                # Non-monotone step: with small probability, swap out one conflict.
                if random.random() < 0.35:
                    evicted = random.choice(list(conflicts))
                    current_set.remove(evicted)
                    if not any(graph.has_edge(current, node) for node in current_set):
                        current_set.add(current)

            if len(current_set) > len(best_set):
                best_set = set(current_set)

        neighbors = list(graph.neighbors(current))
        neighbors = [n for n in neighbors if n in available_nodes and n not in visited]

        if neighbors:
            if len(neighbors) <= 2:
                current = min(neighbors, key=lambda n: graph.degree(n))
            else:
                current = random.choice(neighbors)
            visited.add(current)
        else:
            candidates = list(available_nodes - visited)
            if candidates:
                current = random.choice(candidates)
                visited.add(current)
            else:
                break

    return best_set


def fpt_random_walk_coloring_enhanced(
    graph,
    num_registers=4,
    num_iterations=10,
    seed=None,
    fast_mode=True,
    max_extra_spills=1,
):
    """Enhanced FPT approximation with multiple restarts and local optimization.

    Performs multiple attempts and returns the best coloring found.
    Phase split behavior is handled inside fpt_random_walk_coloring().
    """
    if seed is not None:
        random.seed(seed)

    # Warm-start from greedy: strong speed baseline and spill guardrail reference.
    greedy_assignment, greedy_spills = greedy_graph_coloring(graph, num_registers)
    if len(greedy_spills) == 0:
        return greedy_assignment, greedy_spills

    n = graph.number_of_nodes()
    if fast_mode:
        num_iterations = min(num_iterations, max(3, min(6, (n // 25) + 3)))
        base_walk_length = max(3, int((n ** 0.5) * 0.6))
    else:
        base_walk_length = None

    best_assignment = dict(greedy_assignment)
    best_spills = list(greedy_spills)
    best_quality = float("-inf")

    for iteration in range(num_iterations):
        if fast_mode:
            num_walks = min(4, 2 + iteration)
            walk_length = base_walk_length
        else:
            num_walks = max(2, (iteration // 2) + 3)
            walk_length = None

        assignment, spills = fpt_random_walk_coloring(
            graph,
            num_registers,
            num_walks=num_walks,
            walk_length=walk_length,
        )

        # Penalize high spill growth over greedy to keep practical competitiveness.
        spill_over_greedy = max(0, len(spills) - len(greedy_spills))
        quality = len(assignment) - 3 * len(spills) - 4 * spill_over_greedy

        if quality > best_quality:
            best_quality = quality
            best_assignment = assignment
            best_spills = spills

        # Early exit when close-to-greedy spill quality is reached.
        if len(spills) <= len(greedy_spills) + max_extra_spills:
            break

    # Hard guardrail: do not return significantly worse spill count than greedy.
    if len(best_spills) > len(greedy_spills) + max_extra_spills:
        return greedy_assignment, greedy_spills

    return best_assignment, sorted(best_spills)
