from .database import db_manager
from .models import Position, Trade, AnalysisResult, StopLossUpdate
from datetime import datetime

class TradingDAO:
    def __init__(self):
        self.db = db_manager

    def save_analysis_resilts(self, results):
        """Save analysis results to the database"""
        session = self.db.get_session()
        try:
            for result in results:
                analysis_result = AnalysisResult(
                    symbol = result['symbol'],
                    analysis_date = datetime.now(),
                    singal_strength = result['adjusted_signal'],
                    confidence = result['confidence'],
                    recommendation = result['recommendation'],
                    current_pricce = result['current_price'],
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
            print(f"Error saveing results: {e}")
            raise e
        finally:
            self.db.close_session(session)

    def get_active_position(self):
        """Get all active positions"""
        session =self.db.get_session()
        try:
            positions = session.query(Position).filter(Position.is_active == True).all()
            return positions
        except Exception as e:
            print(f"Error getting active positions: {e}")
            raise e
        
    def create_position(self, symbol, quantity, entry_price, entry_date, current_stop_loss):
        """Create a new position"""
        session = self.db.get_session()
        try:
            position = Position(
                symbol = symbol,
                quantity = quantity,
                entry_price = entry_price,
                entry_date = datetime.now(),
                current_stop_loss = current_stop_loss,
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