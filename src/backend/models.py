from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import string

Base = declarative_base()

class Position(Base):
    __tablename__ = 'positions'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_date = Column(DateTime, nullable=False)
    current_stop_loss = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(String(20), default='filled') # 'filled' or 'pending'
    order_id = Column(String(50), nullable=True)

    # Relationships
    trades = relationship("Trade", back_populates="position")
    stop_updates = relationship("StopLossUpdate", back_populates="position")

class Trade(Base):
    __tablename__ = 'trades'

    id = Column(Integer, primary_key=True)
    position_id = Column(Integer, ForeignKey('positions.id'))
    symbol = Column(String(10), nullable=False)
    action = Column(String(4), nullable=False)  # BUY or SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)

    trade_date = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(255), nullable=True) #'NEW_POSITION, 'STOP_LOSS', 'SIGNAL_CHANGE'

    # Relationships
    position = relationship("Position", back_populates="trades")

class AnalysisResult(Base):
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), nullable=False)
    current_price = Column(Float, nullable=False)
    analysis_date = Column(DateTime, default=datetime.utcnow)
    signal_strength = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    recommendation = Column(String(4), nullable=False)  # BUY, SELL, or HOLD

    # Signals
    sma_signal = Column(Float, nullable=False)
    rsi_signal = Column(Float, nullable=False)
    volume_signal = Column(Float, nullable=False)

    # Risk metrics
    volatility = Column(Float)
    risk_score = Column(Float)

class StopLossUpdate(Base):
    __tablename__ = 'stop_loss_updates'

    id = Column(Integer, primary_key=True)
    position_id = Column(Integer, ForeignKey('positions.id'))
    new_stop_loss = Column(Float, nullable=False)
    old_stop_loss = Column(Float, nullable=True)
    update_date = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(50)) # 'INITIAL', 'TRAILING', 'MANUAL'
    current_price = Column(Float, nullable=False)

    # Relationships
    position = relationship("Position", back_populates="stop_updates")

class RecommendationsSnapshot(Base):
    __tablename__= 'recommendations_snapshots'
    
    id = Column(Integer, primary_key=True)
    analysis_date = Column(DateTime, default=datetime.now(), nullable=False)
    buy_recommendations = Column(Text)
    sell_recommendations = Column(Text)
    hold_recommendations = Column(Text)






