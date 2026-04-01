def compute_liveness(instructions):

    n = len(instructions)

    live_in = [set() for _ in range(n)]
    live_out = [set() for _ in range(n)]

    changed = True

    while changed:
        changed = False

        for i in reversed(range(n)):

            old_in = live_in[i].copy()
            old_out = live_out[i].copy()

            # live_out
            if i < n - 1:
                live_out[i] = live_in[i + 1]

            # live_in
            used = set(instructions[i].used)
            defined = {instructions[i].defined} if instructions[i].defined else set()

            live_in[i] = used.union(live_out[i] - defined)

            if old_in != live_in[i] or old_out != live_out[i]:
                changed = True

    return live_in, live_out