import pytest
from sqlalchemy.exc import IntegrityError
from src.repositories.cities import CitiesRepository
from src.repositories.profiles import ProfilesRepository
from src.schemas.cities import CityAdd
from src.schemas.profiles import ProfileAdd, ProfileRequestPatch
from tests.integration.test_repositories import create_test_user

async def create_test_city(session, title='Москва'):
    data = CityAdd(title=title)
    city = await CitiesRepository(session).add(data)
    await session.commit()
    return city

async def create_test_profile(session, email_suffix='1'):
    user = await create_test_user(session, email=f'profile{email_suffix}@example.com')
    data = ProfileAdd(user_id=user.id)
    profile = await ProfilesRepository(session).add(data)
    await session.commit()
    return (profile, user.id)

class TestCitiesRepository:

    async def test_add_city_returns_id(self, db_session):
        city = await create_test_city(db_session)
        assert city.id is not None
        assert city.id > 0
        assert city.title == 'Москва'

    async def test_get_all_empty(self, db_session):
        result = await CitiesRepository(db_session).get_all()
        assert result == []

    async def test_get_all_returns_all_cities(self, db_session):
        await create_test_city(db_session, 'Москва')
        await create_test_city(db_session, 'Казань')
        result = await CitiesRepository(db_session).get_all()
        assert len(result) == 2

    async def test_get_one_or_none_existing(self, db_session):
        city = await create_test_city(db_session, 'Самара')
        found = await CitiesRepository(db_session).get_one_or_none(id=city.id)
        assert found is not None
        assert found.title == 'Самара'

    async def test_get_one_or_none_nonexistent(self, db_session):
        result = await CitiesRepository(db_session).get_one_or_none(id=99999)
        assert result is None

    async def test_get_one_or_none_by_title(self, db_session):
        await create_test_city(db_session, 'Екатеринбург')
        found = await CitiesRepository(db_session).get_one_or_none(title='Екатеринбург')
        assert found is not None
        assert found.title == 'Екатеринбург'

    async def test_add_duplicate_city_raises(self, db_session):
        await create_test_city(db_session, 'Москва')
        with pytest.raises(IntegrityError):
            await create_test_city(db_session, 'Москва')

    async def test_ids_are_unique(self, db_session):
        city1 = await create_test_city(db_session, 'Омск')
        city2 = await create_test_city(db_session, 'Уфа')
        assert city1.id != city2.id

class TestProfilesRepository:

    async def test_add_profile_returns_id(self, db_session):
        profile, _ = await create_test_profile(db_session)
        assert profile.id is not None
        assert profile.id > 0

    async def test_profile_fields_initially_none(self, db_session):
        profile, _ = await create_test_profile(db_session)
        assert profile.first_name is None
        assert profile.last_name is None
        assert profile.age is None
        assert profile.gender is None

    async def test_get_profile_by_user_id(self, db_session):
        _, uid = await create_test_profile(db_session)
        found = await ProfilesRepository(db_session).get_one_or_none(user_id=uid)
        assert found is not None

    async def test_get_profile_nonexistent_returns_none(self, db_session):
        result = await ProfilesRepository(db_session).get_one_or_none(user_id=99999)
        assert result is None

    async def test_edit_profile_returns_rowcount(self, db_session):
        _, uid = await create_test_profile(db_session)
        patch_data = ProfileRequestPatch(first_name='Иван')
        rows = await ProfilesRepository(db_session).edit(patch_data, exclude_unset=True, user_id=uid)
        assert rows == 1

    async def test_edit_profile_updates_fields(self, db_session):
        _, uid = await create_test_profile(db_session)
        patch_data = ProfileRequestPatch(first_name='Иван', age=25)
        await ProfilesRepository(db_session).edit(patch_data, exclude_unset=True, user_id=uid)
        await db_session.commit()
        updated = await ProfilesRepository(db_session).get_one_or_none(user_id=uid)
        assert updated.first_name == 'Иван'
        assert updated.age == 25

    async def test_edit_profile_exclude_unset_preserves_other_fields(self, db_session):
        _, uid = await create_test_profile(db_session)
        await ProfilesRepository(db_session).edit(ProfileRequestPatch(first_name='Мария'), exclude_unset=True, user_id=uid)
        await db_session.commit()
        await ProfilesRepository(db_session).edit(ProfileRequestPatch(last_name='Иванова'), exclude_unset=True, user_id=uid)
        await db_session.commit()
        updated = await ProfilesRepository(db_session).get_one_or_none(user_id=uid)
        assert updated.first_name == 'Мария'
        assert updated.last_name == 'Иванова'

    async def test_edit_nonexistent_profile_returns_zero(self, db_session):
        patch_data = ProfileRequestPatch(first_name='Тест')
        rows = await ProfilesRepository(db_session).edit(patch_data, exclude_unset=True, user_id=99999)
        assert rows == 0

