import random

def injecterror(bits: str, mode: str = "single", flips: int = 1) -> str:
    """
    - "single"    : flip one random bit
            - "multiple"  : flip N random bits (use flips parameter)
            - "burst"     : flip a consecutive burst of bits of length = flips
            - "drop"      : remove a random bit
            - "dup"       : duplicate a random bit
            - "swap"      : swap two random bits
        flips (int): number of bits to flip for "multiple" or length of burst for "burst"
    """
    length = len(bits)
    if length == 0:
        return bits

    bit_array = list(bits)

    if mode == "single":
        pos = random.randrange(length)
        bit_array[pos] = '1' if bit_array[pos] == '0' else '0'

    elif mode == "multiple":
        for _ in range(flips):
            pos = random.randrange(length)
            bit_array[pos] = '1' if bit_array[pos] == '0' else '0'

    elif mode == "burst":
        start = random.randrange(length)
        for i in range(start, min(start + flips, length)):
            bit_array[i] = '1' if bit_array[i] == '0' else '0'

    elif mode == "drop":
        pos = random.randrange(length)
        del bit_array[pos]

    elif mode == "dup":
        pos = random.randrange(length)
        bit_array.insert(pos, bit_array[pos])

    elif mode == "swap":
        if length > 1:
            i, j = random.sample(range(length), 2)
            bit_array[i], bit_array[j] = bit_array[j], bit_array[i]

    else:
        raise ValueError(f"Unknown error mode: {mode}")

    return "".join(bit_array)
