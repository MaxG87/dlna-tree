#!/usr/bin/python3
# coding: utf-8

import json
import os
import shutil


class IllegalArgumentException(Exception):
    pass


def get_access_cost(max_branching_factor, access_type):
    """
    Returns list of access costs

    This function calculates how costly it is to enter/access the elements of a
    directory. It does not consider traversing a tree, only selecting elements
    on the same tree level.

    Parameter
    ---------
    max_branching_factor: double
        How many subelements are there.
    access_type: str
        Specifies the costs for each element:
            linear: linear, i.e. one "cost" to traverse one element
            wrappable: linear, but with connection between first and last elem
            constant: 1 for each element

    Returns
    -------
    costs: list of doubles
        list of doubles, each stating the cost to choose the corresponding
        element
    """
    if access_type == "wrappable":
        costs = [1] + [
            min(n, max_branching_factor - n) + 1 for n in range(1, max_branching_factor)
        ]
    elif access_type == "linear":
        costs = range(1, max_branching_factor + 1)
    elif access_type == "constant":
        costs = [1] * max_branching_factor
    else:
        return IllegalArgumentException(
            "access_type `{access_type}' not defined".format(access_type=access_type)
        )

    return costs


def get_folder_list(cwd):
    """
    Glob folder and sort them alphabetically
    """
    tr_dict = str.maketrans("ÄÖÜäöü", "AOUäöü")
    folder_list = sorted(os.listdir(cwd), key=lambda s: s.translate(tr_dict).lower())
    return folder_list


def get_ratios(costs):
    """
    Transform costs to ratios

    Given access costs, this function calculates the fraction of the total
    weight that should go into subfolders. This is used for the ratio based
    tree construction and _does not_ take into account nonlinear access costs
    (i.e. costs(2*n) != 2*costs(n) for large n).

    The requirements satisfied by this function are:
        sum(ratios) == 1
        ∀i,j: ratios[i]/ratios[j] = costs[j] / costs[i]

    Thus, this is the most condensed form of the design rationale of the ratio
    based tree construction approach.
    """

    ratios_unnormed = [1 / c for c in costs]
    ratios = [r / sum(ratios_unnormed) for r in ratios_unnormed]
    assert abs(sum(ratios) - 1) < 1e-6
    return ratios


def split_to_lists(inlist, insplit):
    split = (0,) + insplit + (len(inlist),)
    ret_tuple = (inlist[start:end] for start, end in zip(split[:-1], split[1:]))
    return ret_tuple


def iter_nsplits(num_elems, num_splits, start=1, ret_tuple=()):
    if num_splits == 0:
        yield ret_tuple
        return
    for split_pos in range(start, num_elems - num_splits + 1):
        new_tuple = ret_tuple + (split_pos,)
        yield from iter_nsplits(
            num_elems=num_elems,
            num_splits=num_splits - 1,
            start=split_pos + 1,
            ret_tuple=new_tuple,
        )


def move_folders(cwd, move_instructions, len_of_shortcut):
    """
    Moves multiple elements into same subfolder

    This function receives a list of lists, specifying which elements shall be
    moved to the same subfolder. It then automatically determines a name for
    the subfolder and moves all elements to it.

    No subdirectory is created for lone elements.

    Receives
    --------
    cwd: str
        The current working directory. While not really the cwd, this function
        behaves as it were.
    move_instructions: list of containers.
        Elements of each container are moved to a common subfolder. The
        elements must be in cwd! It must hold len(c) > 1 for each c in
        move_instructions.
    len_of_shortcut: int
        The name of the common subfolder is determined by the names of the
        first and last element of the current container in move_instructions.
        From these elements, the first len_of_shortcut characters are taken to
        determine the name of the subfolder.

    Returns
    -------
    ret_list: list of str
        list of created subfolders
    """

    ret_list = []
    for cur_set in move_instructions:
        assert isinstance(cur_set, list)
        assert len(cur_set) > 1
        branch_name = "{first_folder}-{last_folder}".format(
            first_folder=cur_set[0][:len_of_shortcut],
            last_folder=cur_set[-1][:len_of_shortcut],
        )
        full_branch_name = os.path.join(cwd, branch_name)
        os.mkdir(full_branch_name)
        for elem in cur_set:
            full_path = os.path.join(cwd, elem)
            shutil.move(full_path, full_branch_name)
        ret_list.append(full_branch_name)

    return ret_list


