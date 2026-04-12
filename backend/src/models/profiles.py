from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.enums import Gender
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB

from src.database import Base


class ProfilesOrm(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    avatar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(35), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(35), nullable=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    gender: Mapped[Gender | None] = mapped_column(SQLEnum(Gender, name="gender_enum"), nullable=True)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), nullable=True)
    contacts: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
