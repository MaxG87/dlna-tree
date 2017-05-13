#!/usr/bin/python3

import locale
import os
import shutil
import subprocess
import sys
from functools import cmp_to_key


def main():
  locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
  len_of_shortcut = 10
  max_branching_factor = 4
  folder_list = sorted(os.listdir('.'), key=cmp_to_key(locale.strcoll))

  num_elems = len(folder_list)
  if num_elems <= max_branching_factor:
    # Nothing to do
    exit()

  # TODO: implement custom weight per folder
  wrap_around = True # TODO move to function signature
  if wrap_around:
      costs = [1] + [min(n, max_branching_factor - n) + 1
                     for n in range(1, max_branching_factor)]
  else:
      costs = range(1, max_branching_factor+1)
  # Requirements:
  #   sum(ratios) == 1
  #   ∀i,j: ratios[i]/ratios[j] = costs[j] / costs[i]
  ratios_unnormed = [1/c for c in costs]
  ratios = [r/sum(ratios_unnormed) for r in ratios_unnormed]
  assert(abs(sum(ratios) - 1) < 1e-6)

  # move folders to subfolders
  cur_ind = 0
  for num, cur_ratio in enumerate(ratios):
    # 1st Take at least one element!
    elems_to_take = max(1, round(cur_ratio*num_elems))
    # 2nd make sure to take all elements in last iteration
    last_ind = (cur_ind + elems_to_take - 1 if num < len(ratios) - 1
                else num_elems - 1) # inclusive range
    # 3rd make sure not to take too much elements
    last_ind = min(last_ind, num_elems - 1)

    branch_name = '{first_folder}_{last_folder}'.format(
                   first_folder=folder_list[cur_ind][:len_of_shortcut],
                   last_folder=folder_list[last_ind][:len_of_shortcut])
    os.mkdir(branch_name)
    for folder in folder_list[cur_ind:(last_ind + 1)]:
        shutil.move(folder, branch_name)
    cur_ind += elems_to_take

    # Call script recursively
    # FIXME This is bash style recursion. It must be done better!
    cwd = os.getcwd()
    os.chdir(branch_name)
    subprocess.call(os.path.join(cwd, sys.argv[0]))
    os.chdir(cwd)


if __name__ == "__main__":
  main()
