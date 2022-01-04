from hypothesis import strategies as st

from baue_baum import AccessType

MAX_BRANCHING_FACTOR = 128
MAX_ELEM_LIST_LEN = 256


@st.composite
def access_types(draw) -> AccessType:
    ret: AccessType = draw(st.sampled_from(list(AccessType)))
    return ret


@st.composite
def branching_factors(
    draw, min_value: int = 2, max_value: int = MAX_BRANCHING_FACTOR
) -> int:
    factor: int = draw(st.integers(min_value=min_value, max_value=max_value))
    return factor


@st.composite
def equal_weight_elements(
    draw, value: float = 1.0, min_size: int = 1, max_size: int = MAX_ELEM_LIST_LEN
) -> tuple[float, ...]:
    elements: list[float] = draw(
        st.lists(st.just(value), min_size=min_size, max_size=max_size)
    )
    return tuple(elements)


@st.composite
def weights(draw) -> float:
    sane_max_value = 100_000  # usual range is [1, 20]
    value: float = draw(
        st.floats(
            min_value=1.0,
            max_value=sane_max_value,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    return value
