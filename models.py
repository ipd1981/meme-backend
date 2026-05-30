from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Buyer(Base):
    __tablename__ = "buyers"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(200), nullable=False)
    phone      = Column(String(20))
    email      = Column(String(200))
    city       = Column(String(100))
    gstin      = Column(String(15))
    created_at = Column(DateTime, server_default=func.now())
    invoices   = relationship("Invoice", back_populates="buyer")


class Invoice(Base):
    __tablename__ = "invoices"
    id             = Column(Integer, primary_key=True, index=True)
    buyer_id       = Column(Integer, ForeignKey("buyers.id"), nullable=False)
    invoice_no     = Column(String(50), nullable=False, unique=True)
    invoice_date   = Column(Date, nullable=False)
    due_date       = Column(Date, nullable=False)
    amount         = Column(Float, nullable=False)
    amount_paid    = Column(Float, default=0)
    status         = Column(String(20), default="open")
    notes          = Column(Text)
    created_at     = Column(DateTime, server_default=func.now())
    buyer          = relationship("Buyer", back_populates="invoices")
    communications = relationship("Communication", back_populates="invoice")


class Communication(Base):
    __tablename__ = "communications"
    id         = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    buyer_id   = Column(Integer, ForeignKey("buyers.id"))
    channel    = Column(String(20))
    message    = Column(Text)
    sent_at    = Column(DateTime, server_default=func.now())
    status     = Column(String(20), default="sent")
    invoice    = relationship("Invoice", back_populates="communications")