def move_recursively(cwd, folder_list, weight_dict, split_positions):
    weight_tuple = tuple(weight_dict[cur_fold] for cur_fold in folder_list)

    if len(split_positions[weight_tuple]) == 0:
        return

    assert split_positions[weight_tuple][-1] < len(folder_list)
    split_tuple = (0,) + split_positions[weight_tuple] + (len(folder_list),)
    move_instructions = []
    for start, end in zip(split_tuple[:-1], split_tuple[1:]):
        assert start < end
        if start + 1 < end:
            # For single elements no subfolder are created. Thus
            # move_instructions are created only for subfolders that will
            # contain multiple elements.
            to_append = folder_list[start:end]
            move_instructions.append(to_append)

    subfolders = move_folders(
        cwd=cwd, move_instructions=move_instructions, len_of_shortcut=10
    )
    for subf, flist in zip(subfolders, move_instructions):
        new_cwd = os.path.join(cwd, subf)
        move_recursively(
            cwd=new_cwd,
            folder_list=flist,
            weight_dict=weight_dict,
            split_positions=split_positions,
        )


def bruteforce_worker(
    folder_list, weight_dict, cache, split_positions, max_branching_factor, access_type
):
    num_elems = len(folder_list)
    weight_tuple = tuple(weight_dict[cur_fold] for cur_fold in folder_list)
    sum_of_weights = sum(weight_tuple)

    if weight_tuple in cache:
        # abort recursion
        return sum_of_weights, cache[weight_tuple]
    if num_elems <= max_branching_factor:
        costs = get_access_cost(max_branching_factor=num_elems, access_type=access_type)
        # Subfolders which would hold only a single element will not be
        # created, as the element can be used directly. Therefore they do not
        # have inner costs. Their access costs are considered on recursion
        # level earlier.
        total_costs = (
            0 if num_elems == 1 else sum(c * w for c, w in zip(costs, weight_tuple))
        )
        cache[weight_tuple] = total_costs
        split_positions[weight_tuple] = ()
        return sum_of_weights, total_costs

    best_split = ()
    best_split_cost = 0xCAFFEBABE
    costs = get_access_cost(
        max_branching_factor=max_branching_factor, access_type=access_type
    )
    for cur_split in iter_nsplits(
        num_elems=num_elems, num_splits=max_branching_factor - 1
    ):
        cost_list = []
        weight_list = []
        for sublist in split_to_lists(inlist=folder_list, insplit=cur_split):
            cur_weight, cur_cost = bruteforce_worker(
                folder_list=sublist,
                weight_dict=weight_dict,
                cache=cache,
                split_positions=split_positions,
                max_branching_factor=max_branching_factor,
                access_type=access_type,
            )
            cost_list.append(cur_cost)
            weight_list.append(cur_weight)

        total_costs = sum(c * w for c, w in zip(costs, weight_list)) + sum(cost_list)
        if total_costs < best_split_cost:
            best_split = cur_split
            best_split_cost = total_costs

    cache[weight_tuple] = best_split_cost
    split_positions[weight_tuple] = best_split
    return sum_of_weights, best_split_cost


def bruteforce(cwd, folder_list, weight_dict, max_branching_factor, access_type):
    cache = {}
    split_positions = {}
    _, total_costs = bruteforce_worker(
        folder_list=folder_list,
        weight_dict=weight_dict,
        cache=cache,
        split_positions=split_positions,
        max_branching_factor=max_branching_factor,
        access_type=access_type,
    )
    return split_positions


