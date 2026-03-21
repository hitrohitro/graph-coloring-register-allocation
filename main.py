from ir_parser import parse_ir
from liveness import compute_liveness
from interference_graph import build_interference_graph

instructions = parse_ir("ir.txt")

live_in, live_out = compute_liveness(instructions)

print("Liveness Results\n")

for i in range(len(instructions)):
    print(f"Instruction {i}")
    print("LIVE_IN :", live_in[i])
    print("LIVE_OUT:", live_out[i])
    print()

G = build_interference_graph(instructions, live_out)

print("Interference Graph Edges\n")
for edge in G.edges():
    print(edge)