from backend.data_access import TradingDAO
from backend.models import Position, Trade
from datetime import datetime

class TradingManager:
    def __init__(self, dao, analysis_framework):
        self.dao = dao
        self.framework = analysis_framework
    
    def run_full_analysis(self, universe_type):
        """Run completed two-phase analysis"""
        print("=== PHASE 1: POSITION MANAGEMENT ===")
        phase1_results = self._manage_existing_positions()
        print("=== PHASE 2: NEW OPPORTUNITIES ===")
        phase2_results = self._find_new_opportunities(universe_type)

        return {
            'position_management': phase1_results,
            'new_opportunities': phase2_results
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
            'updated_stops': updated_stops
        }
    
    def _find_new_opportunities(self, universe_type):
        """Phase 2: Find new investement opportunities"""
        results = self.framework.run_analysis(universe_type = universe_type)
        recommendations = self.framework.generate_recommendations(results)

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
                    current_prices[symbol] = float(data['Close'].iloc[-1])
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

            stop_loss = position.stop_loss
            if current_price <= stop_loss:
                stop_triggers.append({
                    'position': position,
                    'current_price': current_price,
                    'stop_loss': stop_loss,
                    'loss': current_price - stop_loss
                })

        return stop_triggers
    
    def _execute_stop_loss_sells(self, stop_triggers):
        """Execute stop loss sells"""
        executed_sells = []

        for trigger in stop_triggers:
            position = trigger['position']
            current_price = trigger['current_price']

            trade_id = self.dao.record_trade(
                position_id = position.id,
                symbol = position.symbol,
                action = 'SELL',
                quantity = position.quantity,
                price = current_price,
                reason = 'STOP_LOSS'
            )

            self.dao.close_position(position.id)

            executed_sells.append({
                'symbol': position.symbol,
                'quantity': position.quantity,
                'entry_price': position.entry_price,
                'exit_price': current_price,
                'loss': (position.entry_price - current_price) * position.quantity,
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
    
    def get_portfolio_summary(self):
        """Get summary of current portfolio"""
        active_positions = self.dao.get_active_positions()

        if not active_positions:
            return{'message': 'No active positions'}
        
        total_value = 0
        total_cost = 0
        position_symbols = [pos.symbols for pos in active_positions]
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
    


        
        

