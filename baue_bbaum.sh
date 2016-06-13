#!/bin/bash

abk_len=10

shopt -s nullglob
file_array=(*)
shopt -u nullglob

num_elems=${#file_array[@]}
[[ $num_elems -gt 4 ]] || exit
viertel=$((num_elems / 4))
rest=$((num_elems % 4))

cur_ind=0;
for i in {1..4}
do
  prev_ind=$cur_ind
  if [[ $rest -ge $i ]]
  then
    cur_ind=$(($prev_ind + $viertel + 1));
  else
    cur_ind=$(($prev_ind + $viertel));
  fi

  first_elem_ind=$prev_ind
  last_elem_ind=$(($cur_ind - 1))
  first_elem=${file_array[$first_elem_ind]}
  last_elem=${file_array[$last_elem_ind]}
  dir_name=${first_elem:0:$abk_len}-${last_elem:0:$abk_len}

  #echo $dir_name:
  #echo ${file_array[@]:${num_elems[$(($i - 1))]}:${num_elems[$i]}}
  mkdir -p "$dir_name"
  for j in $(seq $first_elem_ind $last_elem_ind)
  do
    #echo mv "${file_array[$j]}" "$dir_name"
    mv "${file_array[$j]}" "$dir_name"
  done
  #mv ${file_array[@]:${num_elems[$(($i - 1))]}:${num_elems[$i]}} "$dir_name"
  (cd "$dir_name" ; $0)
done
