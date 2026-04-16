from sqlalchemy import String, UniqueConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class SkillsOrm(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)


class SkillAliasOrm(Base):
    __tablename__ = "skill_aliases"
    __table_args__ = (
        UniqueConstraint(
            "skill_id",
            "alias",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(Text, nullable=False)

