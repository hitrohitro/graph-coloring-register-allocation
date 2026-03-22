import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Patch

def draw_graph(G, assignment=None, spills=None, show_labels=False):
    if assignment is None:
        assignment = {}
    if spills is None:
        spills = []

    plt.figure(figsize=(10, 7))

    pos = nx.kamada_kawai_layout(G)

    palette = {
        "R1": "#1f77b4",
        "R2": "#2ca02c",
        "R3": "#ff7f0e",
        "R4": "#d62728",
    }

    node_colors = []
    for node in G.nodes():
        if node in spills:
            node_colors.append("#7f7f7f")
        else:
            node_colors.append(palette.get(assignment.get(node), "#aec7e8"))

    nx.draw_networkx_edges(
        G,
        pos,
        edge_color="#7a7a7a",
        alpha=0.28,
        width=0.9,
        connectionstyle="arc3,rad=0.08",
    )

    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=1200,
        node_color=node_colors,
        edgecolors="#1a1a1a",
        linewidths=1.2,
    )

    if show_labels:
        label_nodes = {node: str(node) for node in G.nodes()}
    else:
        label_nodes = {node: str(node) for node in spills}

    nx.draw_networkx_labels(
        G,
        pos,
        labels=label_nodes,
        font_size=9,
        font_color="#111111",
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 0.2},
    )

    legend_items = [
        Patch(facecolor="#1f77b4", edgecolor="#1a1a1a", label="R1"),
        Patch(facecolor="#2ca02c", edgecolor="#1a1a1a", label="R2"),
        Patch(facecolor="#ff7f0e", edgecolor="#1a1a1a", label="R3"),
        Patch(facecolor="#d62728", edgecolor="#1a1a1a", label="R4"),
        Patch(facecolor="#7f7f7f", edgecolor="#1a1a1a", label="SPILL"),
    ]
    plt.legend(
        handles=legend_items,
        title="Node Color",
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        frameon=False,
    )

    plt.title("Interference Graph with Greedy Register Coloring", fontsize=13)
    plt.axis("off")
    plt.tight_layout(rect=(0, 0, 0.82, 1))
    plt.show()