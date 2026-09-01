from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas import TokenOut, UserCreate, UserOut


def test_user_create_requires_password():
    with pytest.raises(ValidationError):
        UserCreate(username="alice")


def test_user_create_ok():
    u = UserCreate(username="alice", password="secret")
    assert u.username == "alice"
    assert u.password == "secret"


def test_user_out_from_attributes():
    u = UserOut(id=1, username="alice", role="user", created_at=datetime.now())
    assert u.role == "user"


def test_token_out_default_token_type():
    user = UserOut(id=1, username="alice", role="user", created_at=datetime.now())
    tok = TokenOut(access_token="abc", user=user)
    assert tok.token_type == "bearer"
