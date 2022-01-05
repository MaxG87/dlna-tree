import pytest
from hypothesis import given
from hypothesis import strategies as st

from baue_baum import iter_nsplits


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
