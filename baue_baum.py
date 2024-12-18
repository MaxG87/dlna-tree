#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Iterable, List, Mapping, Tuple, TypeVar

FOLDER_LIST_T = List[str]
SPLIT_POS_T = Tuple[int, ...]
WEIGHT_TUPLE_T = Tuple[float, ...]
CACHE_T = dict[WEIGHT_TUPLE_T, float]
SPLIT_POS_MAPPING_T = dict[WEIGHT_TUPLE_T, Tuple[int, ...]]
WEIGHT_MAPPING_T = Mapping[str, float]
T = TypeVar("T")


class AccessType(Enum):
    WRAPPABLE = auto()
    LINEAR = auto()
    CONSTANT = auto()


@dataclass(frozen=True)
class BruteForceResult:
    costs: float
    weight: float


class IllegalArgumentException(Exception):
    pass


def access_costs(max_branching_factor: int, access_type: AccessType) -> Iterable[float]:
    """
    Returns list of access costs

    This function calculates how costly it is to enter/access the elements of a
    directory. It does not consider traversing a tree, only selecting elements
    on the same tree level.

    Parameters
    ----------
    max_branching_factor
        How many subelements are there.
    access_type
        Specifies the cost structure. Possible values are:
            linear: linear, i.e. one "cost" to traverse one element
            wrappable: linear, but with connection between first and last elem
            constant: 1 for each element

    Returns
    -------
    Iterable[float]
        each stating the cost to choose the corresponding element
    """
    if access_type == AccessType.WRAPPABLE:
        return [1] + [
            min(n, max_branching_factor - n) + 1 for n in range(1, max_branching_factor)
        ]
    elif access_type == AccessType.LINEAR:
        return range(1, max_branching_factor + 1)
    elif access_type == AccessType.CONSTANT:  # noqa: SIM106
        return [1] * max_branching_factor
    else:
        raise IllegalArgumentException(f"access_type `{access_type}' not defined")


def get_folder_list(cwd: Path) -> FOLDER_LIST_T:
    """
    Return entries of folder sorted alphabetically

    This function returns the name of the entries of a given folder sorted
    according to German rules (i.e. Umlauts are treated as their vocal
    correspondents).

    The function MUST NOT return absolute paths. The program uses a lookup
    table to get the costs of each element and needs to relocate the entries
    frequently when constructing the access tree. If the returned entries were
    of type `Path` one had to make sure to use `entry.name` whenever the
    elements are used. Thats even more error prone than handling file system
    entries as `str`.

    The sorting treats umlauts as their non-umlaut counterparts, according to
    German rules.

    Parameters
    ----------
    cwd
        Path to get sorted element list from

    Returns
    -------
    FOLDER_LIST_T
        sorted list of names of elements in CWD
    """
    tr_dict = str.maketrans("ÄÖÜäöü", "AOUaou")
    entries = (entry.name for entry in cwd.iterdir())
    folder_list = sorted(entries, key=lambda s: str(s).translate(tr_dict).lower())
    return folder_list


