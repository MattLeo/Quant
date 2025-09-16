import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
import warnings

warnings.filterwarnings('ignore')

class MarketRegimeDetector:
    """
    Market regime detection using the following factors:
    - VIX levels
    - Market breadth indicators
    - Sector rotation patterns
    - Term structure dynamics
    """

    def __init__(self):
        self.regime_thresholds = {
            'vix': {'low': 15, 'moderate': 25, 'high': 35},
            'market_breadth': {'weak': 0.4, 'neutral': 0.6, 'strong': 0.8},
            'term_structure': {'weak': 0.3, 'neutral': 0.6, 'strong': 0.8}
        }

        self.current_regime = None
        self.regime_confidence = 0.8
        self.regime_history = []

    def get_vix_data(self, lookback_days=60):
        """Fetch VIX data"""
        try:
            vix = yf.download('^VIX', period=f'{lookback_days}d', progress=False)
            if len(vix) == 0:
                return None
            return vix
        except Exception as e:
            print(f"Error fetching VIX data: {e}")
            return None
        
    def get_market_breadth_data(self):
        """Calculate market breadth using major market indices"""
        symbols = ['^GSPC', '^DJI', '^IXIC', '^RUT']
        try:
            data = {}
            for symbol in symbols:
                ticker_data = yf.download(symbol, period='60d', progress=False)
                if len(ticker_data) > 0:
                    ticker_data['sma_20'] = ticker_data['Close'].rolling(20).mean()
                    ticker_data['above_sma'] = ticker_data['Close'] > ticker_data['sma_20']
                    data[symbol] = ticker_data
            return data
        except Exception as e:
            print(f"Error fetching market breadth data: {e}")
            return None
    
    def get_sector_rotation_data(self):
        """Analyze sector ETFs performance for rotation patterns"""
        sector_etfs = [
            'XLE', # Energy
            'XLB', # Materials
            'XLI', # Industrial
            'XLF', # Financials
            'XLV', # Healthcare
            'XLY', # Consumer Discretionary
            'XLP', # Consumer Staples
            'XLU', # Utilities
            'XLC', # Communication Services
            'XLRE' # Real Estate
        ]

        try:
            sector_performance = ()
            for etf in sector_etfs:
                data = yf.download(etf, period='30d', progress=False)
                if len(data) > 0:
                    returns = (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1)
                    sector_performance[etf] = returns
            return sector_performance
        except Exception as e:
            print(f"Error fetching sector rotation data: {e}")
            return None

    def calculate_vix_regime(self, vix_data):
        """Determine volatility regime from VIX"""
        if vix_data is None or len(vix_data) == 0:
            return 'moderate', 0.5
        
        current_vix = vix_data['Close'].iloc[-1]
        vix_ma_10 = vix_data['Close'].rolling(10).mean().iloc[-1]
        vix_momentum = (current_vix - vix_ma_10) / vix_ma_10

        if current_vix < self.regime_thresholds['vix']['low']:
            vix_regime = 'low_vol'
            confidence = 0.9 if vix_momentum <= 0 else 0.7
        elif current_vix > self.regime_thresholds['vix']['high']:
            vix_regime = 'high_vol'
            confidence = 0.9 if vix_momentum >= 0 else 0.7
        elif current_vix > self.regime_thresholds['vix']['moderate']:
            vix_regime = 'elevated_vol'
            confidence = 0.8
        else:
            vix_regime = 'moderate_vol'
            confidence = 0.6
        return vix_regime, confidence, current_vix, vix_momentum
    
    def calculate_market_breadth_regime(self, breadth_data):
        """Assess marekt breadth and trend strength"""
        if not breadth_data:
            return 'neutral', 0.5, {}
        
        breadth_metrics = {}
        above_sma_counts = 0
        total_indices = len(breadth_data)

        for symbol, data in breadth_data.items():
            if len(data) > 0 and 'above_sma' in data.columns:
                above_sma = data['above_sma'].iloc[-1]
                if above_sma:
                    above_sma_counts += 1

                current_price = data['Close'].iloc[-1]
                price_20d_ago = data['Close'].iloc[-20] if len(data) >= 20 else data['Close'].iloc[0]
                momentum = (current_price - price_20d_ago) / price_20d_ago
                breadth_metrics[symbol] = {
                    'above_sma': above_sma,
                    'momentum': momentum
                }

        breadth_ratio = above_sma_counts / total_indices if total_indices > 0 else 0.5

        if breadth_ratio >= self.regime_thresholds['market_breadth']['strong']:
            market_breadth = 'strong_breadth'
            confidence = 0.8
        elif breadth_ratio >= self.regime_thresholds['market_breadth']['neutral']:
            market_breadth = 'neutral_breadth'
            confidence = 0.6
        else:
            market_breadth = 'weak_breadth'
            confidence = 0.8

        return market_breadth, confidence, breadth_metrics
    
    def calculate_sector_regime(self, sector_data):
        """Analyze sector rotation patterns"""
        if not sector_data:
            return 'balanced', 0.5, {}
        
        returns = list(sector_data.values())
        if len(returns) == 0:
            return 'balanced', 0.5, {}
        
        return_std = np.std(returns)
        return_range = max(returns) - min(returns)
        sorted_sectors = sorted(sector_data.items(), key=lambda x: x[1], reverse=True)
        leaders = dict(sorted_sectors[:3])
        laggards = dict(sorted_sectors[-3:])

        if return_range > 0.15:
            if max(returns) > 0.05:
                sector_regime = 'risk_on_rotation'
                confidence = 0.8
            else:
                sector_regime = 'risk_off_rotation'
                confidence = 0.8
        else:
            sector_regime = 'balanced'
            confidence = 0.6

        return sector_regime, confidence, {
            'leaders': leaders,
            'laggards': laggards,
            'dispersion': return_std,
            'range': return_range
        }
    
    def determine_overall_regime(self):
        """Combine all factors to determine overall market regime"""
        print("Determining market regime...")

        vix_data = self.get_vix_data()
        breadth_data = self.get_market_breadth_data()
        sector_data = self.get_sector_rotation_data()

        vix_regime, vix_conf, current_vix, vix_mom = self.calculate_vix_regime(vix_data)
        breadth_regime, breadth_conf, breadth_metrics = self.calculate_market_breadth_regime(breadth_data)
        sector_regime, sector_conf, sector_metrics = self.calculate_sector_regime(sector_data)

        regime_weights = {
            'vix': 0.4,
            'breadth': 0.35,
            'sector': 0.25
        }

        overall_confidence = (
            vix_conf * regime_weights['vix'] +
            breadth_conf * regime_weights['breadth'] +
            sector_conf * regime_weights['sector']
        )

        if vix_regime == 'high_vol' or (vix_regime == 'elevated_vol' and breadth_regime == 'weak_breadth'):
            overall_regime = 'high_volitility'
            strategy_weights = {
                'technical': 0.71,
                'fundamental': 0.29
            }
            # technical = 0.6, fundamental = 0.25, sentiment = 0.15
        elif vix_regime == 'low_vol' and breadth_regime in ['strong_breadth', 'neutral_breadth']:
            overall_regime = 'low_volitility'
            strategy_weights = {
                'technical': 0.29,
                'fundamental': 0.71
            }
            # technical = 0.25, fundamental = 0.6, sentiment = 0.15
        elif breadth_regime == 'strong_breadth' and sector_regime == 'risk_on_rotation':
            overall_regime = 'trending_bullish'
            strategy_weights = {
                'technical':  0.625,
                'fundamental': 0.375
            }
            # technical = 0.5, fundamental = 0.3, sentiment = 0.2
        elif breadth_regime == 'weak_breadth' and sector_regime == 'risk_off_rotation':
            overall_regime = 'trending_bearish'
            strategy_weights = {
                'technical': 0.75,
                'fundamental': 0.25
            }
            # techincal = 0.6, fundamental = 0.2, sentiment = 0.2
        else:
            overall_regime = 'transitional'
            strategy_weights = {
                'technical': 0.5,
                'fundamental': 0.5
            }
            # technical 0.4, fundamental = 0.4, sentiment = 0.2

        self.current_regime = overall_regime
        self.regime_confidence = overall_confidence

        regime_analysis = {
            'overall_regime': overall_regime,
            'confidence': overall_confidence,
            'strategy_weights': strategy_weights,
            'components': {
                'vix': {
                    'regime': vix_regime,
                    'confidence': vix_conf,
                    'current_vix': current_vix,
                    'momentum': vix_mom
                },
                'breadth': {
                    'regime': breadth_regime,
                    'confidence': breadth_conf,
                    'metrics': breadth_metrics
                },
                'sector': {
                    'regime': sector_regime,
                    'confidence': sector_conf,
                    'metrics': sector_metrics
                }
            },
            'timestamp': datetime.now()
        }

        self.regime_history.append(regime_analysis)
        
        return regime_analysis
    
    def print_regime_analysis(self, analysis):
        """Print comprehensive regime analysis"""
        print(f"\n📊 MARKET REGIME ANALYSIS")
        print(f"{'='*50}")
        
        print(f"\n🎯 OVERALL REGIME: {analysis['overall_regime'].upper()}")
        print(f"   Confidence: {analysis['confidence']:.1%}")
        
        print(f"\n📈 RECOMMENDED STRATEGY WEIGHTS:")
        for strategy, weight in analysis['strategy_weights'].items():
            print(f"   {strategy.capitalize()}: {weight:.1%}")
        
        print(f"\n🔍 COMPONENT ANALYSIS:")
        
        # VIX Analysis
        vix = analysis['components']['vix']
        print(f"   VIX Regime: {vix['regime']} (Confidence: {vix['confidence']:.1%})")
        print(f"   Current VIX: {vix['current_value']:.1f} | Momentum: {vix['momentum']:.1%}")
        
        # Breadth Analysis  
        breadth = analysis['components']['breadth']
        print(f"   Breadth Regime: {breadth['regime']} (Confidence: {breadth['confidence']:.1%})")
        
        # Sector Analysis
        sector = analysis['components']['sector']
        print(f"   Sector Regime: {sector['regime']} (Confidence: {sector['confidence']:.1%})")
        
        if 'leaders' in sector['metrics']:
            print(f"   Leading Sectors: {', '.join([k.replace('XL', '') for k in sector['metrics']['leaders'].keys()])}")
        
        print(f"\n⏰ Analysis Time: {analysis['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

