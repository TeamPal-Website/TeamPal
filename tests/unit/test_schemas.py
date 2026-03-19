from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.schemas.users import UserRequestAdd, UserAdd, User, UserWithHashedPassword


class TestUserRequestAdd:

    def test_valid_data(self):
        user = UserRequestAdd(email="user@example.com", password="password123")
        assert user.email == "user@example.com"
        assert user.password == "password123"

    def test_password_exactly_8_chars(self):
        user = UserRequestAdd(email="user@example.com", password="12345678")
        assert user.password == "12345678"

    def test_password_7_chars_fails(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRequestAdd(email="user@example.com", password="1234567")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("password",) for e in errors)

    def test_password_9_chars(self):
        user = UserRequestAdd(email="user@example.com", password="123456789")
        assert user.password == "123456789"

    def test_empty_password_fails(self):
        with pytest.raises(ValidationError):
            UserRequestAdd(email="user@example.com", password="")

    def test_one_char_password_fails(self):
        with pytest.raises(ValidationError):
            UserRequestAdd(email="user@example.com", password="a")

    def test_short_password_error_message(self):
        with pytest.raises(ValidationError) as exc_info:
            UserRequestAdd(email="user@example.com", password="short")
        assert "8 символов" in str(exc_info.value)

    def test_very_long_password_accepted(self):
        long_password = "a" * 1000
        user = UserRequestAdd(email="user@example.com", password=long_password)
        assert len(user.password) == 1000

    def test_invalid_email_no_at(self):
        with pytest.raises(ValidationError):
            UserRequestAdd(email="not-an-email", password="password123")

    def test_invalid_email_no_domain(self):
        with pytest.raises(ValidationError):
            UserRequestAdd(email="user@", password="password123")

    def test_invalid_email_empty(self):
        with pytest.raises(ValidationError):
            UserRequestAdd(email="", password="password123")

    def test_email_with_spaces(self):
        with pytest.raises(ValidationError):
            UserRequestAdd(email="user @example.com", password="password123")

    def test_valid_email_with_plus(self):
        user = UserRequestAdd(email="user+tag@example.com", password="password123")
        assert "+" in user.email

    def test_valid_email_with_dots(self):
        user = UserRequestAdd(email="first.last@example.com", password="password123")
        assert user.email == "first.last@example.com"


class TestUserAdd:

    def test_model_dump(self):
        user = UserAdd(
            email="test@example.com",
            hashed_password="$argon2id$hash...",
            is_active=True,
        )
        data = user.model_dump()
        assert data == {
            "email": "test@example.com",
            "hashed_password": "$argon2id$hash...",
            "is_active": True,
        }

    def test_model_dump_inactive(self):
        user = UserAdd(
            email="blocked@example.com",
            hashed_password="hash",
            is_active=False,
        )
        assert user.model_dump()["is_active"] is False


class TestUser:

    def test_from_dict(self):
        user = User(id=1, email="user@example.com", is_active=True)
        assert user.id == 1
        assert user.email == "user@example.com"
        assert user.is_active is True

    def test_from_attributes(self):
        orm_obj = SimpleNamespace(
            id=1, email="test@example.com", is_active=True, hashed_password="secret"
        )
        user = User.model_validate(orm_obj)
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.is_active is True

    def test_no_hashed_password_in_fields(self):
        assert "hashed_password" not in User.model_fields


class TestUserWithHashedPassword:

    def test_includes_hashed_password(self):
        user = UserWithHashedPassword(
            id=1,
            email="test@example.com",
            is_active=True,
            hashed_password="somehash",
        )
        assert user.hashed_password == "somehash"

    def test_inherits_user_fields(self):
        user = UserWithHashedPassword(
            id=5,
            email="admin@example.com",
            is_active=False,
            hashed_password="hash",
        )
        assert user.id == 5
        assert user.email == "admin@example.com"
        assert user.is_active is False
