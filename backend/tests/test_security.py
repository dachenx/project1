import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_roundtrip():
    hashed = hash_password("123456")
    assert hashed != "123456"  # 不是明文存储
    assert verify_password("123456", hashed) is True


def test_verify_wrong_password_returns_false():
    hashed = hash_password("correct-password")
    assert verify_password("wrong-password", hashed) is False


def test_hash_is_salted_and_unique():
    # 同一明文两次哈希结果不同（bcrypt 随机盐）
    assert hash_password("abc") != hash_password("abc")


def test_jwt_roundtrip():
    token = create_access_token("alice", "admin")
    payload = decode_token(token)
    assert payload["sub"] == "alice"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_tampered_token_raises():
    token = create_access_token("alice", "user")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(Exception):
        decode_token(tampered)
