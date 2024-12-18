import pytest
from hypothesis import given
from hypothesis import strategies as st

from baue_baum import AccessType, access_costs, get_ratio_splitpositions, get_ratios
from tests import hypothesis_utils as hu

MAX_BRANCHING_FACTOR = 128
MAX_ELEM_LIST_LEN = 256


@given(access_type=hu.access_types(), branching_factor=hu.branching_factors())
def test_access_costs_return_length(
    access_type: AccessType, branching_factor: int
) -> None:
    result = access_costs(branching_factor, access_type)
    nof_elems = sum(1 for _ in result)
    assert nof_elems == branching_factor


@given(
    access_type=hu.access_types(),
    branching_factor=hu.branching_factors(),
    value=hu.weights(),
)
def test_single_element_is_not_splitted(
    access_type: AccessType, branching_factor: int, value: float
) -> None:
    elements = (value,)
    costs = access_costs(branching_factor, access_type)
    ratios = get_ratios(costs)
    split_positions = get_ratio_splitpositions(elements, ratios)
    assert split_positions == ()


@pytest.mark.parametrize("access_type", AccessType)
def test_splits_before_last_huge_elem(access_type: AccessType) -> None:
    branching_factor = 4
    costs = list(access_costs(branching_factor, access_type))
    ratios = get_ratios(costs)

    weight_tuple = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 9247.0)
    split_positions = get_ratio_splitpositions(weight_tuple, ratios)
    # An optimal solution would distribute the 1.0 weighted entries onto the
    # first N buckets. Unfortunately, this does not happen currently.
    assert split_positions[-1] == 7


@pytest.mark.parametrize(
    "access_type", [AccessType.CONSTANT, AccessType.LINEAR, AccessType.WRAPPABLE]
)
def test_splits_before_and_past_huge_elem(access_type: AccessType) -> None:
    branching_factor = 4
    costs = list(access_costs(branching_factor, access_type))
    ratios = get_ratios(costs)

    weight_tuple = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 9247.0, 1.0, 1.0)
    expected = (7, 8, 9)
    split_positions = get_ratio_splitpositions(weight_tuple, ratios)
    # An optimal solution would distribute the 1.0 weighted entries onto the
    # first N buckets. Unfortunately, this does not happen currently.
    assert expected == split_positions


@pytest.mark.xfail(reason="Known to be handled suboptimal!")
@given(
    access_type=hu.access_types(),
    elements=st.lists(st.just(1.0), min_size=1).map(tuple),
)
def test_branching_factor_is_exhausted(
    access_type: AccessType, elements: tuple[float, ...]
) -> None:
    # This test should pass for small numbers of elements but fails there. It
    # is unclear whether it should pass for huge numbers of elements, say 10
    # but until it passes for few elements it can left as is.
    branching_factor = len(elements)
    costs = list(access_costs(branching_factor, access_type))
    ratios = get_ratios(costs)

    expected = tuple(range(1, branching_factor))
    split_positions = get_ratio_splitpositions(elements, ratios)
    assert split_positions == expected


@pytest.mark.parametrize("access_type", [AccessType.LINEAR, AccessType.WRAPPABLE])
@pytest.mark.parametrize("nof_elems", [1, 2, 3])
def test_very_few_elements_are_splitted_elementwise(
    access_type: AccessType, nof_elems: int
) -> None:
    elements = tuple([1.0] * nof_elems)
    branching_factor = 4
    costs = list(access_costs(branching_factor, access_type))
    ratios = get_ratios(costs)

    expected = tuple(range(1, nof_elems))
    split_positions = get_ratio_splitpositions(elements, ratios)
    assert split_positions == expected


@pytest.mark.xfail(reason="Known to be handled suboptimal!")
@pytest.mark.parametrize("access_type", [AccessType.LINEAR, AccessType.WRAPPABLE])
def test_few_elements_are_splitted_elementwise(access_type: AccessType) -> None:
    # Total Costs:
    # wrappable:
    #   optimal: [1, 1, 1, 1] => 1 + 2 + 3 + 2 == 8
    #   by algorithm: [[1, 1], 1, 1] => 2 + 3 + 2 + 2 == 9
    # linear:
    #   optimal: [1, 1, 1, 1] => 1 + 2 + 3 + 4 == 10
    #   by algorithm: [[1, 1], 1, 1] => 2 + 3 + 2 + 3 == 10
    branching_factor = 4
    elements = tuple([1.0] * branching_factor)
    costs = list(access_costs(branching_factor, access_type))
    ratios = get_ratios(costs)

    expected = tuple(range(1, branching_factor))
    split_positions = get_ratio_splitpositions(elements, ratios)
    assert split_positions == expected


@given(
    elements=st.lists(st.just(1.0), min_size=1).map(tuple),
)
def test_few_elements_are_splitted_elementwise_constant(
    elements: tuple[float, ...]
) -> None:
    access_type = AccessType.CONSTANT
    branching_factor = len(elements)
    costs = list(access_costs(branching_factor, access_type))
    ratios = get_ratios(costs)

    expected = tuple(range(1, branching_factor))
    split_positions = get_ratio_splitpositions(elements, ratios)
    assert split_positions == expected


@pytest.mark.xfail(reason="Known to be handled suboptimal!")
def test_wrappable_splits_seven_elems_optimal() -> None:
    branching_factor = 4
    access_type = AccessType.WRAPPABLE
    costs = list(access_costs(branching_factor, access_type))
    ratios = get_ratios(costs)

    weight_tuple = tuple([1.0] * 7)
    expected = (4, 5, 6)
    split_positions = get_ratio_splitpositions(weight_tuple, ratios)
    assert split_positions == expected


def test_wrappable_splits_many_elems_correcty() -> None:
    branching_factor = 4
    access_type = AccessType.WRAPPABLE
    costs = list(access_costs(branching_factor, access_type))
    ratios = get_ratios(costs)

    weight_tuple = tuple([1.0] * 128)
    split_positions = get_ratio_splitpositions(weight_tuple, ratios)
    expected = (55, 82, 100)
    assert split_positions == expected


@given(
    access_type=hu.access_types(),
    elements=st.lists(hu.weights(), min_size=1),
    branching_factor=hu.branching_factors(),
)
def test_ratio_splitpositions_does_not_crash(
    access_type: AccessType, elements: list[float], branching_factor: int
) -> None:
    costs = list(access_costs(branching_factor, access_type))
    ratios = get_ratios(costs)
    get_ratio_splitpositions(tuple(elements), ratios)
