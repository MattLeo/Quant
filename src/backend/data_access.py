from .database import db_manager
from .models import Position, Trade, AnalysisResult, StopLossUpdate
from datetime import datetime

class TradingDAO:
    def __init__(self):
        self.db = db_manager

    def save_analysis_results(self, results):
        """Save analysis results to the database"""
        session = self.db.get_session()
        try:
            for result in results:
                analysis_result = AnalysisResult(
                    symbol = result['symbol'],
                    analysis_date = datetime.now(),
                    signal_strength = result['adjusted_signal'],
                    confidence = result['confidence'],
                    recommendation = result['recommendation'],
                    current_price = result['current_price'],
                    sma_signal = result['signals']['sma']['value'],
                    rsi_signal = result['signals']['rsi']['value'],
                    volume_signal = result['signals']['volume']['value'],
                    risk_score = result['risk_metrics']['risk_score'],
                    volatility = result['risk_metrics']['volatility']
                )
                session.add(analysis_result)
            session.commit()
            print(f"Saved {len(results)} analysis results to database")
        except Exception as e:
            session.rollback()
            print(f"Error saving results: {e}")
            raise e
        finally:
            self.db.close_session(session)

    def get_active_positions(self):
        """Get all active positions"""
        session =self.db.get_session()
        try:
            positions = session.query(Position).filter(Position.is_active == True).all()
            return positions
        except Exception as e:
            print(f"Error getting active positions: {e}")
            raise e
        
    def create_position(self, symbol, quantity, entry_price, entry_date=datetime.now(), stop_loss_price=None):
        """Create a new position"""
        session = self.db.get_session()
        try:
            position = Position(
                symbol = symbol,
                quantity = quantity,
                entry_price = entry_price,
                entry_date = entry_date,
                current_stop_loss = stop_loss_price,
                is_active = True
            )
            session.add(position)

            trade = Trade(
                position_id = position.id,
                symbol = symbol,
                action = 'BUY',
                quantity = quantity,
                price = entry_price,
                reason = 'NEW_POSITION'
            )
            session.add(trade)
            session.commit()

            return position.id
        
        except Exception as e:
            session.rollback()
            print(f"Error creating position: {e}")
            raise

        finally:
            self.db.close_session(session)

    def record_trade(self, position_id, symbol, action, quantity, price, reason):
        """Reacord a trade transaction"""
        session = self.db.get_session()
        try:
            trade = Trade(
                position_id = position_id,
                symbol = symbol,
                action = action,
                quantity = quantity,
                price = price,
                reason = reason
            )
            session.add(trade)
            session.commit()
            return trade.id
        finally:
            self.db.close_session(session)
    
    def close_position(self, position_id):
        """Mark position as inactive"""
        session = self.db.get_session()
        try:
            position = session.query(Position).filter(Position.id == position_id).first()
            if position:
                position.is_active = False
                session.commit()
        finally:
            self.db.close_session(session)
    
    def update_stop_loss(self, position_id, new_stop, reason):
        """Update stop loss for a porfolio"""
        session = self.db.get_session()
        try:
            position = session.query(Position).filter(Position.id == position_id).first()
            if position:
                update = StopLossUpdate(
                    position_id = position_id,
                    old_stop_loss = position.current_stop_loss,
                    new_stop_loss = new_stop,
                    update_date = datetime.now(),
                    reason = reason,
                    current_price = 0 # TODO pass current price into method
                )
                session.add(update)

                position.current_stop_loss = new_stop
                session.commit()
        finally:
            self.db.close_session(session)

    def get_owned_symbols(self):
        """Get list of owned symbols"""
        session = self.db.get_session()
        try:
            positions = session.query(Position).filter(Position.is_active == True).all()
            return [pos.symbol for pos in positions]
        finally:
            self.db.close_session(session)