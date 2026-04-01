import networkx as nx

def build_interference_graph(instructions, live_out):

    G = nx.Graph()

    for i, inst in enumerate(instructions):

        if inst.defined is None:
            continue

        defined = inst.defined

        G.add_node(defined)

        for var in live_out[i]:
            if var != defined:
                G.add_edge(defined, var)

    return G