from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class CitiesOrm(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50), unique=True)
