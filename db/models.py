from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import (
    IntegrityError,
    NoResultFound,
    SQLAlchemyError,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import (
    joinedload,
    relationship,
    selectinload,
)

from db.main import Base


class BaseModel(Base):
    __abstract__ = True
    id = Column(String, primary_key=True)
    created_at = Column(
        DateTime, default=datetime.now
    )

    @classmethod
    async def create(
        cls,
        db: AsyncSession,
        identifier=None,
        created_at=None,
        **kwargs,
    ):
        if not identifier:
            identifier = str(uuid4())
        if not created_at:
            created_at = datetime.now()

        transaction = cls(
            id=identifier,
            created_at=created_at,
            **kwargs,
        )
        try:
            db.add(transaction)
            await db.commit()
            await db.refresh(transaction)
        except IntegrityError as e:
            await db.rollback()
            raise RuntimeError(e) from e

        return transaction

    @classmethod
    async def get(
        cls, db: AsyncSession, identifier: str
    ):
        try:
            transaction = await db.get(
                cls, identifier
            )
        except NoResultFound:
            return None
        return transaction

    @classmethod
    async def get_all(
        cls,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ):
        stmt = (
            select(cls).offset(skip).limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


class User(BaseModel):
    __tablename__ = "users"

    telegram_id = Column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )
    is_bot = Column(Boolean)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    language_code = Column(String, nullable=True)
    is_premium = Column(
        Boolean, default=False, nullable=False
    )

    updates = relationship(
        "Update",
        back_populates="user",
        cascade="all, delete, delete-orphan",
    )

    profile = relationship(
        "Profile",
        back_populates="user",
        cascade="all, delete, delete-orphan",
    )

    @classmethod
    async def get_by_telegram_id(
        cls, db: AsyncSession, telegram_id: int
    ):
        stmt = select(cls).filter(
            cls.telegram_id == telegram_id
        )
        res = await db.execute(stmt)

        return res.scalar_one_or_none()

    async def add_update(
        self, db: AsyncSession, **update_data
    ):
        update = Update(
            id=str(uuid4()),
            created_at=datetime.now(),
            user_id=self.telegram_id,
            **update_data,
        )
        try:
            db.add(update)

            await db.commit()

            await db.refresh(self)

            return update
        except SQLAlchemyError as e:
            await db.rollback()
            raise RuntimeError(
                "Failed to add update due to a database error."
            ) from e

    def __repr__(self):
        return f"{self.first_name or self.username or self.telegram_id}"


class Update(BaseModel):

    __tablename__ = "updates"
    user_id = Column(
        BigInteger,
        ForeignKey(
            "users.telegram_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    user = relationship(
        "User", back_populates="updates"
    )

    update_id = Column(Integer)
    update_type = Column(String, nullable=False)
    update_data = Column(JSONB)


class Profile(BaseModel):
    __tablename__ = "profiles"
    user_telegram_id = Column(
        BigInteger,
        ForeignKey(
            "users.telegram_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )
    user = relationship(
        "User", back_populates="profile"
    )

    phone = Column(
        BigInteger,
        nullable=True,
        index=True,
        unique=True,
    )
    email = Column(
        String,
        nullable=True,
        index=True,
        unique=True,
    )

    is_active = Column(Boolean, default=True)
    general_search_requests = Column(
        Integer, default=0, nullable=False
    )
    is_phone_confirmed = Column(
        Boolean, default=False, nullable=False
    )
    is_admin = Column(
        Boolean, default=False, nullable=True
    )
    requests = relationship(
        "Request", back_populates="author"
    )
    preferences = relationship(
        "Preferences",
        back_populates="profile",
        cascade="all, delete, delete-orphan",
        lazy="joined",
        uselist=False,
    )

    @classmethod
    async def get_by_telegram_id(
        cls,
        db: AsyncSession,
        telegram_id: int,
        joined: bool = False,
    ):
        stmt = select(cls).filter(
            cls.user_telegram_id == telegram_id
        )
        if joined:
            stmt = stmt.options(
                selectinload(cls.requests),
                selectinload(cls.preferences),
            )
        res = await db.execute(stmt)

        return res.unique().scalar_one_or_none()

    async def increment_general_requests(
        self, db: AsyncSession
    ):
        self.general_search_requests += 1

        db.add(self)

        try:
            await db.commit()  # Commit the transaction
            await db.refresh(
                self
            )  # Refresh the instance from the database
        except Exception as e:
            await db.rollback()  # Rollback in case of error
            raise RuntimeError(
                f"Failed to increment count: {e}"
            ) from e

    async def increment_inline_search_requests(
        self, db: AsyncSession
    ):
        self.inline_search_requests += 1

        db.add(self)

        try:
            await db.commit()  # Commit the transaction
            await db.refresh(
                self
            )  # Refresh the instance from the database
        except Exception as e:
            await db.rollback()  # Rollback in case of error
            raise RuntimeError(
                f"Failed to increment count: {e}"
            ) from e

    async def confirm_phone(self, db, phone: int):
        self.phone = phone
        self.is_phone_confirmed = True
        db.add(self)
        try:
            await db.commit()  # Commit the transaction
            await db.refresh(
                self
            )  # Refresh the instance from the database
            return True
        except Exception as e:
            await db.rollback()  # Rollback in case of error
            raise RuntimeError(
                f"Failed to increment count: {e}"
            ) from e


class Request(BaseModel):
    __tablename__ = "requests"
    author_telegram_id = Column(
        BigInteger,
        ForeignKey(
            "profiles.user_telegram_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    author = relationship(
        "Profile", back_populates="requests"
    )
    request_type = Column(
        String,
        nullable=False,
        default="arbitrary",
    )
    contents = Column(JSONB, nullable=False)


class Preferences(BaseModel):
    __tablename__ = "preferences"

    profile = relationship(
        "Profile", back_populates="preferences"
    )
    user_telegram_id = Column(
        BigInteger,
        ForeignKey(
            "profiles.user_telegram_id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )
