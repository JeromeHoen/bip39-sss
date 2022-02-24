"""
Modified from the Wikipedia page on Shamir's secret sharing:
https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing
"""

from secrets import SystemRandom
from functools import partial

from mnemonic import Mnemonic

# Biggest primes under a power of two corresponding to the strengths accepted
# in BIP39 (https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
# for this application we want a known prime number as close as
# possible to our security level; e.g.  desired security level of 128
# bits to have a level of security as close as the entropy of the seed

# source for the primes: https://primes.utm.edu/lists/2small/
PRIMES = {
    128: 2**128 - 159, # 128 bits = 12 words
    160: 2**160 - 47,  # 160 bits = 15 words
    192: 2**192 - 237, # 192 bits = 18 words
    224: 2**224 - 63,  # 224 bits = 21 words
    256: 2**256 - 189  # 256 bits = 24 words
}

# to avoid printing huge numbers proned to copy/paste mistakes
PRIMES_STR = {
    128: "2^128 - 159", # 128 bits = 12 words
    160: "2^160 - 47",  # 160 bits = 15 words
    192: "2^192 - 237", # 192 bits = 18 words
    224: "2^224 - 63",  # 224 bits = 21 words
    256: "2^256 - 189"  # 256 bits = 24 words
}

STRENGTH_ALLOWED = [128, 160, 192, 224, 256]
STRENGTH_STR = "128, 160, 192, 224 or 256"

LENGTH_ALLOWED =  [12, 15, 18, 21, 24]
LENGTH_STR = "12, 15, 18, 21 or 24"


random_int = partial(SystemRandom().randint, 0)

def int_to_seed(number, mnemo=Mnemonic("english"), strength=256):
    if strength not in STRENGTH_ALLOWED:
        raise ValueError(
            "Strength should be one of the following: %s. But it is not (%d)."
            % (STRENGTH_STR, strength)
        )
    entropy_as_bytes = int.to_bytes(number, length=strength//8, byteorder="big")
    return mnemo.to_mnemonic(entropy_as_bytes)

def seed_to_int(seed, mnemo=Mnemonic("english"), strength=256):
    if strength not in STRENGTH_ALLOWED:
        raise ValueError(
            "Strength should be one of the following %s. But it is not (%d)."
            % (STRENGTH_STR, strength)
        )
    entropy = mnemo.to_entropy(seed)
    return int.from_bytes(entropy, "big")

def _eval_at(poly, x, prime):
    """Evaluates polynomial (coefficient tuple) at x, used to generate a
    shamir pool in make_random_shares below.
    """
    accum = 0
    for coeff in reversed(poly):
        accum *= x
        accum += coeff
        accum %= prime
    return accum

def make_random_shares(seed, minimum, n_shares, share_strength=256):
    """
    Generates a random shamir pool for a given seed phrase.
    Returns share points as seeds phrases (word list).
    """
    if minimum > n_shares:
        raise ValueError(
            "More shares needed (%d) to recover the seed phrase than created "
            "(%d). Seed phrase would be irrecoverable." % (minimum, n_shares)
        )
    seed_length = len(seed.split(" "))
    if seed_length not in LENGTH_ALLOWED:
        raise ValueError(
            "Seed phrase should have %s words, but not %d words."
            % (LENGTH_STR, seed_length)
        )        
    seed_strength = seed_length // 3 * 32
    if share_strength not in STRENGTH_ALLOWED:
        raise ValueError(
            "Share strength should be one of the following %s. "
            "But it is not (%d)." % (STRENGTH_STR, share_strength)
        )
    if share_strength < seed_strength:
        raise ValueError(
            "Share strength (%d) is lower that seed strength (%d). Seed phrase "
            "would be irrecoverable." % (share_strength, seed_strength)
        )
    prime = PRIMES[share_strength]
    secret = seed_to_int(seed)
    poly = [secret] + [random_int(prime - 1) for i in range(minimum - 1)]
    points = [(i, _eval_at(poly, i, prime))
              for i in range(1, n_shares + 1)]
    shares = [(i, int_to_seed(point, strength=share_strength))
              for i, point in points]
    return shares

def _extended_gcd(a, b):
    """
    Division in integers modulus p means finding the inverse of the
    denominator modulo p and then multiplying the numerator by this
    inverse (Note: inverse of A is B such that A*B % p == 1) this can
    be computed via extended Euclidean algorithm
    http://en.wikipedia.org/wiki/Modular_multiplicative_inverse#Computation
    """
    x = 0
    last_x = 1
    y = 1
    last_y = 0
    while b != 0:
        quot = a // b
        a, b = b, a % b
        x, last_x = last_x - quot * x, x
        y, last_y = last_y - quot * y, y
    return last_x, last_y

def _divmod(num, den, p):
    """Compute num / den modulo prime p

    To explain what this means, the return value will be such that
    the following is true: den * _divmod(num, den, p) % p == num
    """
    inv, _ = _extended_gcd(den, p)
    return num * inv

def _lagrange_interpolate(x, x_s, y_s, p):
    """
    Find the y-value for the given x, given n (x, y) points;
    k points will define a polynomial of up to kth order.
    """
    k = len(x_s)
    assert k == len(set(x_s)), "points must be distinct"
    def PI(vals):  # upper-case PI -- product of inputs
        accum = 1
        for v in vals:
            accum *= v
        return accum
    nums = []  # avoid inexact division
    dens = []
    for i in range(k):
        others = list(x_s)
        cur = others.pop(i)
        nums.append(PI(x - o for o in others))
        dens.append(PI(cur - o for o in others))
    den = PI(dens)
    num = sum([_divmod(nums[i] * den * y_s[i] % p, dens[i], p)
               for i in range(k)])
    return (_divmod(num, den, p) + p) % p

def recover_seed(shares, seed_strength=256, prime=None):
    """
    Recover the seed phrase from share points
    (x, y points on the polynomial).
    """
    if len(shares) < 2:
        raise ValueError("Need at least two shares")
    
    # check that all shares have the same number of words
    len_shares = [len(share.split(" ")) for i, share in shares]
    if not len(set(len_shares)) ==  1:
        error_text = "\n".join(
            ["share %d: %d words" %(i, len(share.split(" ")))
             for i, share in shares]
        )
        raise ValueError(
            "Shares have different lengths: \n%s" % error_text
        )
    if seed_strength not in STRENGTH_ALLOWED:
        raise ValueError(
            "Seed strength should be one of the following %s, "
            "but it is not (%d)." % (STRENGTH_STR, seed_strength)
        )
    if not prime:
        share_word_length = len(shares[0][1].split(" "))
        share_strength = share_word_length // 3 * 32
        prime = PRIMES[share_strength]
    shares = [(i, seed_to_int(seed, strength=seed_strength))
              for i, seed in shares]
    x_s, y_s = zip(*shares)
    entropy = _lagrange_interpolate(0, x_s, y_s, prime)
    try:
        seed = int_to_seed(entropy, strength=seed_strength)
    except OverflowError:
        raise ValueError(
            "Failed to recover seed phrase, "
            "check if you have the minimum number of shares"
        )
    return seed