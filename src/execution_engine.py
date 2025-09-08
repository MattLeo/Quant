import alpaca_trade_api as tradeapi
import time

class ExecutionEngine:
    def __init__(self, api_key, secret_key, paper_trading=True):
        base_url = 'https://paper-api.alpaca.markets' if paper_trading else 'https://api.alpaca.markets'
        self.api = tradeapi.REST(key_id=api_key, secret_key=secret_key, base_url=base_url)
        self.paper_trading = paper_trading

    def get_account_info(self):
        """Get current account info"""
        try:
            account = self.api.get_account()
            return {
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity),
                'trading_blocked': account.trading_blocked,
                'account_blocked': account.account_blocked,
                'pattern_day_trader': getattr(account, 'pattern_day_trader', False),
                'status': account.status
            }
        except Exception as e:
            print(f"Error fetching account info: {e}")
            return None
        
    def calculate_position_size(self, signal_strength, confidence, account_value, max_position_percent=0.02):
        """Calculate position size based on signal strength and risk management"""
        base_size = account_value * max_position_percent
        adjustment_factor = (abs(signal_strength) * confidence)
        adjusted_size = base_size * adjustment_factor
        max_size = account_value * 0.05 # Keeping maximum investment size to 5% of account
        return min(adjusted_size, max_size)
    
    def place_buy_order(self, symbol, signal_strength, confidence, current_price):
        """Place a buy order for a stock"""
        try:
            account_info = self.get_account_info()
            if not account_info or account_info['trading_blocked']:
                return {
                    'success': False,
                    'error': 'Trading blocked or account info unavailable'
                }
            
            position_value = self.calculate_position_size(
                signal_strength,
                confidence,
                account_info['portfolio_value']
            )

            raw_shares = position_value / current_price

            try:
                asset = self.api.get_asset(symbol)
                fractionable = getattr(asset, 'fractionable', False)
            except:
                fractionable = False

            if fractionable:
                shares = round(raw_shares, 6)
                min_shares =  0.001
            else:
                shares = int(raw_shares)
                min_shares = 1
            
            if shares < min_shares:
                return {
                    'success': False, 
                    'error': f'Position size too small: {shares:.6f} shares (min: {min_shares})'
                }
            
            actual_position_value = shares * current_price

            if actual_position_value > account_info['buying_power']:
                return {
                    'success': False,
                    'error': f'Insufficient buying power: ${account_info["buying_power"]:.2f} available, ${actual_position_value:.2f} needed'
                }
                
            order = self.api.submit_order(
                symbol=symbol,
                qty=shares,
                side='buy',
                type='market',
                time_in_force='day'
            )

            time.sleep(2)
            updated_order = self.api.get_order(order.id)

            return {
                'success': True,
                'order_id': order.id,
                'symbol': symbol,
                'quantity': float(shares),
                'estimated_value': actual_position_value,
                'status': updated_order.status,
                'filled_qty': float(updated_order.filled_qty or 0),
                'filled_avg_price': float(updated_order.filled_avg_price or 0)
            }
        except Exception as e:
            return {'success': False, 'error': f'Order execution failed:  {str(e)}'}
        
    def place_sell_order(self, symbol, quantity, reason='SIGNAL'):
        """Place a sell order for a position"""
        try:
            # Verify that position matches with sell order
            try:
                position = self.api.get_position(symbol)
                available_qty = float(position.qty)

                if available_qty < quantity:
                    quantity = available_qty

            except tradeapi.rest.APIError:
                return {'success': False, 'error': f'No position found for {symbol}'}
            
            order = self.api.submit_order(
                symbol=symbol,
                qty=quantity,
                side='sell',
                type='market',
                time_in_force='day'
            )

            time.sleep(2)
            updated_order = self.api.get_order(order.id)

            return {
                'success': True,
                'order_id': order.id,
                'symbol': symbol,
                'quantity': quantity,
                'status': updated_order.status,
                'filled_qty': float(updated_order.filled_qty or 0),
                'filled_avg_price': float(updated_order.filled_avg_price or 0)
            }
        except Exception as e:
            return {'success': False, 'error': f'Sell order failed: {str(e)}'}
        
    def get_current_positions(self):
        """Get current positions from Alpaca"""
        try:
            positions = self.api.list_positions()
            if len(positions) < 1:
                return []
            return [{
                'symbol': pos.symbol,
                'quantity': float(pos.qty),
                'market_value': float(pos.market_value),
                'cost_basis': float(pos.cost_basis),
                'unrealized_pnl': float(pos.unrealized_pl),
                'avg_entry_price': float(pos.avg_entry_price)
            } for pos in positions]
        except Exception as e:
            print(f"Error fetching positions: {e}")
            return []
