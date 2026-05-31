from datetime import timedelta, datetime, timezone
import jwt as pyjwt
import pytest
from src.config import settings
from src.errors.auth import TokenExpired, TokenInvalidJwt, TokenInvalidSignature
from src.services.auth import AuthService

class TestPasswordHashing:

    def test_hash_differs_from_plain_password(self):
        service = AuthService()
        password = 'mysecretpassword'
        hashed = service.get_password_hash(password)
        assert hashed != password

    def test_hash_is_not_empty(self):
        hashed = AuthService().get_password_hash('password123')
        assert len(hashed) > 0

    def test_different_hashes_for_same_password(self):
        service = AuthService()
        hash1 = service.get_password_hash('password123')
        hash2 = service.get_password_hash('password123')
        assert hash1 != hash2

class TestPasswordVerification:

    def test_verify_correct_password(self):
        service = AuthService()
        password = 'correctpassword'
        hashed = service.get_password_hash(password)
        assert service.verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        service = AuthService()
        hashed = service.get_password_hash('correctpassword')
        assert service.verify_password('wrongpassword', hashed) is False

    def test_verify_similar_password(self):
        service = AuthService()
        hashed = service.get_password_hash('password123')
        assert service.verify_password('password124', hashed) is False

    def test_verify_empty_password(self):
        service = AuthService()
        hashed = service.get_password_hash('realpassword')
        assert service.verify_password('', hashed) is False

class TestTokenCreation:

    def test_token_contains_user_id(self):
        service = AuthService()
        token = service.create_access_token({'user_id': 42})
        decoded = service.decode_token(token)
        assert decoded['user_id'] == 42

    def test_token_has_expiration(self):
        service = AuthService()
        token = service.create_access_token({'user_id': 1})
        decoded = service.decode_token(token)
        assert 'exp' in decoded

    def test_token_custom_expiration(self):
        service = AuthService()
        delta = timedelta(hours=2)
        before = datetime.now(timezone.utc)
        token = service.create_access_token({'user_id': 1}, expires_delta=delta)
        after = datetime.now(timezone.utc)
        decoded = service.decode_token(token)
        exp = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        tolerance = timedelta(seconds=1)
        assert before + delta - tolerance <= exp <= after + delta + tolerance

    def test_token_default_expiration_uses_settings(self):
        service = AuthService()
        before = datetime.now(timezone.utc)
        token = service.create_access_token({'user_id': 1})
        after = datetime.now(timezone.utc)
        decoded = service.decode_token(token)
        exp = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
        expected_delta = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        tolerance = timedelta(seconds=1)
        assert before + expected_delta - tolerance <= exp <= after + expected_delta + tolerance

    def test_token_preserves_extra_data(self):
        service = AuthService()
        token = service.create_access_token({'user_id': 7, 'role': 'admin'})
        decoded = service.decode_token(token)
        assert decoded['user_id'] == 7
        assert decoded['role'] == 'admin'

class TestTokenDecoding:

    def test_decode_valid_token(self):
        service = AuthService()
        token = service.create_access_token({'user_id': 5})
        decoded = service.decode_token(token)
        assert decoded['user_id'] == 5

    def test_decode_expired_token(self):
        service = AuthService()
        token = service.create_access_token({'user_id': 1}, expires_delta=timedelta(seconds=-10))
        with pytest.raises(TokenExpired) as exc_info:
            service.decode_token(token)
        assert exc_info.value.status_code == 401
        assert 'истек' in exc_info.value.detail.lower()

    def test_decode_token_wrong_secret_key(self):
        token = pyjwt.encode({'user_id': 1, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}, 'x' * 32, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(TokenInvalidSignature) as exc_info:
            AuthService().decode_token(token)
        assert exc_info.value.status_code == 401

    def test_decode_garbage_token(self):
        with pytest.raises(TokenInvalidJwt) as exc_info:
            AuthService().decode_token('this.is.not.a.valid.jwt')
        assert exc_info.value.status_code == 401

    def test_decode_empty_string(self):
        with pytest.raises(TokenInvalidJwt) as exc_info:
            AuthService().decode_token('')
        assert exc_info.value.status_code == 401

    def test_decode_token_wrong_algorithm(self):
        token = pyjwt.encode({'user_id': 1, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}, 'k' * 48, algorithm='HS384')
        with pytest.raises(TokenInvalidJwt) as exc_info:
            AuthService().decode_token(token)
        assert exc_info.value.status_code == 401
