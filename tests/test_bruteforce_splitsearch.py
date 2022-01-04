from hypothesis import given
from hypothesis import strategies as st

from baue_baum import iter_nsplits


@given(nof_elements=st.integers(min_value=1, max_value=256))
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