def get_ratio_splitpositions(weight_tuple, ratios):
    """
    Get appropriate split positions

    Given a tuple of weights and an information about how much of the total
    weight shall be in a given container, this function determines which
    elements go into which container.

    If a given element of weight_tuple does not fit entirely into the container
    at hand it is taken iff its overlap is smaller than the part still fitting
    in the container. Furthermore, the weights and the remaining ratios are
    rescaled to keep errors due to rounding issues as small as possible.

    Parameters
    ----------
    weight_tuple: tuple of doubles
        A tuple containing the weight for each element to consider.
    ratios: tuple of doubles
        The ratio of elements weights to be stored in each subfolder.

    Returns
    -------
    split_positions: tuple of indices
        A tuple of n-1 doubles, with n == len(ratios). The elements of
        split_positions specify the first items (each corresponding to an
        element of weight_tuple) not to be included in the subfolders that are
        about to be created. This way, one can use the elements of
        split_positions directly in Python ranges.
    """

    split_positions = ()

    base_ind = 0
    rescale_ratio = 1
    # The last ratio is not included, as only the positions to split are
    # calculated. Thus, the remaining elements automatically form the last
    # partition.
    for cur_ratio in ratios[:-1]:
        cur_split = 0 if len(split_positions) == 0 else split_positions[-1]
        # Slow but without NumPy. Also, quite elegant.
        cumsum_weights = [
            sum(weight_tuple[cur_split : i + 1])
            for i in range(cur_split, len(weight_tuple))
        ]
        cumratio_weights = [w / cumsum_weights[-1] for w in cumsum_weights]

        # Ratios are rescaled to manage rounding issues. If e.g. one should
        # take 1/3rd but due to a element with a big weight one can only take
        # 1/4th, the remaining 1/12th are correctly included in the remaining
        # list. Without this rescaling the last subfolder would get very huge.
        cur_ratio /= rescale_ratio
        rescale_ratio *= 1 - cur_ratio

        is_greater = list(map(lambda w: w >= cur_ratio, cumratio_weights))
        ind_candidate = is_greater.index(True)
        if ind_candidate == 0:
            cur_split_pos = ind_candidate + 1
        elif (
            cur_ratio - cumratio_weights[ind_candidate - 1]
            < cumratio_weights[ind_candidate] - cur_ratio
        ):
            cur_split_pos = ind_candidate
        else:
            cur_split_pos = ind_candidate + 1
        new_base_ind = base_ind + cur_split_pos
        cur_split_pos += base_ind
        base_ind = new_base_ind

        assert cur_split_pos <= len(weight_tuple)
        if cur_split_pos == len(weight_tuple):
            # Due to deficiencies in the Ansatz it can happen that the maximum
            # branching is not exhausted. This occurs when there is a element
            # with a huge weight at the end of the list. Then the accumulated
            # mass of the first elements is not enough to be split into
            # multiple branches.
            # Since there are only heuristic fixes, no fix is attempted so far.
            # Instead of fixing this issue, improvements of the bruteforce
            # solution seem to be more desirable.
            break
        split_positions += (cur_split_pos,)

    return split_positions


def ratio_based_tree(
    cwd,
    folder_list,
    weight_dict,
    access_type,
    max_branching_factor,
    split_positions={},
    cache={},
):
    weight_tuple = tuple(weight_dict[cur_fold] for cur_fold in folder_list)
    num_elems = len(folder_list)

    if weight_tuple in cache:
        return cache[weight_tuple]
    if num_elems <= max_branching_factor:
        costs = get_access_cost(max_branching_factor=num_elems, access_type=access_type)
        # Subfolders which would hold only a single element will not be
        # created, as the element can be used directly. Therefore they do not
        # have inner costs. Their access costs are considered one recursion
        # level earlier.
        total_costs = (
            0 if num_elems == 1 else sum(c * w for c, w in zip(costs, weight_tuple))
        )
        cache[weight_tuple] = total_costs
        split_positions[weight_tuple] = ()
        return total_costs

    costs = get_access_cost(
        max_branching_factor=max_branching_factor, access_type=access_type
    )
    ratios = get_ratios(costs)

    cur_split_positions = get_ratio_splitpositions(
        weight_tuple=weight_tuple, ratios=ratios
    )
    split_positions[weight_tuple] = cur_split_positions

    range_tuple = (0,) + cur_split_positions + (num_elems,)
    for begin, end in zip(range_tuple[:-1], range_tuple[1:]):
        ratio_based_tree(
            cwd=cwd,
            folder_list=folder_list[begin:end],
            weight_dict=weight_dict,
            cache=cache,
            split_positions=split_positions,
            max_branching_factor=max_branching_factor,
            access_type=access_type,
        )

    return split_positions


def main():
    cwd = os.getcwd()
    folder_list = get_folder_list(cwd=cwd)

    # Import custom weights and apply them to the weight_dict.
    # TODO Sanity checks
    #   1) no keys occour twice
    #   2) only doubles as values
    #   3) all keys are valid folders, otherwise warn or something
    script_dir = os.path.dirname(__file__)
    custom_weights_file = os.path.join(script_dir, "custom-weights.json")
    with open(custom_weights_file) as f:
        custom_weights = json.load(f)
    weight_dict = {f: 1 for f in folder_list}
    weight_dict.update(custom_weights)

    max_branching_factor = 4
    access_type = "wrappable"
    # split_positions = bruteforce(cwd=cwd, folder_list=folder_list,
    #     weight_dict=weight_dict, max_branching_factor=max_branching_factor,
    #     access_type=access_type)
    split_positions = ratio_based_tree(
        cwd=cwd,
        folder_list=folder_list,
        weight_dict=weight_dict,
        max_branching_factor=max_branching_factor,
        access_type=access_type,
    )
    move_recursively(
        cwd=cwd,
        folder_list=folder_list,
        weight_dict=weight_dict,
        split_positions=split_positions,
    )


if __name__ == "__main__":
    main()
