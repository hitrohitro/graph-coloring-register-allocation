class Instruction:
    def __init__(self, defined=None, used=None):
        self.defined = defined
        self.used = used if used else []


RESERVED_TOKENS = {
    "load",
    "store",
    "mov",
    "add",
    "sub",
    "mul",
    "div",
    "use",
}


def is_variable(token):
    if not token:
        return False
    if token.lower() in RESERVED_TOKENS:
        return False
    if token.isdigit():
        return False
    return token[0].isalpha() or token[0] == "_"

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
                used = [tok for tok in tokens[2:] if is_variable(tok)]
                instructions.append(Instruction(defined, used))

            # use statement
            elif tokens[0].lower() == "use":
                used = [tokens[1]] if len(tokens) > 1 and is_variable(tokens[1]) else []
                instructions.append(Instruction(None, used))

            # load definition (e.g. "Load a")
            elif tokens[0].lower() == "load":
                defined = tokens[1] if len(tokens) > 1 and is_variable(tokens[1]) else None
                instructions.append(Instruction(defined, []))

            # single token definition (e.g. "a")
            else:
                defined = tokens[0] if len(tokens) == 1 and is_variable(tokens[0]) else None
                instructions.append(Instruction(defined, []))

    return instructions