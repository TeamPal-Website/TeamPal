import pytest
from src.errors.common import AccessDenied, Unauthorized, UserNotFound
from src.repositories.users import UsersRepository
from src.repositories.admins import AdminsRepository
from src.schemas.users import UserAdd
from src.services.auth import AuthService

async def create_test_user(session, email='test@example.com', is_active=True):
    hashed = AuthService().get_password_hash('password123')
    data = UserAdd(email=email, hashed_password=hashed, is_active=is_active)
    user = await UsersRepository(session).add(data)
    await session.commit()
    return user

class TestBaseRepository:

    async def test_add_returns_schema_with_id(self, db_session):
        user = await create_test_user(db_session)
        assert user.id is not None
        assert user.id > 0
        assert user.email == 'test@example.com'
        assert user.is_active is True

    async def test_add_multiple_users(self, db_session):
        user1 = await create_test_user(db_session, email='first@example.com')
        user2 = await create_test_user(db_session, email='second@example.com')
        assert user1.id != user2.id

    async def test_get_one_or_none_existing(self, db_session):
        created = await create_test_user(db_session)
        found = await UsersRepository(db_session).get_one_or_none(id=created.id)
        assert found is not None
        assert found.id == created.id
        assert found.email == created.email

    async def test_get_one_or_none_nonexistent(self, db_session):
        result = await UsersRepository(db_session).get_one_or_none(id=99999)
        assert result is None

    async def test_get_one_or_none_by_email(self, db_session):
        await create_test_user(db_session, email='findme@example.com')
        found = await UsersRepository(db_session).get_one_or_none(email='findme@example.com')
        assert found is not None
        assert found.email == 'findme@example.com'

    async def test_get_one_or_none_wrong_email(self, db_session):
        await create_test_user(db_session, email='exists@example.com')
        found = await UsersRepository(db_session).get_one_or_none(email='ghost@example.com')
        assert found is None

class TestUsersRepository:

    async def test_get_user_with_hashed_password_active(self, db_session):
        await create_test_user(db_session, email='active@example.com', is_active=True)
        result = await UsersRepository(db_session).get_user_with_hashed_password(email='active@example.com')
        assert result.email == 'active@example.com'
        assert result.hashed_password is not None
        assert len(result.hashed_password) > 0

    async def test_get_user_with_hashed_password_nonexistent(self, db_session):
        with pytest.raises(Unauthorized) as exc_info:
            await UsersRepository(db_session).get_user_with_hashed_password(email='ghost@example.com')
        assert exc_info.value.status_code == 401

    async def test_get_user_with_hashed_password_blocked(self, db_session):
        await create_test_user(db_session, email='blocked@example.com', is_active=False)
        with pytest.raises(AccessDenied) as exc_info:
            await UsersRepository(db_session).get_user_with_hashed_password(email='blocked@example.com')
        assert exc_info.value.status_code == 403

class TestAdminsRepository:

    async def test_block_user(self, db_session):
        user = await create_test_user(db_session, email='victim@example.com', is_active=True)
        await AdminsRepository(db_session).block_user(user_id=user.id)
        await db_session.commit()
        updated = await UsersRepository(db_session).get_one_or_none(id=user.id)
        assert updated.is_active is False

    async def test_block_nonexistent_user(self, db_session):
        with pytest.raises(UserNotFound) as exc_info:
            await AdminsRepository(db_session).block_user(user_id=99999)
        assert exc_info.value.status_code == 404

    async def test_unblock_user(self, db_session):
        user = await create_test_user(db_session, email='freed@example.com', is_active=False)
        await AdminsRepository(db_session).unblock_user(user_id=user.id)
        await db_session.commit()
        updated = await UsersRepository(db_session).get_one_or_none(id=user.id)
        assert updated.is_active is True

    async def test_unblock_nonexistent_user(self, db_session):
        with pytest.raises(UserNotFound) as exc_info:
            await AdminsRepository(db_session).unblock_user(user_id=99999)
        assert exc_info.value.status_code == 404

    async def test_block_already_blocked_user(self, db_session):
        user = await create_test_user(db_session, email='double@example.com', is_active=False)
        await AdminsRepository(db_session).block_user(user_id=user.id)
        await db_session.commit()
        updated = await UsersRepository(db_session).get_one_or_none(id=user.id)
        assert updated.is_active is False

    async def test_unblock_already_active_user(self, db_session):
        user = await create_test_user(db_session, email='active@example.com', is_active=True)
        await AdminsRepository(db_session).unblock_user(user_id=user.id)
        await db_session.commit()
        updated = await UsersRepository(db_session).get_one_or_none(id=user.id)
        assert updated.is_active is True
