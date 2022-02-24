"""
Convert seed phrase to its entropy as an integer. Then, use Shamir's
secret sharing scheme to split the secret into several subshares.
Finally, convert these entropies into seed phrases.

We check that the seed phrase can be recovered with any minimum
combination of shares before printing the results.
"""

from random import sample
from itertools import permutations
from shutil import get_terminal_size
from textwrap import wrap
import argparse

from mnemonic import Mnemonic
from utils import make_random_shares, recover_seed
from utils import PRIMES, PRIMES_STR
from utils import STRENGTH_ALLOWED, STRENGTH_STR
from utils import LENGTH_ALLOWED, LENGTH_STR

# 12 words = 128 bits
# 15 words = 160 bits
# 18 words = 192 bits
# 21 words = 224 bits
# 24 words = 256 bits

def len_permutations(iterable, r=None):
    pool = tuple(iterable)
    n = len(pool)
    r = n if r is None else r
    if r > n:
        return 0
    n_permutations = 1
    for i in range(n - r + 1, n + 1): 
        n_permutations *= i

    return n_permutations
    
def permutations_generator(seq, length):
    seen = set()
    while True:
        permutation = tuple(sample(seq, length))
        if permutation not in seen:
            seen.add(permutation)
            yield permutation

def terminal_print(text, screen_width=None):
    """Make sure the words won't be split between two lines"""
    if not screen_width:
        screen_width = get_terminal_size((80, 20)).columns

        # have at least on space on the right of the screen
        # so that the words won't be joined back when the width
        # of the terminal is increased
        lines = wrap(text, screen_width - 1)

        # fill the right of the screen with spaces
        lines = [line.ljust(screen_width - 1, " ") for line in lines]

    print(" ".join(lines))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--seed_phrase", type=str,
        help="Seed phrase to split in shares; list of %s words" % LENGTH_STR
    )
    parser.add_argument(
        "-g", "--generate_seed", type=int,
        help="""Strength (in bits) to the seed to be generated,
        must be one of %s (the greater the better security)""" % STRENGTH_STR
    )
    parser.add_argument(
        "-M", "--minimum", type=int, default=2,
        help="Number of shares to recover the seed phrase"
    )
    parser.add_argument(
        "-N", "--n_shares", type=int, default=3,
        help="Number of shares created"
    )
    parser.add_argument(
        "--share_strength", type=int,
        help="""Strength (in bits) of the shares generated,
        must be one of %s and greater than or equal to the strength 
        of the main seed. Same strength by default""" % STRENGTH_STR
    )
    args = parser.parse_args()


    if args.generate_seed:
        seed_strength = args.generate_seed
        if seed_strength in STRENGTH_ALLOWED:
            seed = Mnemonic("english").generate(seed_strength)
        else:
            raise ValueError(
                "Strength of the seed to generate must be one of "
                "the following %s, but it is not (%d)."
                % (STRENGTH_STR, seed_strength)
            )
    elif args.seed_phrase:
        seed = args.seed_phrase
    else:
        raise ValueError(
            "Generate a seed with -g (or --generate_seed) argument "
            "or provide yours with -s (or --seed_phrase) argument. "
            "Type -h to see help of the commands."
        )

    len_seed = len(seed.split(" "))

    if len_seed in LENGTH_ALLOWED:
        # convert number of words to bits of entropy
        seed_strength = len_seed // 3 * 32
    else:
        raise ValueError(
            "Number of words must be one of the following: "
            "%s, but it is not (%d)." % (LENGTH_STR, len_seed)
        )

    if not args.share_strength:
        # by default
        share_strength = seed_strength
    else:
        share_strength = args.share_strength

    if share_strength not in STRENGTH_ALLOWED:
        raise ValueError(
            "Share strength must be one of the following "
            "%s, but it is not (%d)." % (STRENGTH_STR, args.share_strength)
        )
    if share_strength < seed_strength:
        raise ValueError(
            "Share strength (%d) must be greater than or equal to "
            "seed strength (%d)." % (share_strength, seed_strength)
        )        

    prime = PRIMES[share_strength]
    # short string representation of the prime to avoid copying mistakes
    prime_str = PRIMES_STR[share_strength]

    shares = make_random_shares(seed, args.minimum, args.n_shares, share_strength)

    # verify that we can recover the seed phrase with the shares created
    # test a maximum of 100 permutations
    if len_permutations(shares, args.minimum) > 100:
        random_permutation = permutations_generator(shares, args.minimum)
        permutations_to_test = [next(random_permutation) for _ in range(100)]
    else:
        permutations_to_test = permutations(shares, args.minimum)

    assert all(
        [seed == recover_seed(subgroup, seed_strength, prime)
        for subgroup in permutations_to_test]
    )

    terminal_print("MAIN SEED: %s" % seed)
    for i, share_seed_phrase in shares:
        terminal_print("SHARE #%d: %s" % (i, share_seed_phrase))

    terminal_print("")
    terminal_print("%d SHARES CREATED (you need at least %d of them to recover "
                  "the orginal seed phrase)" %(args.n_shares, args.minimum))
    terminal_print("PRIME NUMBER USED: %s" % prime_str)
    terminal_print("")
    terminal_print("<!> WRITE DOWN THE PRIME NUMBER USED AND SHARES GENERATED "
                   "(SHARE NUMBER + LIST OF WORDS) <!>")