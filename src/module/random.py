import random

def random_binary(probability: float) -> bool:
    """Returns True with the provided probability in [0.0, 1.0]."""
    return random.random() < probability
