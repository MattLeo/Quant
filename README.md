# Multi-Layer Algorithmic Trading System

A quantitative trading platform that combines technical analysis, fundamental analysis, and sentiment analysis through a layered architecture for robust stock market decision-making.

## Overview

This system implements a multi-factor approach to algorithmic trading, using distinct analytical layers that can adapt to different market conditions. Unlike single-strategy systems, this layered approach provides:

- **Dynamic Signal Weighting**: Adjusts strategy based on market volatility
- **Risk Management**: Multiple exit triggers and position sizing controls  
- **Scalability**: Add new analytical layers without rebuilding core infrastructure
- **Market Adaptability**: Performs across different market regimes

### Core Components

- **Backend API**: Flask-based trading engine with database persistence
- **Frontend Dashboard**: React-based portfolio monitoring and control interface
- **Analysis Framework**: Multi-layer signal processing and recommendation engine
- **Execution Engine**: Alpaca Markets integration for trade execution

### Prerequisites

- Python 3.8+
- Node.js 14+
- Alpaca Markets account (for live/paper trading)
- Git

## Implementation Architecture

### Phase 1: Foundation ✅ **(Completed)**

Basic signal processing and infrastructure:

```python
basic_layers = {
    'universe': 'all non-penny-stock NASDAQ and NYSE equities',
    'signals': ['SMA crossover', 'RSI', 'Volume'],
    'timeframe': '6 months daily data',
    'risk': 'Simple stop losses'
}
```

### Phase 2: Enhancement ✅ **(Completed)**

Enhanced technical analysis with multiple indicators:

```python
enhanced_layers = {
    'universe': 'Sector-balanced screening',
    'signals': ['MACD', 'Bollinger Bands', 'Momentum'],
    'timeframe': '1 year + intraday for entries',
    'risk': 'Position sizing, correlation limits'
}

technical_signal_weights = {
    'sma_crossover': 0.22,
    'rsi_signal': 0.18,
    'macd_signal': 0.18,
    'bollinger_signal': 0.14,
    'stochastic_signal': 0.15,
    'volume_signal': 0.13
}
```

### Phase 3: Advanced 🚧 **(In Progress)**

Multi-factor approach with fundamental analysis:

```python
advanced_layers = {
    'universe': 'Dynamic screening with fundamental filters',
    'signals': ['Technical', 'Fundamental', 'Sentiment'],
    'timeframe': '2+ years multi-timeframe',
    'risk': 'Portfolio-level risk management'
}

fundamental_weights = {
    'pe_ratio': 0.20,
    'rev_growth': 0.15,
    'earnings_growth': 0.18,
    'roe_signal': 0.15,
    'debt_to_equity;': 0.12,
    'pb_ratio': 0.12,
    'current_ratio': 0.08 
}
```

## Data Requirements

### Technical Layer
- **Minimum**: 6 months daily OHLCV data
- **Optimal**: 2+ years daily + 3 months intraday
- **Sources**: Real-time price feeds, volume data

### Fundamental Layer
- **Financial Statements**: 2+ years quarterly earnings
- **Ratios**: P/E, P/B, ROE, debt-to-equity, current ratio
- **Growth Metrics**: Revenue and earnings growth rates

### Sentiment Layer
- **Analyst Ratings**: Real-time + 1 year historical
- **Options Flow**: Current day + 30-day history  
- **News Sentiment**: Real-time news feeds

### Risk Management Layer
- **Correlations**: 1+ year daily returns for correlation analysis
- **Volatility**: 6+ months for volatility calculations
- **Market Regime**: 2+ years for regime detection

## Development Roadmap

### Sprint 1: Core Framework ✅
- [x] Basic signal calculation infrastructure
- [x] Simple signal aggregation logic
- [x] Testing framework with sample stocks
- [x] React frontend dashboard implementation

### Sprint 2: Signal Enhancement ✅
- [x] Automated deployment pipeline
- [x] Confidence scoring system
- [x] MACD signal implementation
- [x] Bollinger Bands analysis
- [x] Stochastic Oscillator signals
- [x] Multi-signal recommendation engine
- [x] Market hours trade execution handling
- [x] Previous recommendation caching

