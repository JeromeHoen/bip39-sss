from utils import recover_seed
from utils import PRIMES, PRIMES_STR
from utils import STRENGTH_ALLOWED, STRENGTH_STR
from utils import LENGTH_ALLOWED, LENGTH_STR

# 12 words = 128 bits
# 15 words = 160 bits
# 18 words = 192 bits
# 21 words = 224 bits
# 24 words = 256 bits

def safe_prime_eval(expression):
    """Evaluate expression for prime numbers"""

    allowed_chars = "0123456789 +-*()^"
    for char in expression:
        if char not in allowed_chars:
            raise ValueError("Invalid math expression for a prime number")

    return int(eval(expression.replace("^", "**")))

def pretty_print_prime(prime, primes_str=PRIMES_STR):
    """Pretty print for primes commonly used"""
    for prime_str in primes_str.values():
        if eval(prime_str.replace("^", "**")) == prime:
            return prime_str
    return prime


if __name__ == "__main__":
    
    print("")
    print("Seed strength in bits:")
    print("128 bits -> 12 words")
    print("160 bits -> 15 words")
    print("192 bits -> 18 words")
    print("224 bits -> 21 words")
    print("256 bits -> 24 words")
    print("[OPTIONAL: Press ENTER if it's the same as the shares]:")
    seed_strength = input()
    if seed_strength:
        seed_strength = int(seed_strength)

    if seed_strength and seed_strength not in STRENGTH_ALLOWED:
        raise ValueError(
            "Strength must be one of the following "
            "%s, but it is not (%d)." % (STRENGTH_STR, seed_strength)
        )

    print("Prime number used?")
    print("[OPTIONAL: Press ENTER for default]:")
    prime = input()
    if prime:
        prime = safe_prime_eval(prime)

    shares = []
    while True:
        share_index = input("Share number (Press ENTER if done): ")
        if not share_index:
            break
        else:
            share_index = int(share_index)
        
        share_seed = input("Seed phrase for share #%d: " % share_index)
        if not share_seed:
            break
        else:
            len_share = len(share_seed.split(" "))
            if len_share not in LENGTH_ALLOWED:
                raise ValueError(
                    "Number of words must be one of the following: "
                    "%s, but it is not (%d)." % (LENGTH_STR, len_share)
                )

        shares.append([share_index, share_seed])

        # if not provided, assume the seed's strength is the same
        # as the shares'
        share_strength = len_share // 3 * 32
        if not seed_strength:
            seed_strength = share_strength
        if not prime:
            prime = PRIMES[share_strength]

    if not shares:
        print("Exit program")
        exit()

    recovered_seed = recover_seed(shares, seed_strength, prime)

    print("")
    print("Prime used: %s" % pretty_print_prime(prime, PRIMES_STR))
    print("Shares used:")
    for i, share in shares:
        print("%d: %s" % (i, share))
    print("")
    print("Seed phrase recovered: %s" % recovered_seed)
