from src.domain import mask_phone, normalize_phone


def test_normalize_phone_adds_brazil_country_code():
    assert normalize_phone("(54) 99999-9999") == "5554999999999"


def test_normalize_phone_rejects_transaction_like_values():
    assert normalize_phone("abc123") is None
    assert normalize_phone("1713999999999") is None
    assert normalize_phone("111111111111") is None


def test_mask_phone():
    assert mask_phone("5554999999999") == "5554***99"
