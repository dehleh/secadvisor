"""Tests for password hashing and JWT utilities."""
from datetime import timedelta

import pytest
from jose import JWTError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify_roundtrip(self):
        hashed = hash_password("Sup3rS3cret!")
        assert hashed != "Sup3rS3cret!"
        assert verify_password("Sup3rS3cret!", hashed) is True

    def test_verify_rejects_wrong_password(self):
        hashed = hash_password("Sup3rS3cret!")
        assert verify_password("WrongPassword", hashed) is False

    def test_same_password_produces_different_hashes(self):
        # bcrypt salts mean repeated hashes differ
        a = hash_password("samepass")
        b = hash_password("samepass")
        assert a != b


class TestJWT:
    def test_access_token_contains_subject(self):
        token = create_access_token(subject="user-123")
        decoded = decode_token(token)
        assert decoded["sub"] == "user-123"
        assert decoded["type"] == "access"

    def test_refresh_token_marked_as_refresh(self):
        token = create_refresh_token(subject="user-123")
        decoded = decode_token(token)
        assert decoded["type"] == "refresh"

    def test_expired_token_rejected(self):
        token = create_access_token(
            subject="user-123", expires_delta=timedelta(seconds=-1)
        )
        with pytest.raises(JWTError):
            decode_token(token)

    def test_garbage_token_rejected(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.jwt")

    def test_extra_claims_included(self):
        token = create_access_token(
            subject="user-123", extra_claims={"company_id": "co-456"}
        )
        decoded = decode_token(token)
        assert decoded["company_id"] == "co-456"
