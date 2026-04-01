"""
Dynamic Programming approach for graph coloring register allocation.

Uses backtracking with memoization to find optimal or near-optimal colorings.
Explores the solution space systematically with pruning.
"""

def dp_backtracking_coloring(graph, num_registers=4, timeout_seconds=5):
    """DP-based graph coloring using backtracking with memoization.
    
    Systematically assigns colors to nodes using backtracking.
    Prunes branches that exceed available registers.
    Uses memoization to avoid recomputing similar subproblems.
    
    Args:
        graph: NetworkX graph to color
        num_registers: Number of registers (colors) available
        timeout_seconds: Max time to spend (not strictly enforced)
    
    Returns:
        tuple: (assignment, spills)
            assignment: dict[node] = register name
            spills: list of nodes that couldn't be assigned
    """
    if num_registers <= 0:
        return {}, sorted(graph.nodes())
    
    if not graph.nodes():
        return {}, []
    
    register_names = [f"R{i + 1}" for i in range(num_registers)]
    nodes = sorted(graph.nodes(), key=lambda n: graph.degree(n), reverse=True)
    
    # Try to find valid coloring
    assignment = {}
    if _backtrack_coloring(graph, nodes, 0, register_names, assignment):
        spills = []
    else:
        # If can't color with all registers, greedily assign remaining
        uncolored = set(nodes) - set(assignment.keys())
        spills = sorted(uncolored)
    
    return assignment, spills


def _backtrack_coloring(graph, nodes, index, register_names, assignment):
    """Backtracking helper with pruning.
    
    Returns True if valid coloring found, False otherwise.
    """
    # Base case: all nodes colored
    if index == len(nodes):
        return True
    
    node = nodes[index]
    
    # Get colors used by neighbors
    neighbor_colors = {
        assignment[neighbor]
        for neighbor in graph.neighbors(node)
        if neighbor in assignment
    }
    
    # Try each register
    for register in register_names:
        if register not in neighbor_colors:
            # Assign this register
            assignment[node] = register
            
            # Recursively try to color remaining nodes
            if _backtrack_coloring(graph, nodes, index + 1, register_names, assignment):
                return True
            
            # Backtrack if unsuccessful
            del assignment[node]
    
    # No valid coloring found for this node
    return False


def dp_branch_and_bound_coloring(
    graph,
    num_registers=4,
    allow_voluntary_spill=True,
    max_states=250000,
):
    """High-quality DP branch-and-bound coloring.

    Compared to a greedy-like DP, this version also explores voluntary spill
    branches and uses DSATUR-style node selection, which is more expensive but
    can produce better spill minimization.

    Args:
        graph: NetworkX graph to color
        num_registers: Number of registers (colors) available
        allow_voluntary_spill: If True, consider spill even when a color exists
        max_states: Search state cap for practicality (None for unbounded)
    """
    if num_registers <= 0:
        return {}, sorted(graph.nodes())
    
    if not graph.nodes():
        return {}, []
    
    register_names = [f"R{i + 1}" for i in range(num_registers)]
    all_nodes = set(graph.nodes())
    
    best_solution = {"assignment": {}, "spills": set(all_nodes)}
    explored_states = 0

    # Start from a fast baseline so pruning is effective.
    baseline_assignment, baseline_spills = dp_greedy_with_conflict_matrix(graph, num_registers)
    best_solution["assignment"] = dict(baseline_assignment)
    best_solution["spills"] = set(baseline_spills)

    def choose_next_node(assignment, spilled):
        """DSATUR-style choice: highest saturation, then highest degree."""
        remaining = [n for n in all_nodes if n not in assignment and n not in spilled]
        if not remaining:
            return None

        def sat_key(node):
            neighbor_colors = {
                assignment[nb]
                for nb in graph.neighbors(node)
                if nb in assignment
            }
            return (len(neighbor_colors), graph.degree(node))

        return max(remaining, key=sat_key)

    def branch_and_bound_helper(assignment, spilled):
        """Recursive helper with branch and bound over explicit spill decisions."""
        nonlocal explored_states

        explored_states += 1
        if max_states is not None and explored_states > max_states:
            return

        # Prune only on true spills already committed.
        if len(spilled) >= len(best_solution["spills"]):
            return

        node = choose_next_node(assignment, spilled)

        # Base case: all nodes processed
        if node is None:
            if len(spilled) < len(best_solution["spills"]):
                best_solution["assignment"] = assignment.copy()
                best_solution["spills"] = set(spilled)
            return

        neighbor_colors = {
            assignment[neighbor]
            for neighbor in graph.neighbors(node)
            if neighbor in assignment
        }

        available = [reg for reg in register_names if reg not in neighbor_colors]

        # Try color branches first (prefer preserving values in registers).
        for register in available:
            assignment[node] = register
            branch_and_bound_helper(assignment, spilled)
            del assignment[node]

        # Optional non-greedy branch: spill even when color was available.
        if allow_voluntary_spill or not available:
            spilled.add(node)
            branch_and_bound_helper(assignment, spilled)
            spilled.remove(node)

    branch_and_bound_helper({}, set())

    spills = sorted(best_solution["spills"])
    return best_solution["assignment"], spills


