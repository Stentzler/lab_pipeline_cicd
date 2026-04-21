from src.service import sum_numbers


def test_sum_numbers() -> None:
    assert sum_numbers(2, 3) == 5
