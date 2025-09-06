# CSFloat Auto-Flipper v2.0

An advanced, fully automated trading bot for CSFloat with AI-powered price predictions, microsecond sniping capabilities, and dynamic strategy optimization.

## 🚀 Features

### Core Features
- **Ultra-Fast WebSocket Connection**: Multiple parallel connections with microsecond latency
- **AI-Powered Price Prediction**: Ensemble ML models (DNN, LSTM, Random Forest, Gradient Boosting)
- **Microsecond Sniping Engine**: Multi-threaded execution with instant order placement
- **Dynamic Strategy Management**: 6+ advanced trading strategies with auto-optimization
- **Real-Time Market Analysis**: Pattern recognition, float analysis, cross-market arbitrage
- **Portfolio Management**: Automated position management with stop-loss/take-profit
- **Comprehensive Monitoring**: Real-time dashboard with Prometheus metrics

### Advanced Strategies
1. **Pattern Arbitrage**: Targets rare patterns (Dragon Lore, Blue Gem, etc.)
2. **Float Capping**: Exploits float value boundaries for premium pricing
3. **Sticker Hunter**: Identifies undervalued stickered items
4. **Market Maker**: Creates liquidity with strategic spread management
5. **Cross-Market Arbitrage**: Exploits price differences across platforms
6. **AI Momentum Trading**: ML-driven trend following

## 📋 Requirements

- Python 3.8+
- MongoDB 4.0+
- Redis 6.0+
- 8GB+ RAM recommended
- Low-latency internet connection

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/csfloat-flipper.git
cd csfloat-flipper
```

2. Run the setup script:
```bash
python setup.py
```

3. Configure your API key:
```bash
# Edit .env file
CSFLOAT_API_KEY=your_api_key_here
```

4. Start required services:
```bash
# Start MongoDB
mongod --dbpath /path/to/data

# Start Redis
redis-server
```

## 🚀 Usage

### Basic Usage
```bash
# Run the auto-flipper
python main.py

# Dry run mode (no real trades)
python main.py --dry-run
```

### Configuration

Edit `config.py` to customize:
- Budget limits
- Profit margins
- Strategy parameters
- Performance settings

### Monitoring

Access the monitoring dashboard:
- Web Dashboard: http://localhost:9090/dashboard
- Prometheus Metrics: http://localhost:9090/metrics

## 📊 Performance Optimization

The bot includes several optimization features:

1. **Parallel Processing**: Multi-threaded sniping with 32+ concurrent threads
2. **JIT Compilation**: Numba-optimized critical paths
3. **Connection Pooling**: Reusable HTTP/WebSocket connections
4. **Predictive Caching**: ML-based prefetching
5. **Memory Optimization**: Automatic garbage collection and cache management

## 🔒 Security Features

- Stealth mode with user agent rotation
- Request throttling with variance
- Distributed execution patterns
- Anti-pattern detection avoidance

## 📈 Strategy Configuration

Each strategy can be configured in `config.py`:

```python
'pattern_arbitrage': {
    'enabled': True,
    'min_pattern_index': 0,
    'max_pattern_index': 999,
    'profit_multiplier': 1.5
}
```

## 🔧 Advanced Features

### Custom ML Models
The AI predictor supports custom model training:
```python
# Models automatically retrain every hour with new market data
# Custom features can be added in ai_predictor.py
```

### WebSocket Optimization
- 10+ parallel connections
- Automatic failover
- Message deduplication
- Priority queuing

### Risk Management
- Kelly Criterion position sizing
- Dynamic stop-loss/take-profit
- Maximum drawdown protection
- Daily loss limits

## 📝 Logging

Logs are stored in the `logs/` directory:
- `flipper_YYYYMMDD.log`: General logs
- `trades_YYYYMMDD.log`: Trade execution logs
- `errors_YYYYMMDD.log`: Error logs

## ⚠️ Disclaimer

This bot is for educational purposes. Trading involves risk, and you should:
- Never invest more than you can afford to lose
- Test thoroughly in dry-run mode first
- Monitor the bot regularly
- Understand the strategies being used

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues or questions:
1. Check the logs for errors
2. Ensure all services are running
3. Verify API key is valid
4. Create an issue on GitHub

---

**Note**: This bot uses advanced algorithms and high-frequency trading techniques. Use responsibly and in accordance with CSFloat's terms of service.