def get_ratios(costs: Iterable[float]) -> list[float]:
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

    Side Effects
    ------------
    Will consume `costs`. If it is a generator, it will be exhausted.
    """

    ratios_unnormed = [1 / c for c in costs]
    sum_ = sum(ratios_unnormed)
    ratios = [r / sum_ for r in ratios_unnormed]
    assert abs(sum(ratios) - 1) < 1e-6
    return ratios


def split_to_lists(inlist: tuple[T, ...], insplit: SPLIT_POS_T) -> list[tuple[T, ...]]:
    split = (0,) + insplit + (len(inlist),)
    ret = [inlist[start:end] for start, end in zip(split[:-1], split[1:])]
    return ret


def iter_nsplits(nof_elems: int, num_splits: int) -> Iterable[SPLIT_POS_T]:
    """Yield all possible splits

    This function will generate all possible splits for the given number of
    elements and split positions. Having nof_elems <= num_splits is illegal and
    causes a ValueError to be raised.

    Parameters
    ----------
    nof_elems
        Number of elements that need to be splitted.

    num_splits
        Number of required splits. Typically the branching factor.

    Returns
    -------
    Iterable[SPLIT_POS_T]
        Lazy stream of all possible split positions

    Raises
    ------
    ValueError
        If nof_elem <= num_splits

    Example:
    --------
    >>> all_splits = iter_nsplits(4,2)
    >>> next(all_splits)
    (1, 2)
    >>> next(all_splits)
    (1, 3)
    >>> next(all_splits)
    (2, 3)
    >>> next(all_splits)
    Traceback (most recent call last):
        ...
    StopIteration
    """

    def iter_nsplits_worker(
        nof_elems: int,
        num_splits: int,
        start_idx: int,
        start_tuple: SPLIT_POS_T,
    ):
        if num_splits == 0:
            yield start_tuple
            return
        for split_pos in range(start_idx, nof_elems - num_splits + 1):
            new_tuple = start_tuple + (split_pos,)
            yield from iter_nsplits_worker(
                nof_elems=nof_elems,
                num_splits=num_splits - 1,
                start_idx=split_pos + 1,
                start_tuple=new_tuple,
            )

    if nof_elems <= num_splits:
        raise ValueError

    yield from iter_nsplits_worker(
        nof_elems=nof_elems, num_splits=num_splits, start_idx=1, start_tuple=()
    )


def move_folders(
    cwd: Path, move_instructions: list[FOLDER_LIST_T], len_of_shortcut: int
) -> list[Path]:
    """
    Moves multiple elements into same subfolder

    This function receives a list of lists, specifying which elements shall be
    moved to the same subfolder. It then automatically determines a name for
    the subfolder and moves all elements to it.

    No subdirectory is created for lone elements.

    Parameters
    ----------
    cwd
        The current working directory. While not really the cwd, this function
        behaves as it were.
    move_instructions
        Elements of each container are moved to a common subfolder. The
        elements must be in cwd! It must hold len(c) > 1 for each c in
        move_instructions.
    len_of_shortcut
        The name of the common subfolder is determined by the names of the
        first and last element of the current container in move_instructions.
        From these elements, the first len_of_shortcut characters are taken to
        determine the name of the subfolder.

    Returns
    -------
    list[Path]
        list of created subfolders
    """

    ret_list = []
    for cur_set in move_instructions:
        assert len(cur_set) > 1
        branch_name = "{first_folder}-{last_folder}".format(
            first_folder=str(cur_set[0])[:len_of_shortcut],
            last_folder=str(cur_set[-1])[:len_of_shortcut],
        )
        new_parent_dir = cwd / branch_name
        new_parent_dir.mkdir()
        for elem in cur_set:
            old = cwd / elem
            new = new_parent_dir / elem
            old.rename(new)
        ret_list.append(new_parent_dir)

    return ret_list


def move_recursively(
    cwd: Path,
    folder_list: FOLDER_LIST_T,
    weight_dict: WEIGHT_MAPPING_T,
    split_positions: SPLIT_POS_MAPPING_T,
) -> None:
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
        new_cwd = cwd / subf
        move_recursively(
            cwd=new_cwd,
            folder_list=flist,
            weight_dict=weight_dict,
            split_positions=split_positions,
        )


def bruteforce_worker(
    access_type: AccessType,
    costs_cache: CACHE_T,
    elements: WEIGHT_TUPLE_T,
    max_branching_factor: int,
    split_positions: SPLIT_POS_MAPPING_T,
) -> BruteForceResult:
    nof_elems = len(elements)
    total_weight = sum(elements)

    if elements in costs_cache:
        # abort recursion
        return BruteForceResult(costs_cache[elements], total_weight)

    best_split: SPLIT_POS_T = ()
    best_split_cost = float(0xCAFFEBABE)

    max_num_splits = min(max_branching_factor - 1, nof_elems - 1)
    for num_splits in range(1, max_num_splits + 1):
        costs = list(
            access_costs(max_branching_factor=num_splits + 1, access_type=access_type)
        )
        for cur_split in iter_nsplits(nof_elems=nof_elems, num_splits=num_splits):
            subtree_results = []
            for sublist in split_to_lists(inlist=elements, insplit=cur_split):
                if len(sublist) == 1:
                    # recursion ends here
                    result = BruteForceResult(costs=0, weight=sublist[0])
                else:
                    result = bruteforce_worker(
                        access_type=access_type,
                        costs_cache=costs_cache,
                        elements=sublist,
                        split_positions=split_positions,
                        max_branching_factor=max_branching_factor,
                    )
                subtree_results.append(result)

            sum_of_subtree_costs = sum(
                cur_result.costs for cur_result in subtree_results
            )
            accumulated_costs_to_access_subtrees = sum(
                access_cost * result.weight
                for access_cost, result in zip(costs, subtree_results)
            )
            total_costs = sum_of_subtree_costs + accumulated_costs_to_access_subtrees
            if total_costs < best_split_cost or (
                total_costs == best_split_cost and len(cur_split) > len(best_split)
            ):
                best_split = cur_split
                best_split_cost = total_costs

    costs_cache[elements] = best_split_cost
    split_positions[elements] = best_split
    return BruteForceResult(best_split_cost, total_weight)


def bruteforce(
    elements: WEIGHT_TUPLE_T,
    max_branching_factor: int,
    access_type: AccessType,
    split_positions: SPLIT_POS_MAPPING_T,
) -> BruteForceResult:
    costs_cache: CACHE_T = {}
    return bruteforce_worker(
        access_type=access_type,
        costs_cache=costs_cache,
        elements=elements,
        max_branching_factor=max_branching_factor,
        split_positions=split_positions,
    )


def get_ratio_splitpositions(
    weight_tuple: WEIGHT_TUPLE_T, ratios: list[float]
) -> SPLIT_POS_T:
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
    weight_tuple
        A tuple containing the weight for each element to consider.
    ratios
        The ratio of elements weights to be stored in each subfolder.

    Returns
    -------
    SPLIT_POS_T
        A tuple of n-1 integers, with n == len(ratios). The elements of the
        returned tuple specify the first items (each corresponding to an
        element of weight_tuple) not to be included in the subfolders that are
        about to be created. This way, one can use the elements of
        split_positions directly in Python ranges.
    """

    split_positions: list[int] = []

    base_ind = 0
    rescale_ratio = 1.0
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

        is_greater = [w >= cur_ratio for w in cumratio_weights]
        candidate_idx = is_greater.index(True)
        if candidate_idx == 0:
            cur_split_pos = candidate_idx + 1
        elif (
            cur_ratio - cumratio_weights[candidate_idx - 1]
            < cumratio_weights[candidate_idx] - cur_ratio
        ):
            cur_split_pos = candidate_idx
        else:
            cur_split_pos = candidate_idx + 1
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
        split_positions.append(cur_split_pos)

    return tuple(split_positions)


