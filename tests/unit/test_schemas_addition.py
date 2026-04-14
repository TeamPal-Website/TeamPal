from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from src.schemas.cities import CityAdd, City
from src.schemas.profiles import (
    ProfileAdd,
    ProfileBase,
    ProfileContacts,
    ProfileRequestPatch,
)
from src.enums import Gender


class TestCityAdd:

    def test_valid_title(self):
        city = CityAdd(title="Москва")
        assert city.title == "Москва"

    def test_empty_title_fails(self):
        with pytest.raises(ValidationError):
            CityAdd(title="")

    def test_title_too_long_fails(self):
        with pytest.raises(ValidationError):
            CityAdd(title="А" * 51)

    def test_title_max_length_accepted(self):
        city = CityAdd(title="А" * 50)
        assert len(city.title) == 50

    def test_title_one_char_accepted(self):
        city = CityAdd(title="М")
        assert city.title == "М"

    def test_missing_title_fails(self):
        with pytest.raises(ValidationError):
            CityAdd()


class TestCity:

    def test_includes_id(self):
        city = City(id=1, title="Казань")
        assert city.id == 1
        assert city.title == "Казань"

    def test_from_attributes(self):
        obj = SimpleNamespace(id=5, title="Самара")
        city = City.model_validate(obj)
        assert city.id == 5
        assert city.title == "Самара"


class TestProfileContacts:

    def test_all_fields_optional(self):
        contacts = ProfileContacts()
        assert contacts.phone is None
        assert contacts.telegram is None
        assert contacts.github is None

    def test_valid_contacts(self):
        contacts = ProfileContacts(phone="+79991234567", telegram="@user", github="username")
        assert contacts.phone == "+79991234567"

    def test_phone_too_long_fails(self):
        with pytest.raises(ValidationError):
            ProfileContacts(phone="1" * 21)

    def test_telegram_too_long_fails(self):
        with pytest.raises(ValidationError):
            ProfileContacts(telegram="@" + "x" * 64)

    def test_github_too_long_fails(self):
        with pytest.raises(ValidationError):
            ProfileContacts(github="x" * 101)


class TestProfileBase:

    def test_all_fields_optional(self):
        profile = ProfileBase()
        assert profile.first_name is None
        assert profile.age is None
        assert profile.gender is None
        assert profile.city_id is None
        assert profile.contacts is None

    def test_age_minimum_16(self):
        profile = ProfileBase(age=16)
        assert profile.age == 16

    def test_age_below_16_fails(self):
        with pytest.raises(ValidationError):
            ProfileBase(age=15)

    def test_age_maximum_100(self):
        profile = ProfileBase(age=100)
        assert profile.age == 100

    def test_age_above_100_fails(self):
        with pytest.raises(ValidationError):
            ProfileBase(age=101)

    def test_gender_male_accepted(self):
        assert ProfileBase(gender=Gender.MALE).gender == Gender.MALE

    def test_gender_female_accepted(self):
        assert ProfileBase(gender=Gender.FEMALE).gender == Gender.FEMALE

    def test_invalid_gender_fails(self):
        with pytest.raises(ValidationError):
            ProfileBase(gender="other")

    def test_first_name_whitespace_stripped(self):
        profile = ProfileBase(first_name="  Анна  ")
        assert profile.first_name == "Анна"

    def test_last_name_whitespace_stripped(self):
        profile = ProfileBase(last_name="  Иванов  ")
        assert profile.last_name == "Иванов"

    def test_name_only_spaces_fails(self):
        with pytest.raises(ValidationError):
            ProfileBase(first_name="   ")

    def test_first_name_too_long_fails(self):
        with pytest.raises(ValidationError):
            ProfileBase(first_name="А" * 36)

    def test_first_name_max_length_accepted(self):
        profile = ProfileBase(first_name="А" * 35)
        assert len(profile.first_name) == 35

    def test_city_id_zero_fails(self):
        with pytest.raises(ValidationError):
            ProfileBase(city_id=0)

    def test_city_id_negative_fails(self):
        with pytest.raises(ValidationError):
            ProfileBase(city_id=-1)

    def test_contacts_as_nested_model(self):
        profile = ProfileBase(contacts={"phone": "+7999", "telegram": None, "github": None})
        assert profile.contacts.phone == "+7999"


class TestProfileAdd:

    def test_requires_user_id(self):
        with pytest.raises(ValidationError):
            ProfileAdd()

    def test_user_id_zero_fails(self):
        with pytest.raises(ValidationError):
            ProfileAdd(user_id=0)

    def test_valid_profile_add(self):
        profile = ProfileAdd(user_id=1)
        assert profile.user_id == 1

    def test_all_other_fields_optional(self):
        profile = ProfileAdd(user_id=5)
        assert profile.first_name is None
        assert profile.age is None


class TestProfileRequestPatch:

    def test_all_fields_optional(self):
        patch_data = ProfileRequestPatch()
        assert patch_data.first_name is None

    def test_model_dump_exclude_unset_only_returns_set_fields(self):
        patch_data = ProfileRequestPatch(first_name="Дмитрий")
        dumped = patch_data.model_dump(exclude_unset=True)
        assert "first_name" in dumped
        assert "last_name" not in dumped
        assert "age" not in dumped

    def test_model_dump_full(self):
        patch_data = ProfileRequestPatch(first_name="Ольга", age=28)
        dumped = patch_data.model_dump(exclude_unset=True)
        assert dumped["first_name"] == "Ольга"
        assert dumped["age"] == 28