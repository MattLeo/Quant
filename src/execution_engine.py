import alpaca_trade_api as tradeapi
import time
import pandas as pd
import yfinance as yf

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
        
    def calculate_position_size(self, signal_strength, confidence, account_value, cash_balance, max_position_percent=0.06):
        """Calculate position size based on signal strength and risk management"""
        signal_quality = abs(signal_strength) * confidence

        if signal_quality > 0.8:
            base_percent = 0.05
        elif signal_quality > 0.6:
            base_percent = 0.03
        else:
            base_percent = 0.015
        
        position_size = base_percent * account_value
        if position_size > cash_balance:
            position_size = cash_balance
        
        max_position = max_position_percent * account_value
        
        return min(position_size, max_position)
    
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
                account_info['portfolio_value'],
                account_info['cash']
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
                'filled_avg_price': float(updated_order.filled_avg_price or 0),
                'is_pending': updated_order.status != 'filled'
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

    def check_order_status(self, order_id):
        """check if order is filled"""
        try:
            order = self.api.get_order(order_id)
            return {
                'success': True,
                'order_id': order_id,
                'status': order.status,
                'filled_avg_price': float(order.filled_avg_price or 0) if order.filled_avg_price else None,
                'is_filled': order.status != 'filled'
            }
        except Exception as e:
            return {'success': False, 'error':  {str(e)}}
    """      
    def get_yfinance_data(self, function, symbol):
        """"""
        Get data from yFinance
        functions: OVERVIEW | BALANCE_SHEET | INCOME_STATEMENT
        """"""
        
        try:
            ticker = yf.Ticker(symbol)
            
            if function == 'OVERVIEW':
                data = ticker.info
                if not data:
                    return None
                overview_data = {
                    'PERatio': data.get('trailingPE', data.get('forwardPE', 0)),
                    'PriceToBookRatio': data.get('priceToBook', 0),
                    'Symbol': data.get('symbol', symbol),
                    'MarketCapitalization': data.get('marketCap', 0),
                    'BookValue': data.get('bookValue', 0),
                    'DividendYield': data.get('dividendYield', 0),
                    'EPS': data.get('trailingEps', data.get('forwardEps', 0))
                }
                return overview_data
            elif function == 'BALANCE_SHEET':
                balance_sheet = ticker.balance_sheet
                if balance_sheet is None or len(balance_sheet) == 0:
                    return None
                
                quarterly_reports = []
                for date_col in balance_sheet.columns:
                    bs_data = balance_sheet[date_col]
                    report = {
                    'fiscalDateEnding': date_col.strftime('%Y-%m-%d'),
                    'totalAssets': bs_data.get('Total Assets', 0),
                    'totalCurrentAssets': bs_data.get('Current Assets', 0),
                    'totalCurrentLiabilities': bs_data.get('Current Liabilities', 0),
                    'totalLiabilities': bs_data.get('Total Liabilities Net Minority Interest', 0),
                    'totalDebt': bs_data.get('Total Debt', 0),
                    }
                    quarterly_reports.append(report)
                return {'quarterlyReports': quarterly_reports}
            
            elif function == 'INCOME_STATEMENT':
                financials = ticker.financials
                if financials is None or len(financials) == 0:
                    return None
                
                quarterly_reports = []
                for date_col in financials.columns:
                    income_statement = financials[date_col]
                    report = {
                    'fiscalDateEnding': date_col.strftime('%Y-%m-%d'),
                    'totalRevnue': income_statement.get('Total Revenue', 0),
                    'netIncome': income_statement.get('Net Income', 0),
                    }
                    quarterly_reports.append(report)
                return {'quarterlyReports': quarterly_reports}
            else:
                return {}
        except Exception as e:
            print(f"Error fetching data from yFinance: {e}")
            return {}
    """

    def get_yfinance_data(self, function, symbol):
        """
        Get extended historical data from yFinance
        """
        try:
            ticker = yf.Ticker(symbol)
            
            if function == 'OVERVIEW':
                info = ticker.info
                if not info:
                    return None
                return {
                    'PERatio': info.get('trailingPE', info.get('forwardPE', 0)),
                    'PriceToBookRatio': info.get('priceToBook', 0), 
                    'ReturnOnEquityTTM': info.get('returnOnEquity', 0),
                }
                
            elif function == 'BALANCE_SHEET':
                quarterly_bs = ticker.quarterly_balance_sheet
                annual_bs = ticker.balance_sheet 
                
                all_data = pd.concat([quarterly_bs, annual_bs], axis=1).sort_index(axis=1, ascending=False)
                
                if all_data is None or all_data.empty:
                    return None
                
                print(f"DEBUG - Combined balance sheet columns: {len(all_data.columns)}")
                
                quarterly_reports = []
                for date_col in all_data.columns[:8]: 
                    report = {'fiscalDateEnding': date_col.strftime('%Y-%m-%d')}
                    
                    if 'Total Assets' in all_data.index:
                        report['totalAssets'] = all_data.loc['Total Assets', date_col]
                    if 'Current Assets' in all_data.index:
                        report['totalCurrentAssets'] = all_data.loc['Current Assets', date_col]
                    if 'Current Liabilities' in all_data.index:
                        report['totalCurrentLiabilities'] = all_data.loc['Current Liabilities', date_col]
                    if 'Total Liabilities Net Minority Interest' in all_data.index:
                        report['totalLiabilities'] = all_data.loc['Total Liabilities Net Minority Interest', date_col]
                    if 'Total Debt' in all_data.index:
                        report['totalDebt'] = all_data.loc['Total Debt', date_col]
                    
                    for key in ['totalAssets', 'totalCurrentAssets', 'totalCurrentLiabilities', 'totalLiabilities', 'totalDebt']:
                        if key not in report:
                            report[key] = 0
                            
                    quarterly_reports.append(report)
                
                print(f"DEBUG - Final balance sheet reports: {len(quarterly_reports)}")
                return {'quarterlyReports': quarterly_reports}
                
            elif function == 'INCOME_STATEMENT':
                quarterly_fin = ticker.quarterly_financials
                annual_fin = ticker.financials
                
                all_data = pd.concat([quarterly_fin, annual_fin], axis=1).sort_index(axis=1, ascending=False)
                
                if all_data is None or all_data.empty:
                    return None
                    
                print(f"DEBUG - Combined income statement columns: {len(all_data.columns)}")
                
                quarterly_reports = []
                for date_col in all_data.columns[:8]: 
                    report = {'fiscalDateEnding': date_col.strftime('%Y-%m-%d')}
                    
                    if 'Total Revenue' in all_data.index:
                        report['totalRevenue'] = all_data.loc['Total Revenue', date_col]
                    if 'Net Income' in all_data.index:
                        report['netIncome'] = all_data.loc['Net Income', date_col]
                    
                    for key in ['totalRevenue', 'netIncome']:
                        if key not in report:
                            report[key] = 0
                            
                    quarterly_reports.append(report)
                
                return {'quarterlyReports': quarterly_reports}
                
        except Exception as e:
            print(f"ERROR fetching data from yFinance for {symbol}: {e}")
            return None