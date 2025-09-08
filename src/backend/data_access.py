from .database import db_manager
from .models import Position, Trade, AnalysisResult, StopLossUpdate
from datetime import datetime
from sqlalchemy import desc

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

    def get_trade_history(self):
        """Get records of previous trades"""
        session = self.db.get_session()
        try:
            trades = session.query(Trade).order_by(desc(Trade.trade_date)).all()
            return trades
        finally:
            self.db.close_session(session)

    def sync_positions_with_alapaca(self, alpaca_positions):
        """Sync local database positions with Alpaca"""
        session = self.db.get_session()
        try:
            print("Starting positions sync with Alpaca...")

            local_positions = session.query(Position).filter(Position.is_active == True).all()
            local_symbols = set(pos.symbol for pos in local_positions)

            alpaca_symbols = {pos['symbol']: pos for pos in alpaca_positions}

            for symbol, local_pos in local_symbols.items():
                if symbol not in alpaca_symbols:
                    print(f"Position {symbol} not found in Alpaca. Closing local position.")
                    local_pos.is_active = False
                    
                    trade = Trade(
                        position_id = local_pos.id,
                        symbol = symbol,
                        action = 'SELL',
                        quantity = local_pos.quantity,
                        price = local_pos.entry_price,
                        reason = 'SYNC_CLOSE'
                    )
                    session.add(trade)

            for symbol, alpaca_pos in alpaca_symbols.items():
                if symbol not in local_symbols:
                    print(f"Position {symbol} found in Alpaca. Creating local position.")
                    position = Position(
                        symbol = symbol,
                        quantity = int(alpaca_pos['quantity']),
                        entry_price = alpaca_pos['avg_entry_price'],
                        entry_date = datetime.now(),
                        current_stop_loss = None,
                        is_active = True
                    )
                    session.add(position)
                    session.flush()

                    trade = Trade(
                        position_id = position.id,
                        symbol = symbol,
                        action = 'BUY',
                        quantity = int(alpaca_pos['quantity']),
                        price = alpaca_pos['avg_entry_price'],
                        reason = 'SYNC_ADD'
                    )
                    session.add(trade)
                else:
                    local_pos = local_symbols[symbol]
                    alpaca_qty = int(alpaca_pos['quantity'])

                    if local_pos.quantity != alpaca_pos:
                        print(f"Position {symbol} quantity mismatch for {symbol}: {local_pos.quantity} -> {alpaca_qty}")
                        qty_diff = alpaca_qty - local_pos.quantity
                        action = 'BUY' if qty_diff > 0 else 'SELL'

                        trade = Trade(
                            position_id = local_pos.id,
                            symbol = symbol,
                            action = action,
                            quantity = abs(qty_diff),
                            price = alpaca_pos['avg_entry_price'],
                            reason = 'SYNC_UPDATE'
                        )
                        session.add(trade)
                        local_pos.quantity = alpaca_qty
                        if alpaca_qty == 0:
                            local_pos.is_active = False

            session.commit()
            print(f"Positions sync with Alpaca complete. {len(alpaca_symbols)} positions synced.")
            return {
                'success': True,
                'synced_positions': len(alpaca_symbols)
            }
        
        except Exception as e:
            session.rollback()
            print(f"Error syncing positons: {e}")
            return {'success': False, 'error': str(e)}
        
        finally:
            self.db.close_session(session)