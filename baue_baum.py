#!/usr/bin/python3

import os
import shutil


def main():
  abk_len = 10
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
  for cur_ratio in ratios:
    elems_to_take = int(cur_ratio*num_elems)
    print("Would move from '", folder_list[cur_ind], "' to '",
          folder_list[cur_ind+elems_to_take-1] ,"'.")

    branch_name = "Br" + str(cur_ind)
    os.mkdir(branch_name)
    for folder in folder_list[cur_ind:(cur_ind + elems_to_take)]:
        shutil.move(folder, branch_name)
        
    cur_ind += elems_to_take



if __name__ == "__main__":
  main()
