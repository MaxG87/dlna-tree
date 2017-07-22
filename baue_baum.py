#!/usr/bin/python3
# coding: utf-8

import json
import os
import shutil


class IllegalArgumentException(Exception):
    pass


def get_access_cost(max_branching_factor, access_type):
    if access_type == 'wrappable':
        costs = [1] + [min(n, max_branching_factor - n) + 1
                       for n in range(1, max_branching_factor)]
    elif access_type == 'linear':
        costs = range(1, max_branching_factor + 1)
    elif access_type == 'constant':
        costs = [1]*max_branching_factor
    else:
        return IllegalArgumentException(
            "access_type `{access_type}' not defined".format(
                access_type=access_type))

    return costs


def get_folder_list(cwd):
    tr_dict = str.maketrans('ÄÖÜ', 'AOU')
    folder_list = sorted(os.listdir(cwd), key=lambda s: s.translate(tr_dict))
    return folder_list


def get_ratios(costs):
    # Requirements:
    #   sum(ratios) == 1
    #   ∀i,j: ratios[i]/ratios[j] = costs[j] / costs[i]
    ratios_unnormed = [1/c for c in costs]
    ratios = [r/sum(ratios_unnormed) for r in ratios_unnormed]
    assert(abs(sum(ratios) - 1) < 1e-6)
    return ratios


def split_to_lists(inlist, insplit):
    split = (0,) + insplit + (len(inlist),)
    ret_tuple = (inlist[start:end]
                 for start, end in zip(split[:-1], split[1:]))
    return ret_tuple


def iter_nsplits(num_elems, num_splits, start=1, ret_tuple=()):
    if num_splits == 0:
        yield ret_tuple
        return
    for split_pos in range(start, num_elems-num_splits+1):
        new_tuple = ret_tuple + (split_pos,)
        yield from iter_nsplits(num_elems=num_elems,
                                 num_splits=num_splits-1,
                                 start=split_pos+1,
                                 ret_tuple=new_tuple)


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
        Elements of each container are moved to a common subfolder.
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
        assert(isinstance(cur_set, list))
        if len(cur_set) == 1:
            continue
        branch_name = '{first_folder}_{last_folder}'.format(
                       first_folder=cur_set[0][:len_of_shortcut],
                       last_folder=cur_set[-1][:len_of_shortcut])
        full_branch_name = os.path.join(cwd, branch_name)
        os.mkdir(full_branch_name)
        for elem in cur_set:
            full_path = os.path.join(cwd, elem)
            shutil.move(full_path, full_branch_name)
        ret_list.append(full_branch_name)

    return ret_list


def ratio_based_structure(folder_list, ratios):
    ret_move_instructions = []
    num_elems = len(folder_list)
    cur_ind = 0
    rescale_ratio = 1
    for num, cur_ratio in enumerate(ratios):
        assert(abs(sum(ratios[num:]) / rescale_ratio - 1) < 1e-6)
        cur_ratio /= rescale_ratio
        rescale_ratio *= (1 - cur_ratio)
        # 1st Take the appropriate ratio of the elements left, but at least 1
        elems_to_take = max(1, round(cur_ratio*(num_elems-cur_ind)))
        # 2nd make sure to take all elements in last iteration
        last_ind = (
                    # inclusive range
                    cur_ind + elems_to_take - 1 if num < len(ratios) - 1
                    else num_elems - 1
                   )
        # 3rd make sure not to take too much elements
        last_ind = min(last_ind, num_elems - 1)

        ret_move_instructions.append(
            [folder for folder in folder_list[cur_ind:(last_ind + 1)]])
        cur_ind += elems_to_take
    return ret_move_instructions


