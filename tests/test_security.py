import pytest
from fastapi import HTTPException

from src.security import validate_shared_secret


def test_validate_shared_secret_allows_empty_expected():
    validate_shared_secret(None, "", "invalid")


def test_validate_shared_secret_rejects_wrong_value():
    with pytest.raises(HTTPException):
        validate_shared_secret("wrong", "secret", "invalid")


def test_validate_shared_secret_accepts_match():
    validate_shared_secret("secret", "secret", "invalid")