### Sprint 3: Risk Management & Fundamental Layer 🚧
- [x] Position sizing logic improvements
- [x] Stop-loss implementation
- [ ] Risk Management configuration
- [ ] Portfolio-level risk constraints
- [ ] Fundamental analysis layer:
  - [x] P/E Ratio analysis
  - [x] P/B Ratio evaluation
  - [ ] Debt-to-Equity ratio assessment
  - [x] Current ratio liquidity analysis
  - [ ] Revenue growth tracking
  - [ ] Earnings growth analysis
  - [x] ROE measurements
- [ ] Combined Technical + Fundamental weighting
- [ ] Market regime detection and switching
- [ ] Growth capture timing optimization
- [ ] User configuration interface
- [ ] Update workflow for deployed instances

### Sprint 4: Optimization & UI Improvements 
- [ ] Enhanced portfolio detail screens
- [ ] Performance visualization over time
- [ ] Individual position charting (SMA, Bollinger, Volume, RSI)
- [ ] Automated analysis scheduling
- [ ] Proton-based UI implementation
- [ ] Google Drive database synchronization
- [ ] Signal parameter optimization via backtesting
- [ ] Advanced performance tracking per position

### Sprint 5: Sentiment Layer Development
- [ ] Implement limited news feed scraping
- [ ] Decipher sentiment from scraped news feeds
- [ ] Implement insider trading scraper from SEC filings
- [ ] Build a signal generator from the scraped feeds
- [ ] Incorporate sentiment signal into recommendations
- [ ] Backtest with previous versions and market regimes to quantify improvement
- [ ] Expand out corpus of news feeds to maximize signal accuracy

### Future: Advanced Features 
- [ ] Machine learning signal generation
- [ ] Alternative data integration (satellite, social media)
- [ ] Real-time execution system
- [ ] Options trading strategies
- [ ] Cryptocurrency support

## System Design

### Signal Weighting Strategy

The system dynamically adjusts signal weights based on market conditions:

```python
def adjust_weights_by_market_regime(current_signals, market_vol):
    """Adjust signal weights based on market volatility regime"""
    if market_vol > 30:  # High volatility regime
        return {
            'technical': 0.5,    # Favor technical signals
            'fundamental': 0.3,  # Reduce fundamental weight
            'sentiment': 0.2
        }
    else:  # Low volatility regime
        return {
            'technical': 0.3,
            'fundamental': 0.5,  # Favor fundamental analysis
            'sentiment': 0.2
        }
```

### Entry/Exit Logic
- **Entry Signals**: Require agreement from 2+ analytical layers
- **Exit Signals**: Any layer can trigger (risk management priority)
- **Position Sizing**: Based on signal conviction + risk assessment

## Expected Performance

| Metric | Single Strategy | Layered Approach |
|--------|----------------|------------------|
| **Win Rate** | ~60% | 70%+ |
| **Volatility** | High | Smoother returns |
| **Robustness** | Market dependent | Multi-regime adaptability |
| **Drawdown Control** | Limited | Multiple exit triggers |
| **Scalability** | Requires rebuilding | Incremental layer addition |

### Key Advantages
- **Cross-Market Robustness**: Adapts to different market conditions
- **Enhanced Risk Control**: Multiple exit triggers and portfolio constraints
- **Modular Architecture**: Add new strategies without system redesign
- **Dynamic Adaptability**: Real-time weight adjustment based on market regime

## API Endpoints

The system exposes a RESTful API for frontend integration:

- `GET /api/portfolio` - Portfolio summary and metrics
- `GET /api/positions` - Current active positions
- `GET /api/trades` - Historical trade data
- `GET /api/analysis/results` - Latest analysis recommendations
- `POST /api/analysis/run` - Trigger new analysis execution
- `POST /api/trades/execute` - Execute recommended trades

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer ⚠️

This software is for educational and research purposes only. Past performance does not guarantee future results. Always consult with a financial advisor before making investment decisions. Use at your own risk.