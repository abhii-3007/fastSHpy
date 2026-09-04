import random

def simulate_typo(word: str) -> str:
    """
    Simulates a human typing error by swapping two adjacent characters.
    Only applies to names 4 characters or longer.
    """
    if len(word) < 4:
        return word
        
    arr = list(word)
    idx = random.randint(1, len(arr) - 3)
    arr[idx], arr[idx + 1] = arr[idx + 1], arr[idx]
    
    return "".join(arr)
