import matplotlib.pyplot as plt
import networkx as nx

def draw_graph(G):
    plt.figure(figsize=(6,6))

    pos = nx.spring_layout(G)

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=2000,
        font_size=12
    )

    plt.title("Interference Graph", fontsize=14)
    plt.show()