import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
import time
import logging
from execution_engine import ExecutionEngine
from regime_detector import MarketRegimeDetector


logger = logging.getLogger("console_log")

class TradingAnalysis:
    """Trading analysis of stocks to track performance"""

    def __init__(self, api_key, secret_key, vol_regime='high'):
        self.api = tradeapi.REST(
            key_id=api_key,
            secret_key=secret_key,
            base_url='https://paper-api.alpaca.markets'
        )

        self.execution_engine = ExecutionEngine(
            api_key=api_key,
            secret_key=secret_key,
            paper_trading=True
       )
        
        self.regime_detector = MarketRegimeDetector()

        # Initial signal weights
        self.technical_weights = {
            'sma_crossover': 0.22,
            'rsi_signal': 0.18,
            'volume_signal': 0.13,
            'macd_signal': 0.18,
            'bollinger_signal': 0.14,
            'stochastic_signal': 0.15
        }

        self.fundamental_weights = {
            'pe_ratio': 0.20,
            'rev_growth': 0.15,
            'earnings_growth': 0.18,
            'roe_signal': 0.15,
            'debt_to_equity': 0.12,
            'pb_ratio': 0.12,
            'current_ratio': 0.08 
        }

        if vol_regime == 'high':
            self.layer_weights = {
                'technical': 0.7,
                'fundamental': 0.3
            }
        else:
            self.layer_weights = {
                'technical': 0.3,
                'fundamental': 0.7
            }

        self.current_regime_analysis = None
        self.last_regime_check = None

        # Buy/Sell Thresholds
        self.buy_threshold = 0.3
        self.sell_threshold = -0.3


    def update_market_regime(self, force_update=False):
        """Update market regime analysis"""
        if(not force_update and
           self.last_regime_check and
           (datetime.now() - self.last_regime_check).days < 1):
            return self.current_regime_analysis
        
        print("[*] Updating market regime analysis...")
        self.current_regime_analysis = self.regime_detector.determine_overall_regime()
        self.last_regime_check = datetime.now()

        if self.current_regime_analysis:
            self.layer_weights = self.current_regime_analysis['strategy_weights']
            regime = self.current_regime_analysis['regime']
            self.adjust_technical_weights_by_regime(regime)

        return self.current_regime_analysis

    def adjust_technical_weights_by_regieme(self, regime):
        """Adjust the technical indicator weighting based on market regime"""
        if regime == 'high_volitility':
            self.technical_weights = {
                'rsi_signal': 0.25,
                'macd_signal': 0.22,
                'bollinger_signal': 0.20,
                'stochastic_signal': 0.18,
                'sma_crossover': 0.10,
                'volume_signal': 0.05
            }

        elif regime == 'low_volitility':
            self.technical_weights = {
                'sma_crossover': 0.3,
                'macd_signal': 0.25,
                'volume_signal': 0.15,
                'bollinger_signal': 0.12,
                'rsi_signal': 0.1,
                'stochastic_signal': 0.08
            }

        elif regime == 'trending_bullish':
            self.technical_weights = {
                'macd_signal': 0.28,
                'sma_crossover': 0.25,
                'volume_signal': 0.18,
                'stochastic_signal': 0.15,
                'volume_signal': 0.12,
                'sma_crossover': 0.05
            }

        else: # transitional regime
            self.technical_weights = {
                'sma_crossover': 0.18,
                'rsi_signal': 0.18,
                'macd_signal': 0.18,
                'bollinger_signal': 0.16,
                'stochastic_signal': 0.15,
                'volume_signal': 0.15
            }

    def set_thresholds(self, regime):
        """Adjust buy/sell signal thresholds based on market regime"""
        if regime == 'high_volitility':
            self.buy_threshold = 0.65
            self.sell_threshold = -0.55
        elif regime == 'low_volitility':
            self.buy_threshold = 0.45
            self.sell_threshold = -0.65
        elif regime == 'trending_bullish':
            self.buy_threshold = 0.4
            self.sell_threshold = -0.7
        elif regime == 'trending_bearish':
            self.buy_threshold = 0.75
            self.sell_threshold = -0.4
        else: # transitional market
            self.buy_threshold = 0.55
            self.sell_threshold = -0.6

    def get_starter_stocks(self):
        """Layer 1: Basic analysis of popular stocks"""

        starter_stocks = [
            # Tech Sector
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'NVDA', 'NFLX', 'AMD', 'CRM',
            # ETFs
            'SPY', 'QQQ',
            # Finance & Healthcare
            'JPM', 'JNJ', 'PFE',  # Fixed: JPM not JMP
            # Growth
            'PYPL', 'ZOOM', 'ROKU', 'SQ', 'SHOP'
        ]

        print(f"[*] Analyzing {len(starter_stocks)} stocks...")
        logger.info(f"[*] Analyzing {len(starter_stocks)} stocks...\n")
        return starter_stocks
    
    def get_all_tradable_symbols(self, filters=None):
        """Get all tradable symbols with optional filtering"""
        try:
            assets = self.api.list_assets(status='active', asset_class='us_equity')

            all_symbols = []
            for asset in assets:
                if asset.tradable and asset.shortable:
                    all_symbols.append({
                        'symbol': asset.symbol,
                        'name': asset.name,
                        'exchange': asset.exchange
                    })
            print(f"    Found {len(all_symbols)} total tradable symbols")
            logger.info(f"[*] Found {len(all_symbols)} total tradable symbols [*]\n")

            if filters:
                filtered_symbols = self.apply_universe_filters(all_symbols, filters)
                print(f"    After Filtering: {len(filtered_symbols)} symbols remain")
                logger.info(f"[*] After Filtering: {len(filtered_symbols)} symbols remain [*]\n")
                return filtered_symbols
            return [s['symbol'] for s in all_symbols]
        except Exception as e:
            print(f"    ✗ Error fetching all tradable symbols: {e}")
            return self.get_starter_stocks()
    
    def apply_universe_filters(self, symbols, filters):
        """Apply filtering criteria to reduce universe size"""
        print("[*] Applying universe filters...")
        print(f"   Starting with {len(symbols)} symbols")
    
        filtered = []
        excluded_counts = {'patterns': 0, 'exchanges': 0, 'penny_stocks': 0}
    
        for symbol_info in symbols:
            symbol = symbol_info['symbol']
            excluded = False
        
            # Skip complex instruments by pattern
            if filters.get('exclude_patterns'):
                if any(pattern in symbol for pattern in filters['exclude_patterns']):
                    excluded_counts['patterns'] += 1
                    excluded = True
                    continue
        
            # Filter by exchange
            if filters.get('exchanges'):
                if symbol_info['exchange'] not in filters['exchanges']:
                    excluded_counts['exchanges'] += 1
                    excluded = True
                    continue
        
            # Skip penny stocks by pattern
            if filters.get('exclude_penny_stocks'):
                if (len(symbol) > 4 or  # Long symbols usually penny stocks
                    any(char in symbol for char in ['.', '-']) or
                    symbol.endswith(('F', 'Y', 'U', 'W'))):
                    excluded_counts['penny_stocks'] += 1
                    excluded = True
                    continue
        
            if not excluded:
                filtered.append(symbol)
    
        print(f"   Excluded: {excluded_counts}")
        print(f"   Remaining: {len(filtered)} symbols")
        return filtered

    def get_stock_data(self, symbol, days=183):
        """Get historical data for analysis"""

        try:
            end_datetime = datetime.now() - timedelta(days=1)
            start_datetime = end_datetime - timedelta(days=days)

            end_date = end_datetime.date().isoformat()
            start_date = start_datetime.date().isoformat()

            print(f"   Fetching data from {start_date} to {end_date}")
            logger.info(f"  Fetching data from {start_date} to {end_date}\n")

            bars = self.api.get_bars(
                symbol,
                timeframe='1Day',
                start=start_date,
                end=end_date,
                feed='iex'
            )

            if not bars:
                print(f"   No bars returned for {symbol}")
                return None

            data = pd.DataFrame([{
                'date': bar.t.date(),  # t = timestamp
                'open': float(bar.o),   # o = open
                'high': float(bar.h),   # h = high
                'low': float(bar.l),    # l = low
                'close': float(bar.c),  # c = close
                'volume': int(bar.v)    # v = volume
            } for bar in bars])

            if len(data) == 0:
                print(f"   Empty dataset for {symbol}")
                return None

            data.set_index('date', inplace=True)
            data = data.sort_index()

            print(f"   ✓ Gathered {len(data)} days of data for {symbol}")
            logger.info(f"  ✓ Gathered {len(data)} days of data for {symbol}\n")
            return data
        
        except Exception as e:
            print(f"   ✗ Error fetching data for {symbol}: {e}")
            logger.info(f"   ✗ Error fetching data for {symbol}: {e}\n")
            return None
    
    def calculate_sma(self, data):
        """Simple Moving Average Crossover"""
        if len(data) < 50:
            return 0, 0

        # Calculating Moving Average
        data['sma_20'] = data['close'].rolling(window=20).mean()
        data['sma_50'] = data['close'].rolling(window=50).mean()

        # Current position related to MAs
        current_price = data['close'].iloc[-1]
        sma_20 = data['sma_20'].iloc[-1]
        sma_50 = data['sma_50'].iloc[-1]

        # Signal strength based on MAs
        if pd.isna(sma_20) or pd.isna(sma_50):
            return 0, 0
        
        # Trending up
        if current_price > sma_20 > sma_50:
            signal = 0.8
        # Trending down
        elif current_price < sma_20 < sma_50:
            signal = -0.8
        # Mixed signals
        elif current_price > sma_20 and sma_20 < sma_50:
            signal = 0.3
        elif current_price < sma_20 and sma_20 > sma_50:
            signal = -0.3
        else:
            signal = 0

        # Confidence rating based on separation
        ma_separation = abs(sma_20 - sma_50) / sma_50
        confidence = min(1.0, ma_separation * 20)

        return signal, confidence
    
    def calculate_rsi(self, data):
        """Relative Strength Index"""
        if len(data) < 15:
            return 0, 0

        # Calculating RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        current_rsi = rsi.iloc[-1]

        if pd.isna(current_rsi):
            return 0, 0
        
        # RSI Signals
        if current_rsi < 30:
            signal = 0.9
            confidence = 0.8
        elif current_rsi < 40:
            signal = 0.5
            confidence = 0.6
        elif current_rsi > 70:
            signal = -0.9
            confidence = 0.8
        elif current_rsi > 60:
            signal = -0.5
            confidence = 0.6
        else:
            signal = 0
            confidence = 0.3

        return signal, confidence
    
    def calculate_volume(self, data):
        """Volume Analysis"""
        if len(data) < 20:
            return 0, 0

        try:
            # Calculate 20-day average volume
            avg_volume_series = data['volume'].rolling(window=20).mean()
            current_volume = float(data['volume'].iloc[-1])
            
            avg_volume = float(avg_volume_series.iloc[-1])

            if pd.isna(avg_volume) or avg_volume <= 0:
                return 0, 0
            
            volume_ratio = current_volume / avg_volume
            
            current_price = float(data['close'].iloc[-1])
            previous_price = float(data['close'].iloc[-2])
            price_change = (current_price - previous_price) / previous_price

            # Volume signals with price movement
            if volume_ratio > 2.0 and price_change > 0.02:
                signal = 0.7
                confidence = 0.8
            elif volume_ratio > 2.0 and price_change < -0.02:
                signal = -0.7
                confidence = 0.8
            elif volume_ratio > 1.5 and price_change > 0.01:
                signal = 0.4
                confidence = 0.6
            elif volume_ratio > 1.5 and price_change < -0.01:
                signal = -0.4
                confidence = 0.6
            else:
                signal = 0
                confidence = 0.3

            return signal, confidence
            
        except Exception as e:
            print(f"   Warning: Volume calculation error: {e}")
            return 0, 0.1
    
    def calculate_risk_metrics(self, data):
        """Basic risk assessment"""
        if len(data) < 30:
            return {'volatility': 0.5, 'risk_score': 0.5}
        
        returns = data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)
        recent_vol = returns.tail(10).std() * np.sqrt(252)
        vol_ratio = recent_vol / volatility if volatility > 0 else 1
        risk_score = min(1.0, volatility * 2)

        return {
            'volatility': volatility,
            'recent_volatility': recent_vol,
            'volatility_ratio': vol_ratio,
            'risk_score': risk_score
        }
    
    def analyze_stock(self, symbol):
        """Analyze a single stock with all signals"""
        print(f"\n[*] Analyzing {symbol}...")
        logger.info(f"\n[*] Analyzing {symbol}...\n")

        # Getting data
        data = self.get_stock_data(symbol)
        if data is None or len(data) < 50: 
            print(f"    ✗ Insufficient data for {symbol}")
            logger.info(f"    ✗ Insufficient data for {symbol}\n")
            return None
        
        overview = self.execution_engine.get_yfinance_data('OVERVIEW', symbol)
        if overview is None:
            print(f"    ✗ No overview data for {symbol}")
            logger.info(f"    ✗ No overview data for {symbol}\n")

        balance_sheet = self.execution_engine.get_yfinance_data('BALANCE_SHEET', symbol)
        if balance_sheet is None or len(balance_sheet['quarterlyReports']) < 8:
            print(f"    ✗ No balance sheet data for {symbol}")
            logger.info(f"    ✗ No balance sheet data for {symbol}\n")

        income_statement = self.execution_engine.get_yfinance_data('INCOME_STATEMENT', symbol)
        if income_statement is None or len(income_statement['quarterlyReports']) < 8:
            print(f"    ✗ No income statement data for {symbol}")
            logger.info(f"    ✗ No income statement data for {symbol}\n")

        # Calculating all signals
        sma_signal, sma_confidence = self.calculate_sma(data)
        rsi_signal, rsi_confidence = self.calculate_rsi(data)
        vol_signal, vol_confidence = self.calculate_volume(data)
        macd_signal, macd_confidence = self.calculate_macd(data)
        bollinger_signal, bollinger_confidence = self.calculate_bollinger_bands(data)
        stochastic_signal, stochastic_confidence = self.calculate_stochastic(data)

        pe_signal, pe_confidence = self.calculate_pe(overview)
        pb_signal, pb_confidence = self.calculate_pb(overview)
        roe_signal, roe_confidence, roe = self.calculate_roe(overview)
        current_signal, current_confidence = self.calculate_current_ratio(balance_sheet)
        dte_signal, dte_confidence = self.calculate_debt_to_equity(balance_sheet, roe)
        rev_growth_signal, rev_growth_confidence = self.calculate_revenue_growth(income_statement)
        earnings_singal, earnings_confidence = self.calculate_earnings_growth(income_statement)

        

        risk_metrics = self.calculate_risk_metrics(data)

        technical_signal = (
            sma_signal * sma_confidence * self.technical_weights['sma_crossover'] +
            rsi_signal * rsi_confidence * self.technical_weights['rsi_signal'] +
            vol_signal * vol_confidence * self.technical_weights['volume_signal'] +
            macd_signal * macd_confidence * self.technical_weights['macd_signal'] +
            bollinger_signal * bollinger_confidence * self.technical_weights['bollinger_signal'] +
            stochastic_signal * stochastic_confidence * self.technical_weights['stochastic_signal']
        )

        fundamental_signal = (
            pe_signal * pe_confidence * self.fundamental_weights['pe_ratio'] +
            pb_signal * pb_confidence * self.fundamental_weights['pb_ratio'] +
            roe_signal * roe_confidence * self.fundamental_weights['roe_signal'] +
            current_signal * current_confidence * self.fundamental_weights['current_ratio'] +
            dte_signal * dte_confidence * self.fundamental_weights['debt_to_equity'] +
            rev_growth_signal * rev_growth_confidence * self.fundamental_weights['rev_growth'] +
            earnings_singal * earnings_confidence * self.fundamental_weights['earnings_growth']
        )

        technical_confidence = (
            sma_confidence * self.technical_weights['sma_crossover'] +
            rsi_confidence * self.technical_weights['rsi_signal'] +
            vol_confidence * self.technical_weights['volume_signal'] +
            macd_confidence * self.technical_weights['macd_signal'] +
            bollinger_confidence * self.technical_weights['bollinger_signal'] +
            stochastic_confidence * self.technical_weights['stochastic_signal']
        )

        fundamental_confidence = (
            pe_confidence * self.fundamental_weights['pe_ratio'] +
            pb_confidence * self.fundamental_weights['pb_ratio'] +
            roe_confidence * self.fundamental_weights['roe_signal'] +
            current_confidence * self.fundamental_weights['current_ratio'] +
            dte_confidence * self.fundamental_weights['debt_to_equity'] +
            rev_growth_confidence * self.fundamental_weights['rev_growth'] +
            earnings_confidence * self.fundamental_weights['earnings_growth']
        )

        total_signal = (
            technical_signal * self.layer_weights['technical'] +
            fundamental_signal * self.layer_weights['fundamental']
        )

        total_confidence = (
            technical_confidence + self.layer_weights['technical'] +
            fundamental_confidence + self.layer_weights['fundamental']
        )

        # Risk adjustment
        risk_adjustment = 1 - (risk_metrics['risk_score'] * 0.3)
        adjusted_signal = total_signal * risk_adjustment

        # Generating recommendation
        if adjusted_signal > self.buy_threshold and total_confidence > 0.5:
            recommendation = 'BUY'
        elif adjusted_signal < self.sell_threshold and total_confidence > 0.5:
            recommendation = 'SELL'
        else:
            recommendation = 'HOLD'
        
        current_price = data['close'].iloc[-1]

        result = {
            'symbol': symbol,
            'current_price': current_price,
            'total_signal': total_signal,
            'adjusted_signal': adjusted_signal,
            'confidence': total_confidence,
            'recommendation': recommendation,
            'signals': {
                'sma': {'value': sma_signal, 'confidence': sma_confidence},
                'rsi': {'value': rsi_signal, 'confidence': rsi_confidence},
                'macd': {'value': macd_signal, 'confidence': macd_confidence},
                'bollinger': {'value': bollinger_signal, 'confidence': bollinger_confidence},
                'stochastic': {'value': stochastic_signal, 'confidence': stochastic_confidence},
                'volume': {'value': vol_signal, 'confidence': vol_confidence},
                'pe': {'value': pe_signal, 'confidence': pe_confidence},
                'pb': {'value': pb_signal, 'confidence': pb_confidence},
                'roe': {'value': roe_signal, 'confidence': roe_confidence},
                'current_ratio': {'value': current_signal, 'confidence': current_confidence},
                'debt_to_equity': {'value': dte_signal, 'confidence': dte_confidence},
                'rev_growth': {'value': rev_growth_signal, 'confidence': rev_growth_confidence},
                'earnings_growth': {'value': earnings_singal, 'confidence': earnings_confidence}
            },
            'risk_metrics': risk_metrics
        }
        return result
    
    def run_analysis(self, universe_type='starter', max_stocks=None, batch_size=50, save_progress=True, results_folder = 'analysis_results'):
        """Run analysis on all stocks"""
        
        print("🚀 Starting Basic Analysis Stocks")
        print("=" * 50)

        if universe_type == 'starter':
            stocks = self.get_starter_stocks()
        elif universe_type == 'all':
            stocks = self.get_all_tradable_symbols()
        elif universe_type == 'filtered':
            filters = {
                'exclude_penny_stocks': True,
                'exchanges': ['NASDAQ', 'NYSE'],
                'exclude_patterns': ['.', '-', 'WARRANT', 'UNIT', 'RT'],
            }
            stocks = self.get_all_tradable_symbols(filters)
        else:
            print(f"Unknown universe type '{universe_type}', using starter")
            stocks = self.get_starter_stocks()

        if max_stocks:
            stocks = stocks[:max_stocks]

        total_stocks = len(stocks)
        print(f"📊 Total stocks to analyze: {total_stocks}")
        logger.info(f"Total stocks to analyze: {total_stocks}\n")

        print(f"🔄 Processing in batches of {batch_size}")

        results = []
        failed_symbols = []

        for batch_start in range(0, total_stocks, batch_size):
            batch_end = min(batch_start + batch_size, total_stocks)
            batch_stocks = stocks[batch_start:batch_end]
            batch_num = (batch_start // batch_size) + 1
            total_batches = (total_stocks // batch_size) + 1

            print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch_stocks)} stocks)")
            print("-" * 50)

            batch_results = []

            for i, symbol in enumerate(batch_stocks, 1):
                progress = batch_start + i
                print(f"[{progress}/{total_stocks}] ", end="")
                logger.info(f"[{progress}/{total_stocks}]\n")

                result = self.analyze_stock(symbol)

                if result:
                    batch_results.append(result)
                    results.append(result)
                else:
                    failed_symbols.append(symbol)
                
                time.sleep(0.2)

            if batch_end < total_stocks:
                time.sleep(2)

        print("\n")
        print("=" * 50)
        print(f"📈 ANALYSIS COMPLETE")
        print("=" * 50)
        print(f"✅ Successfully analyzed: {len(results)}")
        print(f"❌ Failed to analyze: {len(failed_symbols)}")
        print(f"📊 Success rate: {len(results)/total_stocks*100:.1f}%")

        if failed_symbols:
            print(f"❌ Failed symbols: {', '.join(failed_symbols[:10])}{'...' if len(failed_symbols) > 10 else ''}")

        results.sort(key=lambda x: x['adjusted_signal'], reverse=True)
        
        return results

    def generate_recommendations(self, results):
        """Generate recommendations based on analysis results"""
        print("\n" + "=" * 50)
        print("📝 FINAL RECOMMENDATIONS")
        print("=" * 50)

        buy_recommendations = [r for r in results if r['recommendation'] == "BUY"]
        sell_recommendations = [r for r in results if r['recommendation'] == "SELL"]
        hold_recommendations = [r for r in results if r['recommendation'] == "HOLD"]

        print(f"\n🟢 BUY SIGNALS ({len(buy_recommendations)}):")
        for i, stock in enumerate(buy_recommendations[:5], 1):
            print(f"  {i}. {stock['symbol']} - ${stock['current_price']:.2f}")
            print(f"     Signal: {stock['adjusted_signal']:.3f} | Confidence: {stock['confidence']:.2f}")
            print(f"     Risk: {stock['risk_metrics']['risk_score']:.2f} | Vol: {stock['risk_metrics']['volatility']:.2f}")

        print(f"\n🔴 SELL SIGNALS ({len(sell_recommendations)}):")
        for i, stock in enumerate(sell_recommendations[:3], 1):
            print(f"  {i}. {stock['symbol']} - ${stock['current_price']:.2f}")
            print(f"     Signal: {stock['adjusted_signal']:.3f} | Confidence: {stock['confidence']:.2f}")
        
        print(f"\n⚪ HOLD/NEUTRAL ({len(hold_recommendations)}):")
        for stock in hold_recommendations[:3]:
            print(f"     {stock['symbol']}: {stock['adjusted_signal']:.3f}")

        if results:
            avg_signal = np.mean([r['adjusted_signal'] for r in results])
            avg_confidence = np.mean([r['confidence'] for r in results])

            print(f"\n📊 MARKET SUMMARY:")
            print(f"   Average Signal: {avg_signal:.3f}")
            print(f"   Average Confidence: {avg_confidence:.2f}")
            print(f"   Buy Ratio: {len(buy_recommendations) / len(results) * 100:.1f}%")

        return {
            'buy_list': buy_recommendations,
            'sell_list': sell_recommendations,
            'hold_list': hold_recommendations,
            'total_analyzed': len(results)
        }
    def calculate_macd(self, data):
        """Calculate MACD (Moving Average Convergence/Divergence)"""
        if len(data) < 35:
            return 0, 0
        
        try:
            ema_12 = data['close'].ewm(span=12).mean()
            ema_26 = data['close'].ewm(span=26).mean()

            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line

            # Current values
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_histogram = histogram.iloc[-1]
            previous_histogram = histogram.iloc[-2] if len(histogram) > 1 else 0

            if pd.isna(current_macd) or pd.isna(current_signal) or pd.isna(current_histogram):
                return 0, 0
            
            signal = 0
            confidence = 0

            # Generate signal values based on MACD behavior
            if current_macd > current_signal:
                if current_histogram > previous_histogram:
                    signal = 0.7
                    confidence = 0.6
                else:
                    signal = 0.3
                    confidence = 0.6
            elif current_macd < current_signal:
                if current_histogram < previous_histogram:
                    signal = -0.7
                    confidence = 0.8
                else:
                    signal = -0.3
                    confidence = 0.6

            # MACD crossover signals
            if (current_macd > current_signal and
                macd_line.iloc[-2] <= signal_line.iloc[-2]):
                signal = 0.9
                confidence = 0.9
            elif (current_macd < current_signal and
                  macd_line.iloc[-2] >= signal_line.iloc[-2]):
                signal = -0.9
                confidence = 0.9

            # Zero line crossover signals
            if (current_macd > 0 and macd_line.iloc[-2] <= 0):
                signal = min(0.8, signal + 0.2)
                confidence = min(1.0, confidence + 0.1)
            elif (current_macd < 0 and macd_line.iloc[-2] >= 0):
                signal = max(-0.8, signal - 0.2)
                confidence = min(1.0, confidence + 0.1)

            return signal, confidence
        
        except Exception as e:
            print(f"Error in MACD calculation: {e}")
            return 0, 0

    def calculate_bollinger_bands(self, data, period=20, std_dev=2):
        """Calculate Bollinger Bands trading signals"""

        if len(data) < period + 5:
            return 0, 0
        
        try:
            # Calculating bands
            sma = data['close'].rolling(window=period).mean()
            std = data['close'].rolling(window=period).std()
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)

            # Current values
            current_price = data['close'].iloc[-1]
            current_sma = sma.iloc[-1]
            current_upper = upper_band.iloc[-1]
            current_lower = lower_band.iloc[-1]

            # Previous values
            previous_price = data['close'].iloc[-2] if len(data) > 1 else current_price
            previous_upper = upper_band.iloc[-2] if len(upper_band) > 1 else current_upper
            previous_lower = lower_band.iloc[-2] if len(lower_band) > 1 else current_lower

            if pd.isna(current_sma) or pd.isna(current_upper) or pd.isna(current_lower):
                return 0, 0
        
            band_width = (current_upper - current_lower) / current_sma
            if current_upper != current_lower:
                band_position = (current_price - current_lower) / current_sma
            else:
                band_position = 0.5

            signal = 0
            confidence = 0

            # Band touching / breaching
            if current_price <= current_lower :
                if previous_price > previous_lower :
                    signal = 0.8
                    confidence = 0.9
                else:
                    signal = 0.6
                    confidence = 0.7
            elif current_price >= current_upper :
                if previous_price < previous_upper :
                    signal = -0.8
                    confidence = 0.9
                else:
                    signal = -0.6
                    confidence = 0.7
            # Mean reverse
            elif band_position < 0.2 :
                signal = 0.4
                confidence = 0.6
            elif band_position > 0.8 :
                signal = -0.4
                confidence = 0.6
            # Middle band crossover
            elif current_price > current_sma and previous_price <= current_sma:
                signal = 0.3
                confidence = 0.5
            elif current_price < current_sma and previous_price >= current_sma:
                signal = -0.3
                confidence = 0.5
            # Band squeeze
            if band_width < 0.1 :
                if current_price > previous_price:
                    signal += 0.2
                    confidence = min(1.0, confidence + 0.1)
                if current_price < previous_price:
                    signal -= 0.2
                    confidence = min(1.0, confidence + 0.1)

            volatility_adjustment = min(1.0, band_width * 5)
            if abs(signal) < 0.5 :
                confidence *= (1 - volatility_adjustment * 0.3)
            
            # Clamping signal and confidence to signal bounds
            signal = max( -1.0, min(1.0, signal))
            confidence = max(0.0, min(1.0, confidence))

            return signal, confidence
        
        except Exception as e:
            print(f"Error in Bollinger Bands calculation: {e}")
            return 0, 0

    def calculate_stochastic(self, data, k_period=14, d_period=3) :
        """Calculate Stochasitc Oscillator (%K and %D)"""
        if len(data) < k_period + d_period :
            return 0, 0
        try:
            # Calculate %K
            low_min = data['low'].rolling(window=k_period).min()
            high_max = data['high'].rolling(window=k_period).max()

            # Avoiding division by zero
            range_hl = high_max - low_min
            range_hl = range_hl.replace(0, 0.01)

            k_percent = ((data['close'] - low_min) / range_hl) * 100

            # Calculate %D
            d_percent = k_percent.rolling(window=d_period).mean()

            current_k = k_percent.iloc[-1]
            current_d = d_percent.iloc[-1]
            prev_k = k_percent.iloc[-2] if len(k_percent) > 1 else current_k
            prev_d = d_percent.iloc[-2] if len(d_percent) > 1 else current_d

            if pd.isna(current_k) or pd.isna(current_d):
                return 0, 0
            
            signal = 0
            confidence = 0

            if current_k < 20 and current_d < 20:
                if current_k > prev_k and current_d > prev_d:
                    signal = 0.9
                    confidence = 0.9
                elif current_k > current_d:
                    signal = 0.7
                    confidence = 0.8
                else:
                    signal = 0.5
                    confidence = 0.6
            
            elif current_k < 30 and current_d < 30:
                if current_k > prev_k and current_d > prev_d:
                    signal = 0.6
                    confidence = 0.7
                else:
                    signal = 0.3
                    confidence = 0.5
            
            elif current_k > 80 and current_d > 80:
                if current_k < prev_k and current_d < prev_d:
                    signal = -0.9
                    confidence = 0.9
                elif current_k < current_d:
                    signal = -0.7
                    confidence = 0.8
                else:
                    signal = -0.3
                    confidence = 0.5
            
            elif 30 <= current_k <= 70 and current_k > current_d and prev_k <= prev_d:
                signal = 0.4
                confidence = 0.6
            
            else:
                k_momentum = current_k - prev_k
                d_momentum = current_d - prev_d

                if k_momentum > 2 and d_momentum > 1:
                    signal = 0.2
                    confidence = 0.3
                elif k_momentum < -2 and d_momentum < -1:
                    signal = -0.2
                    confidence = 0.3
                else:
                    signal = 0
                    confidence = 0.1

            extremity_factor = 1.0
            if current_k < 10 or current_k > 90:
                extremity_factor = 1.2
            elif current_k < 20 or current_k > 80:
                extremity_factor = 1.1

            confidence = min(1.0, confidence * extremity_factor)
            return signal, confidence
        except Exception as e:
            print(f"Error calculating Stochastic Oscillator: {e}")
            return 0, 0
        
    def calculate_pe(self, overview): 
        """Calculate the Price to Earnings signal for a stock"""
        try:
            try:
                pe_ratio = float(overview.get('PERatio', 0))
            except (ValueError, TypeError):
                return 0, 0
            
            if pe_ratio > 0:
                pe_signal =  max(-0.9, min(0.9, (20 - pe_ratio) / 12.5))
            else:
                pe_signal = -0.9

            if pe_ratio < 0 or pe_ratio > 50:
                pe_confidence = 0.9
            elif pe_ratio < 10 or pe_ratio > 35:
                pe_confidence = 0.8
            elif pe_ratio < 12 or pe_ratio > 30:
                pe_confidence = 0.6
            else:
                pe_confidence = 0.4

            return pe_signal, pe_confidence
        
        except Exception as e:
            print(f"Error calculating Price to Earnings signal: {e}")
            return 0, 0
        
    def calculate_pb(self, overview):
        """Caluclate the Price to Book signal for a stock"""

        try:
            try:
                pb_ratio = float(overview.get('PriceToBookRatio', 0))
            except (ValueError, TypeError):
                return 0, 0
            
            if pb_ratio > 0:
                signal = max(-0.9, min(0.9, (2.4 - pb_ratio) / 2.0))
                confidence = min(0.9, abs(signal) + 0.3)
            else:
                signal = -0.9
                confidence = 0.9
            
            return signal, confidence
        
        except Exception as e:
            print(f"Error calculating Price to Book signal: {e}")

    def calculate_roe(self, overview):
        """Calculate the Return on Equity signal for a stock"""

        try:
            try:
                roe = float(overview.get('ReturnOnEquityTTM', 0))
            except (ValueError, TypeError):
                return 0, 0

            if roe > 0:
                signal = min(0.8, max(-0.2, (roe - 10) / 12.5))
                confidence = min(0.9, abs(signal) * 0.8 + 0.4)
            else:
                signal = -0.8
                confidence = 0.9

            return signal, confidence, roe

        except Exception as e:
            print(f"Error calculating Return on Equity signal: {e}")

    def calculate_current_ratio(self, balance_sheet):
        """Calculate the Current Liquidity Ratio for a company"""
        try:
            quarterly_report = balance_sheet.get('quarterlyReports', [])[0]
            if quarterly_report is None or len(quarterly_report) == 0:
                return 0, 0
            
            try:
                current_assets = float(quarterly_report.get('totalCurrentAssets', 0))
            except (ValueError, TypeError):
                current_assets = 0.0
            try:    
                current_liabilities = float(quarterly_report.get('totalCurrentLiabilities', 0))
            except (ValueError, TypeError):
                current_liabilities = 0.01
            
            if current_liabilities == 0:
                current_liabilities = 0.01 # Protecting against divide by zero issues

            current_ratio = current_assets / current_liabilities

            if current_ratio <= 2.0:
                signal = max(-0.7, (current_ratio - 0.5) / 1.5 * 0.6)
            else:
                signal = max(-0.1, 0.6 - (current_ratio - 2.0) * 0.2)

            confidence = min(0.8, abs(signal) * 0.8 + 0.3)

            return signal, confidence
        except Exception as e:
            print(f"Error calculating Current Ratio: {e}")
            return 0, 0
        
    def calculate_debt_to_equity(self, balance_sheet, roe):
        """Calculate the Debt to Equity Ratio for a company"""
        try:
            quarterly_report = balance_sheet.get('quarterlyReports', [])[0]
            if quarterly_report is None or len(quarterly_report) == 0:
                return 0, 0
            
            try:
                total_assets = float(quarterly_report.get('totalAssets', 0))
            except (ValueError, TypeError):
                total_assets = 0.0
            try:
                total_liabilities = float(quarterly_report.get('totalLiabilities', 0))
            except (ValueError, TypeError):
                total_liabilities = 0.0

            equity = total_assets - total_liabilities
            if equity == 0:
                equity = 0.01

            try:
                total_debt = float(quarterly_report.get('totalDebt', 0))
            except (ValueError, TypeError):
                total_debt = 0.0
            
            debt_to_equity = total_debt / equity

            if debt_to_equity <= 0.5:
                signal = min(0.6, debt_to_equity * 1.2)
            else:
                signal = max(-0.8, 0.6 - (debt_to_equity - 0.5) * 0.8)

            if roe > 15 and debt_to_equity < 1.0:
                signal = min(1.0, signal + 0.1)
            elif roe < 5 and debt_to_equity > 0.8:
                signal = max(-1.0, signal - 0.2)

            if debt_to_equity > 2.0 or debt_to_equity < 0.05:
                confidence = 0.9
            else:
                confidence = min(0.8, abs(signal) * 0.6 + 0.4)

            return signal, confidence
        except Exception as e:
            print(f"Error calculating Debt to Equity Ratio: {e}")
            return 0, 0
        
    def calculate_weighted_revenue_growth(self, quarters):
        """
        Calculate the year-over-year revenue growth with recent quarters
        weighted more heavily
        """
        yoy_rates = []
        weights = [0.4, 0.3, 0.2, 0.1]

        for i in range(4):
            try:
                current = quarters[i].get('totalRevnue', 0)
            except (ValueError, TypeError):
                current = 0.0
            try:
                previous_year = quarters[i + 4].get('totalRevnue', 0)
            except (ValueError, TypeError):
                previous_year = 0.0
            if previous_year == 0:
                previous_year = 0.01
            yoy_growth = (current - previous_year) / previous_year * 100
            yoy_rates.append(yoy_growth)

        weighted_growth = sum(rate * weight for rate, weight in zip(yoy_rates, weights))
        return weighted_growth
            
    def calculate_revenue_growth(self, income_statement):
        """Calculate the year-over-year revenue growth"""
        try:
            quarterly_reports = income_statement.get('quarterlyReports', [])
            if len(quarterly_reports) < 8:
                return 0, 0
            
            quarters = quarterly_reports[:8]
            growth = self.calculate_weighted_revenue_growth(quarters)

            if growth < -10:
                signal = -0.8
                confidence = 0.8
            elif growth < 0:
                signal = -0.3
                confidence = 0.6
            elif growth < 5:
                signal = 0.1
                confidence = 0.5
            elif growth < 15:
                signal = 0.5
                confidence = 0.7
            elif growth < 25:
                signal = 0.7
                confidence = 0.8
            else:
                signal = 0.8
                confidence = 0.7
            
            return signal, confidence
        except Exception as e:
            print(f"Error calculating Revenue Growth: {e}")
            return 0, 0

    def earnings_growth_calculator(self, current, previous):
        """Handle negative earnings gracefully"""

        if previous <= 0 and current > 0:
            return 100.0
        elif previous > 0 and current <= 0:
            return -100.0
        elif previous <= 0 and current <= 0:
            return 0.0
        else:
            if previous == 0:
                previous = 0.01
            return (current - previous) / previous * 100
        
    def calculate_earnings_growth(self, income_statement):
        """Calculate the year-over-year earnings growth"""
        try:
            quarterly_reports = income_statement.get('quarterlyReports', [])
            if len(quarterly_reports) < 8:
                return 0, 0

            quarters = quarterly_reports[:8]
            
            yoy_rates = []
            for i in range(4):
                try:
                    current = quarters[i].get('retainedEarnings', 0)
                except (ValueError, TypeError):
                    current = 0.0
                try:
                    previous = quarters[i + 4].get('retainedEarnings', 0)
                except (ValueError, TypeError):
                    previous = 0.0
                growth = self.earnings_growth_calculator(current, previous)
                yoy_rates.append(growth)
            
            filtered_rates = [rate for rate in yoy_rates if -200 < rate < 200]

            growth_rate = sum(filtered_rates) / len(filtered_rates) if filtered_rates else 0

            if growth_rate < -25:
                signal = -0.9
                confidence = 0.9
            elif growth_rate < -10:
                signal = -0.5
                confidence = 0.7
            elif growth_rate < 0:
                signal = -0.2
                confidence = 0.5
            elif growth_rate < 10:
                signal = 0.2
                confidence = 0.6
            elif growth_rate < 20:
                signal = 0.6
                confidence = 0.8
            elif growth_rate < 40:
                signal = 0.8
                confidence = 0.8
            else:
                signal = 0.7
                confidence = 0.6
            
            return signal, confidence
        except Exception as e:
            print(f"Error calculating Earnings Growth: {e}")
            return 0, 0