#!/usr/bin/python3
# coding: utf-8

import os
import shutil


def get_access_cost(max_branching_factor, wrap_around):
    if wrap_around:
        costs = [1] + [min(n, max_branching_factor - n) + 1
                       for n in range(1, max_branching_factor)]
    else:
        costs = range(1, max_branching_factor + 1)

    return costs


def get_ratios(costs):
    # Requirements:
    #   sum(ratios) == 1
    #   ∀i,j: ratios[i]/ratios[j] = costs[j] / costs[i]
    ratios_unnormed = [1/c for c in costs]
    ratios = [r/sum(ratios_unnormed) for r in ratios_unnormed]
    assert(abs(sum(ratios) - 1) < 1e-6)
    return ratios


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


def setup_node(cwd, wrap_around):
    # preparation of some constants
    len_of_shortcut = 10
    max_branching_factor = 4
    tr_dict = str.maketrans('ÄÖÜ', 'AOU')
    folder_list = sorted(os.listdir(cwd), key=lambda s: s.translate(tr_dict))

    num_elems = len(folder_list)
    if num_elems <= max_branching_factor:
        # Nothing to do
        return

    # preparation of some important variables
    # TODO: implement custom weight per folder
    costs = get_access_cost(max_branching_factor=max_branching_factor,
                            wrap_around=wrap_around)
    ratios = get_ratios(costs)

    # move folders to subfolders
    move_instructions = ratio_based_structure(folder_list=folder_list,
                                              ratios=ratios)
    subfolders = move_folders(cwd=cwd, move_instructions=move_instructions,
                              len_of_shortcut=len_of_shortcut)
    for folder in subfolders:
        setup_node(cwd=folder, wrap_around=wrap_around)


def main():
    setup_node(cwd=os.getcwd(), wrap_around=True)

if __name__ == "__main__":
    main()