def ratio_based_tree(
    access_type: AccessType,
    bruteforce_threshold: int,
    costs_cache: CACHE_T,
    cwd: Path,
    folder_list: FOLDER_LIST_T,
    max_branching_factor: int,
    split_positions: SPLIT_POS_MAPPING_T,
    weight_dict: WEIGHT_MAPPING_T,
) -> None:
    """
    Create access tree based on weight ratios

    This function recreates the access tree such that the more weight will be
    put into a subtree the smaller its access cost are. This concept is
    explained in detail in `get_ratio_splitpositions` and the file
    Designnotizen.

    Returns
    -------
    None
        The important calculations are stored in split_positions.

    Side Effects
    ------------
    The input variables cache and split_positions are manipulated.
    """
    weight_tuple = tuple(weight_dict[cur_fold] for cur_fold in folder_list)
    num_elems = len(folder_list)

    if weight_tuple in costs_cache:
        return

    if len(weight_tuple) < bruteforce_threshold:
        bruteforce_worker(
            access_type=access_type,
            costs_cache=costs_cache,
            elements=weight_tuple,
            max_branching_factor=max_branching_factor,
            split_positions=split_positions,
        )
        return

    if num_elems <= max_branching_factor:
        costs = access_costs(max_branching_factor=num_elems, access_type=access_type)
        # Subfolders which would hold only a single element will not be
        # created, as the element can be used directly. Therefore they do not
        # have inner costs. Their access costs are considered one recursion
        # level earlier.
        total_costs = (
            0.0 if num_elems == 1 else sum(c * w for c, w in zip(costs, weight_tuple))
        )
        costs_cache[weight_tuple] = total_costs
        split_positions[weight_tuple] = ()
        return

    costs = access_costs(
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
            access_type=access_type,
            bruteforce_threshold=bruteforce_threshold,
            costs_cache=costs_cache,
            cwd=cwd,
            folder_list=folder_list[begin:end],
            max_branching_factor=max_branching_factor,
            split_positions=split_positions,
            weight_dict=weight_dict,
        )


def main() -> None:
    cwd = Path.cwd()
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
    weight_dict = {f: 1.0 for f in folder_list}
    weight_dict.update(custom_weights)

    max_branching_factor = 4
    access_type = AccessType.WRAPPABLE
    split_positions: SPLIT_POS_MAPPING_T = {}
    ratio_based_tree(
        access_type=access_type,
        bruteforce_threshold=40,
        costs_cache={},
        cwd=cwd,
        folder_list=folder_list,
        max_branching_factor=max_branching_factor,
        split_positions=split_positions,
        weight_dict=weight_dict,
    )
    move_recursively(
        cwd=cwd,
        folder_list=folder_list,
        weight_dict=weight_dict,
        split_positions=split_positions,
    )


if __name__ == "__main__":
    main()
