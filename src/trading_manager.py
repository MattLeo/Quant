from backend.data_access import TradingDAO
from backend.models import Position, Trade, StopLossUpdate
from datetime import datetime
from execution_engine import ExecutionEngine

class TradingManager:
    def __init__(self, dao, analysis_framework, api_key=None, secret_key=None, paper_trading=True, auto_execute=False):
        self.dao = dao
        self.framework = analysis_framework
        self.auto_execute = auto_execute

        if api_key and secret_key:
            self.execution_engine = ExecutionEngine(api_key, secret_key, paper_trading)
        else:
            self.execution_engine = None
    
    def run_full_analysis(self, universe_type, execute_trades=False):
        """Run completed two-phase analysis with optional trade execution"""
        print("=== PHASE 1: POSITION MANAGEMENT ===")
        phase1_results = self._manage_existing_positions()

        executed_sells = []

        if  phase1_results.get('executed_sells'):
            executed_sells = phase1_results['executed_sells']

        print("=== PHASE 2: NEW OPPORTUNITIES ===")
        phase2_results = self._find_new_opportunities(universe_type)

        executed_buys = []
        failed_buys = []
        if execute_trades and phase2_results['recommendations']['buy_list']:
            executed_buys, failed_buys = self.execute_buy_recommendations(phase2_results['recommendations']['buy_list'], execute_trades=execute_trades)

        return {
            'position_management': phase1_results,
            'new_opportunities': phase2_results,
            'executed_trades': {
                'buys': executed_buys,
                'sells': executed_sells
            }
        }
    
    def _manage_existing_positions(self):
        """Phase 1: manage existing positions"""
        active_positions = self.dao.get_active_positions()

        if not active_positions:
            print("No active positions found.")
            return {
                'positions_checked': 0,
                'stop_losses_triggered': 0,
                'trailing_stops_updated': 0
            }
        
        print(f"Checking {len(active_positions)} active positions...")

        position_symbols = [pos.symbol for pos in active_positions]
        current_prices = self._get_current_prices(position_symbols)

        # Stop-Losses
        stop_triggers = self._check_stop_losses(current_prices)
        executed_sells = []

        if stop_triggers:
            print(f"Found {len(stop_triggers)} positions with stop loss triggered.")
            executed_sells = self._execute_stop_loss_sells(stop_triggers)

            for sell in executed_sells:
                print(f"Stop loss executed: {sell['symbol']} - Loss: ${sell['loss']:.2f}")
        else:
            print("No stop losses triggered.")

        # Trailing stops
        updated_stops = self._update_trailing_stops(current_prices)
        if updated_stops:
            print(f"Updated trailing stops for {len(updated_stops)} positions.")

        return {
            'positions_checked': len(active_positions),
            'stop_losses_triggered': len(executed_sells),
            'trailing_stops_updated': len(updated_stops),
            'executed_sells': executed_sells,
            'updated_stops': updated_stops,
            'stop_triggers': stop_triggers
        }
    
    def _find_new_opportunities(self, universe_type):
        """Phase 2: Find new investement opportunities"""
        results = self.framework.run_analysis(universe_type = universe_type)
        recommendations = self.framework.generate_recommendations(results)
        self.dao.save_recommendations_snapshot(recommendations['buy_list'], recommendations['sell_list'], recommendations['hold_list'])

        owned_symbols = self.dao.get_owned_symbols()
        original_buy_count = len(recommendations['buy_list'])
        filtered_count = 0

        if owned_symbols:
            recommendations['buy_list'] = [
                stock for stock in recommendations['buy_list'] 
                if stock['symbol'] not in owned_symbols
            ]
            filtered_count = original_buy_count - len(recommendations['buy_list'])
            if filtered_count > 0:
                print(f"Filtered out {filtered_count} buy recommendations (already owned).")

        self.dao.save_analysis_results(results)

        print("New opportunities found:")
        print(f"    Buy Signals: {len(recommendations['buy_list'])}")
        print(f"    Sell Signals: {len(recommendations['sell_list'])}")
        print(f"    Hold Signals: {len(recommendations['hold_list'])}")

        return {
            'analysis_results': results,
            'recommendations': recommendations,
            'total_analyzed': len(results),
            'filtered_duplicates': filtered_count
        }
    
    def _get_current_prices(self, symbols):
        """Get current prices for symbols"""
        current_prices = {}
        for symbol in symbols:
            try:
                data = self.framework.get_stock_data(symbol, days=5)
                if data is not None and len(data) > 0:
                    current_prices[symbol] = float(data['close'].iloc[-1])
            except Exception as e:
                print(f"Cound not get price for {symbol}: {e}")
        return current_prices
    
    def _calculate_stop_loss(self, entry_price, volatility, method='percentage'):
        """Calculate stop loss based on multiple methods"""
        if method == 'percentage':
            return entry_price * 0.92 # 8% stop loss
        elif method == 'volatility':
            daily_vol = volatility / (252**0.5)
            return entry_price * (1 - (2 * daily_vol))
        else:
            return entry_price * 0.95 # 5% stop loss as default
    
    def _check_stop_losses(self, current_prices):
        """Check if stop loss is triggered"""
        active_positions = self.dao.get_active_positions()
        stop_triggers = []

        for position in active_positions:
            current_price = current_prices.get(position.symbol)
            if current_price is None:
                continue

            stop_loss = position.current_stop_loss
            if current_price <= stop_loss:
                stop_triggers.append({
                    'position_id': position.id,
                    'symbol': position.symbol,
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'current_price': current_price,
                    'stop_loss': stop_loss,
                    'loss': current_price - stop_loss
                })

        return stop_triggers
    
    def execute_stop_losses(self, stop_triggers):
        """Execute stop losses via Alpaca API"""
        if not self.execution_engine:
            return self._execute_stop_loss_sells(stop_triggers)

        executed_sells = []
        failed_orders = []

        for trigger in stop_triggers:
            symbol = trigger['symbol']
            quantity = trigger['quantity']
            position_id = trigger['position_id']

            print(f"Executing stop loss for {symbol}...")
            order_result = self.execution_engine.place_sell_order(
                symbol = symbol,
                quantity = quantity,
                reason = 'STOP_LOSS'
            )

            if order_result['success']:
                trade_id = self.dao.record_trade(
                    position_id = position_id,
                    symbol = symbol,
                    action = 'SELL',
                    quantity = quantity,
                    price = order_result['filled_avg_price'],
                    reason = 'STOP_LOSS'
                )
                self.dao.close_position(position_id)
                
                executed_sells.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': order_result['filled_avg_price'],
                    'order_id': order_result['order_id'],
                    'trade_id': trade_id
                })
                print(f"Stop loss executed: {symbol} sold at ${order_result['filled_avg_price']:.2f}")
            else:
                failed_orders.append({
                    'symbol': symbol,
                    'error': order_result['error']
                })
                print(f"Failed to execute stop loss for {symbol}: {order_result['error']}")
        return executed_sells, failed_orders
    
    def _execute_stop_loss_sells(self, stop_triggers):
        """Execute stop loss sells"""
        executed_sells = []

        for trigger in stop_triggers:
            symbol = trigger['symbol']
            quantity = trigger['quantity']
            position_id = trigger['position_id']
            entry_price = trigger['entry_price']
            current_price = trigger['current_price']

            trade_id = self.dao.record_trade(
                position_id = position_id,
                symbol = symbol,
                action = 'SELL',
                quantity = quantity,
                price = current_price,
                reason = 'STOP_LOSS'
            )

            self.dao.close_position(position_id)

            executed_sells.append({
                'symbol': symbol,
                'quantity': quantity,
                'entry_price': entry_price,
                'exit_price': current_price,
                'loss': (entry_price - current_price) * quantity,
                'trade_id': trade_id
            })
    
        return executed_sells
    
    def _update_trailing_stops(self, current_prices, trail_percent=0.05):
        """Update trailing stops for profitable positions"""
        active_positions = self.dao.get_active_positions()
        updated_stops = []

        for position in active_positions:
            current_price = current_prices.get(position.symbol)
            if current_price is None:
                continue

            new_stop = current_price * (1 - trail_percent)

            if not position.current_stop_loss or new_stop > position.current_stop_loss:
                self.dao.update_stop_loss(position.id, new_stop, 'TRAILING')
                updated_stops.append({
                    'symbol': position.symbol,
                    'old_stop': position.current_stop_loss,
                    'new_stop': new_stop
                })

        return updated_stops
    
    def execute_buy_recommendations(self, buy_recommendations, execute_trades=False):
        """Execute buy recommendations via Alpaca API"""
        if not self.execution_engine or not execute_trades:
            print("Auto-execution disabeld. Buy recommendations available for manual review.")
            return [], []
        
        executed_buys = []
        failed_orders = []

        for recommendation in buy_recommendations:
            symbol = recommendation['symbol']
            signal_strength = recommendation['adjusted_signal']
            confidence = recommendation['confidence']
            current_price = recommendation['current_price']

            print(f"Executing buy order for {symbol}...")

            order_result = self.execution_engine.place_buy_order(
                symbol = symbol,
                signal_strength = signal_strength,
                confidence = confidence,
                current_price = current_price
            )

            if order_result['success']:
                volatility = recommendation['risk_metrics']['volatility']
                stop_price = self._calculate_stop_loss(
                    order_result['filled_avg_price'],
                    volatility
                )

                if order_result.get('is_pending', False):
                    position_id = self.dao.create_position(
                        symbol = symbol,
                        quantity = order_result['quantity'],
                        entry_price = current_price,
                        order_id = order_result['order_id'],
                        status = 'ordered',
                        stop_loss_price = stop_price
                    )

                    executed_buys.append({
                        'symbol': symbol,
                        'quantity': order_result['quantity'],
                        'price': current_price,
                        'status': 'ordered',
                        'position_id': position_id
                    })
                    print(f"⏳ {symbol} order pending")
                
                elif order_result['filled_qty'] > 0:
                    position_id = self.dao.create_position(
                        symbol = symbol,
                        quantity = order_result['filled_qty'],
                        entry_price = order_result['filled_avg_price'],
                        order_id = order_result['order_id'],
                        status = 'filled',
                        stop_loss_price = stop_price
                    )

                    executed_buys.append({
                        'symbol': symbol,
                        'quantity': order_result['filled_qty'],
                        'price': order_result['filled_avg_price'],
                        'status': 'filled',
                        'position_id': position_id
                    })

                    print(f"✅ {symbol} filled at ${order_result['filled_avg_price']:.2f}")
               
            else:
                failed_orders.append({
                    'symbol': symbol,
                    'error': order_result.get('error', 'Unknown error')
                })
                print(f"Failed to execute buy order for {symbol}: {order_result.get('error', 'Unknown error')}")
        return executed_buys, failed_orders
    
    def get_portfolio_summary(self):
        """Get summary of current portfolio"""
        active_positions = self.dao.get_active_positions()

        if not active_positions:
            return{'message': 'No active positions'}
        
        total_value = 0
        total_cost = 0
        position_symbols = [pos.symbol for pos in active_positions]
        current_prices = self._get_current_prices(position_symbols)

        portfolio_data = []
        for position in active_positions:
            current_price = current_prices.get(position.symbol, position.entry_price)
            current_value = current_price * position.quantity
            cost_basis = position.entry_price * position.quantity

            total_value += current_value
            total_cost += cost_basis

            portfolio_data.append({
                'symbol': position.symbol,
                'quantity': position.quantity,
                'entry_price': position.entry_price,
                'current_price': current_price,
                'current_value': current_value,
                'cost_basis': cost_basis,
                'stop_loss': position.current_stop_loss 
            })

        return {
            'positions': portfolio_data,
            'total_positions': len(active_positions),
            'total_value': total_value,
            'total_cost': total_cost,
            'total_unrealized_pnl': total_value - total_cost
        }
    
    def sync_with_alpaca(self):
        """Sync local database with Alpaca positions"""
        if not self.execution_engine:
            print("Execution engine not initialized. Cannot sync with Alpaca.")
            return {'success': False,'message': 'Execution engine not initialized'}
        try:
            alpaca_positions = self.execution_engine.get_current_positions()
            sync_result = self._sync_positions_with_stop_losses(alpaca_positions)

            if sync_result['success']:
                print("Successfully sycned positions with Alpaca")
            else:
                print(f"Failed to sync positions with Alpaca: {sync_result['error']}")

            return sync_result
        
        except Exception as e:
            print(f"Error syncing positions with Alpaca: {e}")
            return {'success': False, 'error': str(e)}
        
    def _sync_positions_with_stop_losses(self, alpaca_positions):
        """Sync positions with Alpaca API and calculate stop-losses"""
        session = self.dao.db.get_session()
        try:
            local_positions = session.query(Position).filter(Position.is_active == True).all()
            local_symbols = {pos.symbol: pos for pos in local_positions}
            alpaca_symbols = {pos['symbol']: pos for pos in alpaca_positions}

            for symbol, local_pos in local_symbols.items():
                if symbol not in alpaca_symbols:
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
                    print(f"New position detected: {symbol}")

                    entry_price = alpaca_pos['avg_entry_price']
                    stop_loss_price = self._calculate_stop_loss_for_sync(symbol, entry_price)

                    position = Position(
                        symbol = symbol,
                        quantity = alpaca_pos['quantity'],
                        entry_price = entry_price,
                        entry_date = datetime.now(),
                        current_stop_loss = stop_loss_price,
                        is_active = True
                    )
                    session.add(position)
                    session.flush()

                    trade = Trade(
                        position_id = position.id,
                        symbol = symbol,
                        action = 'BUY',
                        quantity = alpaca_pos['quantity'],
                        price = entry_price,
                        reason = 'SYNC_ADD'
                    )
                    session.add(trade)

                    if stop_loss_price:
                        stop_update = StopLossUpdate(
                            position_id = position.id,
                            old_stop_loss = None,
                            new_stop_loss = stop_loss_price,
                            update_date = datetime.now(),
                            reason = 'INITIAL',
                            current_price = entry_price
                        )
                        session.add(stop_update)
                    
                    else:
                        local_pos = local_symbols[symbol]
                        alpaca_qty = alpaca_pos['quantity']

                        if local_pos.quantity != alpaca_qty:
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

                        if local_pos.current_stop_loss is None:
                            print(f"Setting missing stop loss for {symbol}")
                            stop_loss_price = self._calculate_stop_loss_for_sync(symbol, local_pos.entry_price)
                            if stop_loss_price:
                                local_pos.current_stop_loss = stop_loss_price

                                stop_update = StopLossUpdate(
                                    position_id = local_pos.id,
                                    old_stop_loss = None,
                                    new_stop_loss = stop_loss_price,
                                    update_date = datetime.now(),
                                    reason = 'SYNC_SET',
                                    current_price = local_pos.entry_price
                                )
                                session.add(stop_update)
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
            self.dao.db.close_session(session)

    def _calculate_stop_loss_for_sync(self, symbol, entry_price):
        """Calculate stop loss for a position during sync"""
        try:
            data = self.framework.get_stock_data(symbol, days=90)
            if data is not None and len(data) >= 30:
                returns = data['close']. pct_change().dropna()
                volatility = returns.std() * (252**0.5)
                stop_loss_price = self._calculate_stop_loss(entry_price, volatility)
                print(f"Caluclated stop loss for {symbol}: {stop_loss_price:.2f}")
                return stop_loss_price
            else:
                stop_loss_price = entry_price * 0.92
                print(f"Using default stop loss for {symbol}: {stop_loss_price:.2f}")
                return stop_loss_price
            
        except Exception as e:
            print(f"Error calculating stop loss for {symbol}: {e}")
            print(f"Using default stop loss for {symbol}: {stop_loss_price:.2f}")
            stop_loss_price = entry_price * 0.92
            return stop_loss_price
        
    def check_ordered_positions(self):
        """Check ordered positions for updates"""
        if not self.execution_engine:
            print("Execution engine not initialized. Cannot check ordered positions.")
            return []
        
        try:
            ordered_positions = self.dao.get_ordered_position()
            
            if not ordered_positions:
                return []
            
            updated_positions = []

            for position in ordered_positions:
                order_status = self.execution_engine.get_order_status(position.order_id)

                if order_status['success'] and order_status['is_filled']:
                    actual_price = order_status['filled_avg_price']
                    success = self.dao.update_position(position.id, actual_price)

                    if success:
                        updated_positions.append({
                            'symbol': position.symbol,
                            'estimated_price': position.entry_price,
                            'actual_price': actual_price
                        })
                        print(f"{position.symbol} filled at ${actual_price:.2f}")
            return updated_positions
        except Exception as e:
            print(f"Error checking ordered positions: {e}")
            return []

        
    


        
        