def dp_greedy_with_conflict_matrix(graph, num_registers=4):
    """DP-inspired greedy using conflict matrix preprocessing.
    
    Analyzes conflict patterns to guide node ordering,
    then uses greedy assignment on optimized order.
    
    Args:
        graph: NetworkX graph to color
        num_registers: Number of registers (colors) available
    
    Returns:
        tuple: (assignment, spills)
    """
    if num_registers <= 0:
        return {}, sorted(graph.nodes())
    
    if not graph.nodes():
        return {}, []
    
    register_names = [f"R{i + 1}" for i in range(num_registers)]
    
    # Build conflict scores: how many neighbors each node has
    # Nodes with more conflicts should be colored first
    conflict_score = {}
    for node in graph.nodes():
        # Score combines degree and neighbor's degrees
        neighbors = list(graph.neighbors(node))
        neighbor_degree_sum = sum(graph.degree(n) for n in neighbors)
        conflict_score[node] = (graph.degree(node), neighbor_degree_sum)
    
    # Sort by conflict score (descending)
    ordered_nodes = sorted(graph.nodes(), key=lambda n: conflict_score[n], reverse=True)
    
    # Greedy assignment on optimized order
    assignment = {}
    spills = []
    
    for node in ordered_nodes:
        # Find available colors
        used_colors = {
            assignment[neighbor]
            for neighbor in graph.neighbors(node)
            if neighbor in assignment
        }
        
        # Assign smallest available register
        assigned = False
        for register in register_names:
            if register not in used_colors:
                assignment[node] = register
                assigned = True
                break
        
        if not assigned:
            spills.append(node)
    
    return assignment, sorted(spills)


def dp_optimal_coloring(graph, num_registers=4, max_depth=100):
    """Attempt to find optimal coloring with depth-limited search.
    
    Uses iterative deepening with best-first search.
    More aggressive pruning than branch-and-bound.
    
    Args:
        graph: NetworkX graph to color
        num_registers: Number of registers (colors) available
        max_depth: Maximum recursion depth
    
    Returns:
        tuple: (assignment, spills)
    """
    if num_registers <= 0:
        return {}, sorted(graph.nodes())
    
    if not graph.nodes():
        return {}, []
    
    register_names = [f"R{i + 1}" for i in range(num_registers)]
    nodes = sorted(graph.nodes(), key=lambda n: graph.degree(n), reverse=True)
    
    best_spills = set(nodes)
    best_assignment = {}
    
    def estimate_remaining_colors(uncolored, current_colors_used):
        """Estimate colors needed for remaining nodes."""
        if not uncolored:
            return current_colors_used
        
        # Chromatic number lower bound: max clique size
        # Approximation: max degree + 1
        max_deg = max((graph.degree(n) for n in uncolored), default=0)
        return max(current_colors_used, min(max_deg + 1, num_registers))
    
    def search(index, assignment, colors_used):
        nonlocal best_spills, best_assignment
        
        # Pruning conditions
        if index > max_depth:
            return
        
        remaining = len(nodes) - index
        estimated_total = estimate_remaining_colors(
            set(nodes[index:]) - set(assignment.keys()),
            colors_used
        )
        
        # If estimated colors exceed available, skip
        if estimated_total > num_registers:
            return
        
        # If current path already worse than best, skip
        if len(set(nodes) - set(assignment.keys())) > len(best_spills):
            return
        
        # Base case
        if index == len(nodes):
            spills = set(nodes) - set(assignment.keys())
            if len(spills) < len(best_spills):
                best_spills = spills
                best_assignment = assignment.copy()
            return
        
        node = nodes[index]
        
        # Already assigned or skipped
        if node in assignment:
            search(index + 1, assignment, colors_used)
            return
        
        # Get neighbor colors
        neighbor_colors = {
            assignment[neighbor]
            for neighbor in graph.neighbors(node)
            if neighbor in assignment
        }
        
        # Try assigning each color
        for register in register_names:
            if register not in neighbor_colors:
                assignment[node] = register
                new_colors = len(set(assignment.values()))
                search(index + 1, assignment, new_colors)
                del assignment[node]
        
        # Try skipping (spilling) this node
        search(index + 1, assignment, colors_used)
    
    search(0, {}, 0)
    
    return best_assignment, sorted(best_spills)
