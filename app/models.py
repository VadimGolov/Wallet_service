from decimal import Decimal
from sqlalchemy import Integer, DateTime, Numeric, String, func, Column, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass


class Wallet(Base):
    __tablename__ = 'wallets'

    uuid = Column(String, primary_key=True, index=True)
    balance = Column(
        Numeric(precision=10, scale=2),
        default=Decimal('0.00'),
        server_default='0.00',
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transactions = relationship(
        'Transaction',
        back_populates='wallet',
        cascade='all, delete-orphan',
    )


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)

    wallet_uuid = Column(
        String,
        ForeignKey('wallets.uuid'),
        nullable=False,
        index=True,
    )

    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ИСПРАВЛЕНИЕ 2: прямой класс + список из колонки
    wallet = relationship(
        Wallet,
        back_populates='transactions',
        foreign_keys=[wallet_uuid],  # noqa ignore[arg-type]
    )