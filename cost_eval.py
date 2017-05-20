#!/usr/bin/python3

import argparse
import numpy as np
import random as rnd

maxN = 201
maxB = 10

class IllegalArgumentException(Exception):
    pass

def get_access_cost(cur_bin, num_bins, access_type):
    if access_type == 'wrappable':
        # When cur_bin goes from 0 to N, num_bins is N+1
        # Thus, for maximal cur_bin, num_bins-cur_bin+1 == 2
        return min(cur_bin, num_bins-cur_bin) + 1
    elif access_type == 'linear':
        return cur_bin + 1
    elif access_type == 'constant':
        return 1
    else:
        return IllegalArgumentException(
            "access_type `{access_type}' not defined".format(
                access_type=access_type))

def init(access_type):
    global tree_cost
    global n

    # Initialise
    tree_cost = np.zeros([maxN, maxB], dtype=np.float64)
    tree_cost[:] = np.nan
    n = np.zeros([maxB, maxN, maxB], dtype=np.int8)

    # No elements. Degenerated special case.
    tree_cost[0, :] = 0
    # Exactly one element. No subtree is needed, thus no access cost.
    # Considered as special case.
    tree_cost[1, :] = 0
    # All other trivial cases. These need an access action and thus are not for
    # free.
    for cur_n in range (2, maxN):
        for cur_b in range(cur_n, maxB):
            total_cost = sum([get_access_cost(cur_bin=cur_bin, num_bins=cur_n,
                access_type=access_type) for cur_bin in range(0, cur_n)])
            tree_cost[cur_n, cur_b] = total_cost
            n[0:cur_n, cur_n, cur_b] = 1


def derive_tree_cost(N, B, access_type):
    global tree_cost
    if B == 1 and N > 1:
        return np.nan
    if not np.isnan(tree_cost[N, B]):
        return tree_cost[N, B]
    if np.isnan(tree_cost[N-1, B]):
        # Derive costs for N-1 elements. The size of the bins is needed to
        # derive the base cost.
        derive_tree_cost(N=N-1, B=B, access_type=access_type)
    
    best_i = -1
    best_cost = 0xCAFFEBABE

    # Best cost when adding to an existing bin
    base_cost = 0
    for cur_i, cur_n in enumerate(n[:, N-1, B]):
        if cur_n == 0: break
        cur_access_cost = get_access_cost(cur_bin=cur_i, num_bins=B,
                                          access_type=access_type) * cur_n
        base_cost += cur_access_cost + derive_tree_cost(N=cur_n, B=B,
                                                        access_type=access_type)
    for cur_i in range(0, B):
        cur_n = n[cur_i, N-1, B]
        if cur_n == 0: break
        base_access_cost = get_access_cost(cur_bin=cur_i, num_bins=B,
                                           access_type=access_type)
        old_term = (base_access_cost * cur_n
                    + derive_tree_cost(N=cur_n, B=B, access_type=access_type))
        new_term = base_access_cost * (cur_n+1) + derive_tree_cost(
            N=(cur_n+1), B=B, access_type=access_type)
        cur_cost = base_cost - old_term + new_term
        if cur_cost <= best_cost:
            if (cur_cost < best_cost
                or rnd.random() < 0.5):
                # or best_i < 0
                # or n[cur_i, N-1, B] <= n[best_i, N-1, B]):
                best_cost = cur_cost
                best_i = cur_i

    tree_cost[N, B] = best_cost
    n[:, N, B] = n[:, N-1, B]
    n[best_i, N, B] += 1

    return best_cost


def main():
    global tree_cost
    global n

    parser = argparse.ArgumentParser()
    parser.add_argument('-N', required=True, type=int,
                        help='Number of elements')
    args = parser.parse_args()

    access_type = 'wrappable'
    B = 4
    N = args.N

    for __ in range(1000):
        init(access_type=access_type)
        ret = derive_tree_cost(N=N, B=B, access_type=access_type)
        #print(ret)
        print(ret, (n[:B, N, B]))

if __name__ == "__main__":
    main()
