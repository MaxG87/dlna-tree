#!/usr/bin/python3

import os
import shutil


def main():
  len_of_shortcut = 10
  max_branching_factor = 4
  folder_list = os.listdir('.')

  num_elems = len(folder_list)
  if num_elems <= max_branching_factor:
    # Nothing to do
    exit()

  # TODO: implement custom weight per folder
  costs = [1]*max_branching_factor
  s_costs = sum(costs)
  # Requirements:
  #   sum(ratios) == 1
  #   ∀i,j: ratios[i]/ratios[j] = costs[j] / costs[i]
  ratios = [1/(cc * s_costs) for cc in costs]

  # move folders to subfolders
  cur_ind = 0
  for num, cur_ratio in enumerate(ratios):
    elems_to_take = round(cur_ratio*num_elems)
    # 1st make sure to take all elements in last iteration
    last_ind = (cur_ind + elems_to_take - 1 if num < len(ratios) - 1
                else num_elems - 1) # inclusive range
    # 2nd make sure not to take too much elements
    last_ind = min(last_ind, num_elems - 1)

    branch_name = '{first_folder}_{last_folder}'.format(
                   first_folder=folder_list[cur_ind][:len_of_shortcut],
                   last_folder=folder_list[last_ind][:len_of_shortcut])
    os.mkdir(branch_name)
    for folder in folder_list[cur_ind:(last_ind + 1)]:
        shutil.move(folder, branch_name)

    cur_ind += elems_to_take



if __name__ == "__main__":
  main()
