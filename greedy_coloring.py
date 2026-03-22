def greedy_graph_coloring(graph, num_registers=4):
    """Greedy graph coloring for register allocation.

    Returns:
        tuple: (assignment, spills)
            assignment: dict[node] = register name (e.g. R1)
            spills: sorted list of nodes that could not be assigned a register
    """
    if num_registers <= 0:
        return {}, sorted(graph.nodes())

    register_names = [f"R{i + 1}" for i in range(num_registers)]

    # Degree-descending order is a simple heuristic that usually reduces spills.
    ordered_nodes = sorted(graph.nodes(), key=lambda node: graph.degree[node], reverse=True)

    assignment = {}
    spills = []

    for node in ordered_nodes:
        used_registers = {
            assignment[neighbor]
            for neighbor in graph.neighbors(node)
            if neighbor in assignment
        }

        selected_register = None
        for register in register_names:
            if register not in used_registers:
                selected_register = register
                break

        if selected_register is None:
            spills.append(node)
        else:
            assignment[node] = selected_register

    return assignment, sorted(spills)
