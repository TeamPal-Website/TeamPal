from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB

from src.database import Base


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class ProfilesOrm(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(35))
    last_name: Mapped[str] = mapped_column(String(35))
    age: Mapped[int]
    gender: Mapped[Gender | None] = mapped_column(
        SQLEnum(Gender, name="gender_enum"),
        nullable=True,
    )
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    contacts: Mapped[dict] = mapped_column(JSONB, nullable=True, default=dict)



