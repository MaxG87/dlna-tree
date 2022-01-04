import pytest
from hypothesis import given
from hypothesis import strategies as st

from baue_baum import AccessType, bruteforce, iter_nsplits
from tests import hypothesis_utils as hu

MAX_BRANCHING_FACTOR = 128
MAX_ELEM_LIST_LEN = 256


@given(nof_elements=st.integers(min_value=3, max_value=256))
def test_iter_nsplits_two_splits(nof_elements: int) -> None:
    result = list(iter_nsplits(nof_elements, 2))
    expected = [
        (start, stop)
        for start in range(1, nof_elements)
        for stop in range(start + 1, nof_elements)
    ]
    assert expected == result


@given(nof_elements=st.integers(min_value=2, max_value=256))
def test_iter_nsplits_must_split_single_elements(nof_elements: int) -> None:
    result = list(iter_nsplits(nof_elements, nof_elements - 1))
    expected = [tuple(range(1, nof_elements))]
    assert expected == result


@given(
    test_case=st.integers(min_value=2, max_value=256).flatmap(
        lambda n: st.tuples(st.just(n), st.integers(min_value=n))
    )
)
def test_iter_nsplits_raises_if_to_few_elements(test_case: tuple[int, int]) -> None:
    nof_elements, num_splits = test_case
    with pytest.raises(ValueError):
        list(iter_nsplits(nof_elements, num_splits))


@given(
    access_type=hu.access_types(),
    branching_factor=hu.branching_factors(),
    elements=st.lists(hu.weights(), max_size=10),
)
def test_return_value_is_correct(
    access_type: AccessType, branching_factor: int, elements: list[float]
) -> None:
    split_positions = {}  # type: ignore
    result = bruteforce(
        access_type=access_type,
        elements=tuple(elements),
        max_branching_factor=branching_factor,
        split_positions=split_positions,
    )
    assert result.weight == sum(elements)
    assert result.costs > 0


@given(
    access_type=hu.access_types(),
    branching_factor=hu.branching_factors(),
    value=hu.weights(),
)
def test_single_element_is_not_splitted(
    access_type: AccessType, branching_factor: int, value: float
) -> None:
    elements = (value,)
    split_positions = {}  # type: ignore
    bruteforce(
        access_type=access_type,
        elements=elements,
        max_branching_factor=branching_factor,
        split_positions=split_positions,
    )
    assert split_positions == {(value,): ()}


@pytest.mark.parametrize("access_type", AccessType)
def test_splits_before_last_huge_elem(access_type: AccessType) -> None:
    branching_factor = 4
    split_positions = {}  # type: ignore

    elements = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 9247.0)
    bruteforce(
        access_type=access_type,
        elements=elements,
        max_branching_factor=branching_factor,
        split_positions=split_positions,
    )
    result_split = split_positions[elements]
    # An optimal solution would distribute the 1.0 weighted entries onto the
    # first N buckets. Unfortunately, this does not happen currently.
    assert result_split[-1] == 7


@pytest.mark.parametrize(
    "access_type", [AccessType.CONSTANT, AccessType.LINEAR, AccessType.WRAPPABLE]
)
def test_splits_before_and_past_huge_elem(access_type: AccessType) -> None:
    branching_factor = 4
    split_positions = {}  # type: ignore

    elements = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 9247.0, 1.0, 1.0)
    bruteforce(
        access_type=access_type,
        elements=elements,
        max_branching_factor=branching_factor,
        split_positions=split_positions,
    )
    result_split = split_positions[elements]
    assert 7 in result_split
    assert 8 in result_split


# @given(
#     access_type=hu.access_types(),
#     elements=st.lists(st.just(1.0), min_size=1).map(tuple),
# )
# def test_branching_factor_is_exhausted(
#     access_type: AccessType, elements: tuple[float, ...]
# ) -> None:
#     # This test should pass for small numbers of elements but fails there. It
#     # is unclear whether it should pass for huge numbers of elements, say 10
#     # but until it passes for few elements it can left as is.
#     branching_factor = len(elements)
#     split_positions = {}  # type: ignore

#     expected = tuple(range(1, branching_factor))
#     bruteforce(
#         access_type=access_type,
#         elements=elements,
#         max_branching_factor=branching_factor,
#         split_positions=split_positions,
#     )
#     assert split_positions == expected


@pytest.mark.parametrize("access_type", AccessType)
@pytest.mark.parametrize("nof_elems", [1, 2, 3, 4])
def test_few_elements_are_splitted_elementwise(
    access_type: AccessType, nof_elems: int
) -> None:
    elements = tuple([1.0] * nof_elems)
    branching_factor = 4
    split_positions = {}  # type: ignore

    expected = tuple(range(1, nof_elems))
    bruteforce(
        access_type=access_type,
        elements=elements,
        max_branching_factor=branching_factor,
        split_positions=split_positions,
    )
    result_split = split_positions[elements]
    assert result_split == expected


def test_wrappable_splits_seven_elems_optimal() -> None:
    branching_factor = 4
    access_type = AccessType.WRAPPABLE
    split_positions = {}  # type: ignore

    elements = tuple([1.0] * 7)
    expected = (4, 5, 6)
    bruteforce(
        access_type=access_type,
        elements=elements,
        max_branching_factor=branching_factor,
        split_positions=split_positions,
    )
    result_split = split_positions[elements]
    assert result_split == expected
