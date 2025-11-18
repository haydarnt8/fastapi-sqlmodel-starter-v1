"""
Tests for Security Module
"""

import pytest
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token

def test_password_hashing():
    password = "SecurePass123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)

def test_password_verification_fails_wrong_password():
    password = "SecurePass123!"
    hashed = get_password_hash(password)
    assert not verify_password("WrongPass!", hashed)

def test_create_and_decode_token():
    user_id = "test-user-id"
    token = create_access_token(subject=user_id)
    payload = decode_token(token)
    assert payload["sub"] == user_id
