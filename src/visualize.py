import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Patch

def draw_graph(G, assignment=None, spills=None, show_labels=False, title="Register Allocation"):
    """Draw a single graph coloring result."""
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

    plt.title(title, fontsize=13)
    plt.axis("off")
    plt.tight_layout(rect=(0, 0, 0.82, 1))
    plt.show()


def draw_comparison(
    G,
    greedy_assignment,
    greedy_spills,
    fpt_assignment,
    fpt_spills,
    dp_assignment,
    dp_spills,
    show_labels=False,
):
    """Draw Greedy/FPT/DP allocation graphs in one window."""

    palette = {
        "R1": "#1f77b4",
        "R2": "#2ca02c",
        "R3": "#ff7f0e",
        "R4": "#d62728",
    }

    def node_colors(assignment, spills):
        colors = []
        for node in G.nodes():
            if node in spills:
                colors.append("#7f7f7f")
            else:
                colors.append(palette.get(assignment.get(node), "#aec7e8"))
        return colors

    def draw_algo(ax, title, assignment, spills, pos):
        nx.draw_networkx_edges(
            G,
            pos,
            ax=ax,
            edge_color="#7a7a7a",
            alpha=0.28,
            width=0.9,
        )
        nx.draw_networkx_nodes(
            G,
            pos,
            ax=ax,
            node_size=900,
            node_color=node_colors(assignment, spills),
            edgecolors="#1a1a1a",
            linewidths=1.0,
        )

        if show_labels:
            labels = {node: str(node) for node in G.nodes()}
        else:
            labels = {node: str(node) for node in spills}

        nx.draw_networkx_labels(
            G,
            pos,
            labels=labels,
            ax=ax,
            font_size=8,
            font_color="#111111",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.75, "pad": 0.15},
        )
        ax.set_title(f"{title} (Spills: {len(spills)})", fontsize=11, fontweight="bold")
        ax.axis("off")

    if G.number_of_nodes() == 0:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "Interference graph is empty", ha="center", va="center", fontsize=12)
        ax.axis("off")
        plt.tight_layout()
        plt.show()
        return

    pos = nx.kamada_kawai_layout(G)

    fig = plt.figure(figsize=(18, 7))
    gs = fig.add_gridspec(1, 3)

    ax_greedy = fig.add_subplot(gs[0, 0])
    ax_fpt = fig.add_subplot(gs[0, 1])
    ax_dp = fig.add_subplot(gs[0, 2])

    draw_algo(ax_greedy, "Greedy", greedy_assignment, greedy_spills, pos)
    draw_algo(ax_fpt, "FPT Random Walk", fpt_assignment, fpt_spills, pos)
    draw_algo(ax_dp, "DP Branch-and-Bound", dp_assignment, dp_spills, pos)

    legend_items = [
        Patch(facecolor="#1f77b4", edgecolor="#1a1a1a", label="R1"),
        Patch(facecolor="#2ca02c", edgecolor="#1a1a1a", label="R2"),
        Patch(facecolor="#ff7f0e", edgecolor="#1a1a1a", label="R3"),
        Patch(facecolor="#d62728", edgecolor="#1a1a1a", label="R4"),
        Patch(facecolor="#7f7f7f", edgecolor="#1a1a1a", label="SPILL"),
    ]

    fig.legend(
        handles=legend_items,
        title="Register Assignment",
        loc="upper center",
        bbox_to_anchor=(0.5, 0.98),
        ncol=5,
        frameon=False,
    )

    fig.suptitle("Interference Graph Coloring Dashboard", fontsize=15, fontweight="bold", y=0.995)
    plt.tight_layout(rect=(0, 0, 1, 0.95))
    plt.show()

