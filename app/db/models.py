from uuid import UUID as Py_UUID
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, ForeignKey, String, Integer, DateTime, Numeric, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class TransactionStatus:
    CONFIRMED: str = 'CONFIRMED'
    CANCELLED: str = 'CANCELLED'


class Base(DeclarativeBase):
    pass


class Wallet(Base):
    __tablename__ = 'wallets'

    uuid: Mapped[Py_UUID] = mapped_column(Uuid, primary_key=True)
    balance: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        server_default='0.00',
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list['Transaction']] = relationship(back_populates='wallet', cascade='all, delete-orphan')


class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet_uuid: Mapped[Py_UUID] = mapped_column(
        Uuid,
        ForeignKey('wallets.uuid'),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    status: Mapped[str] = mapped_column(String(10), default=TransactionStatus.CONFIRMED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    wallet: Mapped['Wallet'] = relationship(back_populates='transactions', lazy='joined')