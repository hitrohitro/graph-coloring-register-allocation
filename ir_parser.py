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


def normalize_token(token):
    return token.strip().strip(",;()")

def parse_ir(filename):
    instructions = []

    with open(filename, "r") as f:
        for line in f:
            tokens = line.strip().split()
            normalized = [normalize_token(tok) for tok in tokens]

            if not tokens:
                continue

            # assignment
            if "=" in normalized:
                defined = normalized[0] if is_variable(normalized[0]) else None
                used = [tok for tok in normalized[2:] if is_variable(tok)]
                instructions.append(Instruction(defined, used))

            # use statement
            elif normalized[0].lower() == "use":
                used = [normalized[1]] if len(normalized) > 1 and is_variable(normalized[1]) else []
                instructions.append(Instruction(None, used))

            # load definition (e.g. "Load a")
            elif normalized[0].lower() == "load":
                defined = normalized[1] if len(normalized) > 1 and is_variable(normalized[1]) else None
                instructions.append(Instruction(defined, []))

            # single token definition (e.g. "a")
            else:
                defined = normalized[0] if len(normalized) == 1 and is_variable(normalized[0]) else None
                instructions.append(Instruction(defined, []))

    return instructions