def bruteforce_worker(folder_list, weight_dict, cache, split_positions,
                      max_branching_factor, access_type):
    ret_move_instructions = []
    num_elems = len(folder_list)
    weight_tuple = tuple(weight_dict[cur_fold] for cur_fold in folder_list)
    sum_of_weights = sum(weight_tuple)

    # Abort recursion
    if weight_tuple in cache:
        return sum_of_weights, cache[weight_tuple]
    if num_elems <= max_branching_factor:
        costs = get_access_cost(max_branching_factor=num_elems,
                                access_type=access_type)
        # Subfolders which would hold only a single element will not be
        # created, as the element can be used directly. Therefore they do not
        # have inner costs. Their access costs are considered on recursion
        # level earlier.
        total_costs = (0 if num_elems == 1
                        else sum(c*w for c, w in zip(costs, weight_tuple)))
        cache[weight_tuple] = total_costs
        split_positions[weight_tuple] = ()
        return sum_of_weights, total_costs

    best_split = ()
    best_split_cost = 0xCAFFEBABE
    costs = get_access_cost(max_branching_factor=max_branching_factor,
                            access_type=access_type)
    for cur_split in iter_nsplits(num_elems=num_elems,
                                   num_splits=max_branching_factor-1):
        cost_list = []
        weight_list = []
        for sublist in split_to_lists(inlist=folder_list, insplit=cur_split):
            cur_weight, cur_cost = bruteforce_worker(folder_list=sublist,
                weight_dict=weight_dict, cache=cache,
                split_positions=split_positions,
                max_branching_factor=max_branching_factor,
                access_type=access_type)
            cost_list.append(cur_cost)
            weight_list.append(cur_weight)

        total_costs = (sum(c*w for c, w in zip(costs, weight_list))
                       + sum(cost_list))
        if total_costs < best_split_cost:
            best_split = cur_split
            best_split_cost = total_costs

    cache[weight_tuple] = best_split_cost
    split_positions[weight_tuple] = best_split
    return sum_of_weights, best_split_cost


def move_recursively(cwd, folder_list, weight_dict, split_positions):
    weight_tuple = tuple(weight_dict[cur_fold] for cur_fold in folder_list)

    if len(split_positions[weight_tuple]) == 0:
        return

    split_tuple = (0,) + split_positions[weight_tuple] + (len(folder_list),)
    move_instructions = []
    for start, end in zip(split_tuple[:-1], split_tuple[1:]):
        to_append = folder_list[start:end]
        move_instructions.append(to_append)

    subfolders = move_folders(cwd=cwd, move_instructions=move_instructions,
                              len_of_shortcut=10)
    for subf, flist in zip(subfolders, move_instructions):
        new_cwd = os.path.join(cwd, subf)
        move_recursively(cwd=new_cwd, folder_list=flist,
                         weight_dict=weight_dict,
                         split_positions=split_positions)


def bruteforce(cwd, folder_list, weight_dict, max_branching_factor,
               access_type):
    cache = {}
    split_positions={}
    _, total_costs = bruteforce_worker(folder_list=folder_list,
        weight_dict=weight_dict,
        cache=cache,
        split_positions=split_positions,
        max_branching_factor=max_branching_factor,
        access_type=access_type)
    move_recursively(cwd=cwd, folder_list=folder_list, weight_dict=weight_dict,
                     split_positions=split_positions)


def setup_node(cwd, weight_dict, max_branching_factor, access_type):
    # preparation of some constants
    len_of_shortcut = 10
    folder_list = get_folder_list(cwd)

    num_elems = len(folder_list)
    if num_elems <= max_branching_factor:
        # Nothing to do
        return

    # preparation of some important variables
    # TODO: implement custom weight per folder
    costs = get_access_cost(max_branching_factor=max_branching_factor,
                            access_type=access_type)
    ratios = get_ratios(costs)

    # move folders to subfolders
    move_instructions = ratio_based_structure(folder_list=folder_list,
                                              ratios=ratios)
    subfolders = move_folders(cwd=cwd, move_instructions=move_instructions,
                              len_of_shortcut=len_of_shortcut)
    for folder in subfolders:
        setup_node(cwd=folder, weight_dict=weight_dict,
                   max_branching_factor=max_branching_factor,
                   access_type=access_type)


def main():
    cwd = os.getcwd()
    folder_list = get_folder_list(cwd=cwd)

    # Import custom weights and apply them to the weight_dict.
    # TODO Sanity checks
    #   1) no keys occour twice
    #   2) only doubles as values
    #   3) all keys are valid folders, otherwise warn or something
    script_dir = os.path.dirname(__file__)
    custom_weights_file = os.path.join(script_dir, 'custom_weights.json')
    with open(custom_weights_file) as f:
        custom_weights = json.load(f)
    weight_dict = {f: 1 for f in folder_list}
    weight_dict.update(custom_weights)

    max_branching_factor = 4
    access_type = 'wrappable'
    # bruteforce(cwd=cwd, folder_list=folder_list, weight_dict=weight_dict,
    #            max_branching_factor=max_branching_factor,
    #            access_type=access_type)
    setup_node(cwd=cwd, weight_dict=weight_dict,
               max_branching_factor=max_branching_factor,
               access_type=access_type)

if __name__ == "__main__":
    main()
