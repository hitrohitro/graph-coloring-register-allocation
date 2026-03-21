class Instruction:
    def __init__(self, defined=None, used=None):
        self.defined = defined
        self.used = used if used else []

def parse_ir(filename):
    instructions = []

    with open(filename, "r") as f:
        for line in f:
            tokens = line.strip().split()

            if not tokens:
                continue

            # assignment
            if "=" in tokens:
                defined = tokens[0]
                used = tokens[2:]
                instructions.append(Instruction(defined, used))

            # use statement
            elif tokens[0] == "use":
                instructions.append(Instruction(None, [tokens[1]]))

            # load definition
            else:
                instructions.append(Instruction(tokens[0], []))

    return instructions