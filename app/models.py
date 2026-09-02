from sqlalchemy import func, Column, ForeignKey
from sqlalchemy.types import Integer, DateTime, Numeric, UUID
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class Wallet(Base):
    __tablename__ = 'wallets'

    uuid = Column(UUID, primary_key=True)
    balance = Column(
        Numeric(precision=10, scale=2),
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

    id = Column(Integer, primary_key=True)  # autoincrement подразумевается
    wallet_uuid = Column(
        UUID,
        ForeignKey('wallets.uuid'),
        nullable=False,
        index=True  # Оставляем, т.к. это внешний ключ, по нему часто ищут
    )
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    wallet = relationship('Wallet', back_populates='transactions')