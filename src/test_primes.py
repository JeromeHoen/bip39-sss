"""
Check that PRIME numbers used to generate shares are the biggest possible for the number of bits chosen.
Based on Miller-Rabin test: https://en.wikipedia.org/wiki/Miller%E2%80%93Rabin_primality_test
Implementation source: https://gist.github.com/Ayrx/5884790
"""

import random

from utils import PRIMES

def miller_rabin(n, k):
    """Implementation uses the Miller-Rabin Primality Test
    The optimal number of rounds for this test is 40
    See http://stackoverflow.com/questions/6325576/how-many-iterations-of-rabin-miller-should-i-use-for-cryptographic-safe-primes
    for justification.
    """

    if n == 2 or n == 3:
        return True

    if n % 2 == 0:
        return False

    r, s = 0, n - 1
    while s % 2 == 0:
        r += 1
        s //= 2
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, s, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


for bits, prime in PRIMES.items():
    # Let's pick k=100 beacause there are few numbers to check.
    prime_is_verified = miller_rabin(prime, 100)
    no_prime_in_range = [miller_rabin(i, 100) for i in range(prime + 1, 2**bits)]
    assert prime_is_verified and not any(no_prime_in_range)
    print(f"Biggest prime under {bits} bits is verified!")