class TestSkillsRepository:

    async def test_add_skill(self, db_session):
        from src.repositories.skills import SkillsRepository
        from src.schemas.skills import SkillAdd
        repo = SkillsRepository(db_session)
        skill = await repo.add(SkillAdd(name='Python'))
        await db_session.commit()
        assert skill.id is not None
        assert skill.id > 0
        assert skill.name == 'Python'

    async def test_get_one_or_none_existing(self, db_session):
        from src.repositories.skills import SkillsRepository
        from src.schemas.skills import SkillAdd
        repo = SkillsRepository(db_session)
        created = await repo.add(SkillAdd(name='JavaScript'))
        await db_session.commit()
        found = await repo.get_one_or_none(id=created.id)
        assert found is not None
        assert found.id == created.id

    async def test_get_one_or_none_nonexistent(self, db_session):
        from src.repositories.skills import SkillsRepository
        repo = SkillsRepository(db_session)
        result = await repo.get_one_or_none(id=99999)
        assert result is None

    async def test_get_all(self, db_session):
        from src.repositories.skills import SkillsRepository
        from src.schemas.skills import SkillAdd
        repo = SkillsRepository(db_session)
        await repo.add(SkillAdd(name='Python'))
        await repo.add(SkillAdd(name='JavaScript'))
        await db_session.commit()
        all_skills = await repo.get_all()
        assert len(all_skills) == 2

    async def test_delete_skill(self, db_session):
        from src.repositories.skills import SkillsRepository
        from src.schemas.skills import SkillAdd
        repo = SkillsRepository(db_session)
        created = await repo.add(SkillAdd(name='Go'))
        await db_session.commit()
        await repo.delete(id=created.id)
        await db_session.commit()
        result = await repo.get_one_or_none(id=created.id)
        assert result is None

class TestRolesDictionaryRepository:

    async def test_add_role(self, db_session):
        from src.repositories.roles_dictionary import RolesDictionaryRepository
        from src.schemas.roles_dictionary import RoleDictionaryAdd
        repo = RolesDictionaryRepository(db_session)
        role = await repo.add(RoleDictionaryAdd(name='Backend Developer'))
        await db_session.commit()
        assert role.id is not None
        assert role.id > 0
        assert role.name == 'Backend Developer'

    async def test_get_one_or_none_existing(self, db_session):
        from src.repositories.roles_dictionary import RolesDictionaryRepository
        from src.schemas.roles_dictionary import RoleDictionaryAdd
        repo = RolesDictionaryRepository(db_session)
        created = await repo.add(RoleDictionaryAdd(name='Frontend Developer'))
        await db_session.commit()
        found = await repo.get_one_or_none(id=created.id)
        assert found is not None
        assert found.id == created.id

    async def test_get_one_or_none_by_name(self, db_session):
        from src.repositories.roles_dictionary import RolesDictionaryRepository
        from src.schemas.roles_dictionary import RoleDictionaryAdd
        repo = RolesDictionaryRepository(db_session)
        await repo.add(RoleDictionaryAdd(name='Designer'))
        await db_session.commit()
        found = await repo.get_one_or_none(name='Designer')
        assert found is not None
        assert found.name == 'Designer'

    async def test_get_all(self, db_session):
        from src.repositories.roles_dictionary import RolesDictionaryRepository
        from src.schemas.roles_dictionary import RoleDictionaryAdd
        repo = RolesDictionaryRepository(db_session)
        await repo.add(RoleDictionaryAdd(name='Developer'))
        await repo.add(RoleDictionaryAdd(name='Designer'))
        await db_session.commit()
        all_roles = await repo.get_all()
        assert len(all_roles) == 2

    async def test_delete_role(self, db_session):
        from src.repositories.roles_dictionary import RolesDictionaryRepository
        from src.schemas.roles_dictionary import RoleDictionaryAdd
        repo = RolesDictionaryRepository(db_session)
        created = await repo.add(RoleDictionaryAdd(name='Manager'))
        await db_session.commit()
        await repo.delete(id=created.id)
        await db_session.commit()
        result = await repo.get_one_or_none(id=created.id)
        assert result is None
