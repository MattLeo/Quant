import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
import time
import os
import logging

logger = logging.getLogger("console_log")

class TradingAnalysis:
    """Trading analysis of stocks to track performance"""

    def __init__(self, api_key, secret_key):
        self.api = tradeapi.REST(
            key_id=api_key,
            secret_key=secret_key,
            base_url='https://paper-api.alpaca.markets'
        )

        # Initial signal weights
        self.signal_weights = {
            'sma_crossover': 0.25,
            'rsi_signal': 0.2,
            'volume_signal': 0.15,
            'macd_signal': 0.2,
            'bollinger_signal': 0.15,
            #TODO add momentum signal
        }

        # Buy/Sell Thresholds
        self.buy_threshold = 0.3
        self.sell_threshold = -0.3

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
        
        # Calculating all signals
        sma_signal, sma_confidence = self.calculate_sma(data)
        rsi_signal, rsi_confidence = self.calculate_rsi(data)
        vol_signal, vol_confidence = self.calculate_volume(data)
        macd_signal, macd_confidence = self.calculate_macd(data)
        bollinger_signal, bollinger_confidence = self.calculate_bollinger_bands(data)

        risk_metrics = self.calculate_risk_metrics(data)

        total_signal = (
            sma_signal * sma_confidence * self.signal_weights['sma_crossover'] +
            rsi_signal * rsi_confidence * self.signal_weights['rsi_signal'] +
            vol_signal * vol_confidence * self.signal_weights['volume_signal'] +
            macd_signal * macd_confidence * self.signal_weights['macd_signal'] +
            bollinger_signal * bollinger_confidence * self.signal_weights['bollinger_signal']
        )

        total_confidence = (
            sma_confidence * self.signal_weights['sma_crossover'] +
            rsi_confidence * self.signal_weights['rsi_signal'] +
            vol_confidence * self.signal_weights['volume_signal'] +
            macd_confidence * self.signal_weights['macd_signal'] +
            bollinger_confidence * self.signal_weights['bollinger_signal']
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
                'volume': {'value': vol_signal, 'confidence': vol_confidence}
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
            current_std = std.iloc[-1]

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
            
                


        


    