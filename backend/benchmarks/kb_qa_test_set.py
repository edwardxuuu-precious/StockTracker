"""
AI Benchmark Test Set - Knowledge Base Retrieval

Purpose: Evaluate KB's ability to recall relevant documents and rank them correctly.

Format:
- query: User's question
- relevant_docs: List of documents that should be retrieved (with relevance scores)
- irrelevant_docs: List of documents that should NOT be ranked highly
- quality_thresholds: Expected recall@k and ranking metrics
"""

KB_QA_TEST_SET = [
    # Category: Risk Management
    {
        "id": "KB-001",
        "category": "risk_management",
        "query": "如何降低回撤",
        "relevant_docs": [
            {
                "content": "To reduce drawdown, use stop-loss at 2% and position sizing at 5% per trade. Risk management is critical for portfolio protection.",
                "relevance": "high",
            },
            {
                "content": "Drawdown control methods: 1) Set maximum loss limits 2) Diversify positions 3) Use trailing stops 4) Reduce position size during volatile periods.",
                "relevance": "high",
            },
            {
                "content": "Portfolio risk metrics include maximum drawdown, value at risk (VaR), and Sharpe ratio.",
                "relevance": "medium",
            },
        ],
        "irrelevant_docs": [
            {
                "content": "Weather forecast for tomorrow is sunny with light clouds.",
                "relevance": "none",
            },
        ],
        "quality_thresholds": {
            "recall@3": 0.67,  # At least 2 out of 3 relevant docs in top-3
            "top1_relevance": ["high", "medium"],
        },
    },
    {
        "id": "KB-002",
        "category": "risk_management",
        "query": "stop loss设置多少合适",
        "relevant_docs": [
            {
                "content": "Stop-loss recommendations: Conservative 1-2%, Moderate 3-5%, Aggressive 5-8%. Never exceed 10% per trade.",
                "relevance": "high",
            },
            {
                "content": "Position sizing and stop-loss go hand-in-hand. A 2% stop with 10% position = 0.2% portfolio risk.",
                "relevance": "medium",
            },
        ],
        "irrelevant_docs": [
            {
                "content": "Market hours: US stock market opens at 9:30 AM EST.",
                "relevance": "none",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-003",
        "category": "risk_management",
        "query": "position sizing strategy",
        "relevant_docs": [
            {
                "content": "Kelly Criterion for position sizing: f = (bp - q) / b, where p=win rate, q=loss rate, b=win/loss ratio.",
                "relevance": "high",
            },
            {
                "content": "Fixed fractional position sizing: Allocate constant percentage (e.g., 2-5%) of portfolio per trade.",
                "relevance": "high",
            },
            {
                "content": "Volatility-based sizing: Larger positions in low-volatility assets, smaller in high-volatility.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 0.67,
            "top1_relevance": ["high"],
        },
    },
    # Category: Performance Metrics
    {
        "id": "KB-004",
        "category": "metrics",
        "query": "如何提高夏普比率",
        "relevant_docs": [
            {
                "content": "Sharpe ratio measures risk-adjusted returns. To improve: 1) Increase returns 2) Reduce volatility 3) Better entry timing 4) Stricter stop-loss 5) Portfolio diversification.",
                "relevance": "high",
            },
            {
                "content": "Sharpe ratio = (Return - Risk-free rate) / Standard deviation. Higher is better, >1 is good, >2 is excellent.",
                "relevance": "medium",
            },
        ],
        "irrelevant_docs": [
            {
                "content": "Recipe for chocolate cake: mix flour, sugar, cocoa powder.",
                "relevance": "none",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-005",
        "category": "metrics",
        "query": "win rate vs profit factor",
        "relevant_docs": [
            {
                "content": "Win rate = Winning trades / Total trades. Profit factor = Gross profit / Gross loss. A strategy with 40% win rate can be profitable if profit factor > 1.5.",
                "relevance": "high",
            },
            {
                "content": "Performance metrics: total return, max drawdown, win rate, Sharpe ratio, Sortino ratio, profit factor.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-006",
        "category": "metrics",
        "query": "maximum drawdown calculation",
        "relevant_docs": [
            {
                "content": "Maximum drawdown (MDD) = (Peak value - Trough value) / Peak value. Measures worst peak-to-trough decline.",
                "relevance": "high",
            },
            {
                "content": "Drawdown duration is also important. A 20% MDD that recovers in 1 month is better than 15% MDD over 12 months.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    # Category: Strategy Development
    {
        "id": "KB-007",
        "category": "strategy",
        "query": "均线策略优化方法",
        "relevant_docs": [
            {
                "content": "MA crossover optimization: 1) Test different window combinations 2) Add volume filter 3) Combine with RSI 4) Use adaptive windows 5) Add trend filter.",
                "relevance": "high",
            },
            {
                "content": "Common MA strategy pitfalls: 1) Whipsaws in ranging markets 2) Late entry in strong trends 3) Fixed parameters ignore market regime changes.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-008",
        "category": "strategy",
        "query": "momentum vs mean reversion",
        "relevant_docs": [
            {
                "content": "Momentum strategies: Buy strength, sell weakness. Work in trending markets. Mean reversion: Buy dips, sell rallies. Work in ranging markets.",
                "relevance": "high",
            },
            {
                "content": "Market regime detection is key. Use ADX for trend strength, Bollinger Band width for volatility regime.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-009",
        "category": "strategy",
        "query": "backtesting pitfalls",
        "relevant_docs": [
            {
                "content": "Common backtesting errors: 1) Look-ahead bias 2) Survivorship bias 3) Overfitting 4) Ignoring transaction costs 5) Data snooping.",
                "relevance": "high",
            },
            {
                "content": "Walk-forward analysis prevents overfitting. Split data into in-sample (optimization) and out-of-sample (validation).",
                "relevance": "high",
            },
            {
                "content": "Realistic transaction costs: Slippage 0.05-0.1%, Commission 0.1% per trade for stocks.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 0.67,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-010",
        "category": "strategy",
        "query": "parameter optimization techniques",
        "relevant_docs": [
            {
                "content": "Optimization methods: Grid search (exhaustive), Random search (faster), Bayesian optimization (efficient), Genetic algorithms (global).",
                "relevance": "high",
            },
            {
                "content": "Anti-overfitting: 1) Use validation set 2) Limit parameter count 3) Regularization 4) Cross-validation 5) Walk-forward testing.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    # Category: Market Microstructure
    {
        "id": "KB-011",
        "category": "market",
        "query": "bid-ask spread impact",
        "relevant_docs": [
            {
                "content": "Bid-ask spread represents transaction cost. Wider spreads = higher cost. Impacts short-term strategies more than long-term.",
                "relevance": "high",
            },
            {
                "content": "Spread varies by: Liquidity (volume), volatility, market hours. Typically 0.01-0.05% for large-cap stocks.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-012",
        "category": "market",
        "query": "market impact cost",
        "relevant_docs": [
            {
                "content": "Market impact = Price movement caused by your order. Larger orders have higher impact. Use VWAP/TWAP to minimize.",
                "relevance": "high",
            },
            {
                "content": "Impact cost models: Square-root model (common), Linear model (simple). Impact ∝ sqrt(Order size / Daily volume).",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    # Category: Chinese Market Specific
    {
        "id": "KB-013",
        "category": "cn_market",
        "query": "A股T+1限制",
        "relevant_docs": [
            {
                "content": "A股实行T+1交易制度，当天买入的股票次日才能卖出。策略需考虑隔夜风险，不能做日内回转。",
                "relevance": "high",
            },
            {
                "content": "T+1限制下的策略调整：1) 延长持仓周期 2) 加强止损管理 3) 避免追涨杀跌 4) 关注盘后新闻风险。",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-014",
        "category": "cn_market",
        "query": "涨跌停板影响",
        "relevant_docs": [
            {
                "content": "A股涨跌停板限制：主板±10%，科创板/创业板±20%。涨停买不进，跌停卖不出，影响策略执行。",
                "relevance": "high",
            },
            {
                "content": "连续涨停股票流动性极差，回测应考虑无法买入的情况。跌停板需设置强制止损。",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    # Category: Technical Indicators
    {
        "id": "KB-015",
        "category": "indicators",
        "query": "RSI indicator interpretation",
        "relevant_docs": [
            {
                "content": "RSI (Relative Strength Index): >70 overbought, <30 oversold. Range 0-100. 14-day period is standard.",
                "relevance": "high",
            },
            {
                "content": "RSI divergence signals: Price makes new high but RSI doesn't = bearish. Price new low but RSI doesn't = bullish.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-016",
        "category": "indicators",
        "query": "Bollinger Bands strategy",
        "relevant_docs": [
            {
                "content": "Bollinger Bands: Middle = 20-day SMA, Upper/Lower = ±2 std dev. Price at upper band = overbought, at lower = oversold.",
                "relevance": "high",
            },
            {
                "content": "BB strategies: 1) Mean reversion (buy lower band, sell upper) 2) Breakout (buy above upper band in trend) 3) Squeeze (low volatility before big move).",
                "relevance": "high",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-017",
        "category": "indicators",
        "query": "MACD信号线交叉",
        "relevant_docs": [
            {
                "content": "MACD = 12EMA - 26EMA, Signal line = 9EMA of MACD. Golden cross (MACD上穿signal) = bullish, Death cross (MACD下穿signal) = bearish.",
                "relevance": "high",
            },
            {
                "content": "MACD histogram = MACD - Signal line. Histogram expanding = trend strengthening, contracting = trend weakening.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    # Category: Portfolio Management
    {
        "id": "KB-018",
        "category": "portfolio",
        "query": "diversification benefits",
        "relevant_docs": [
            {
                "content": "Diversification reduces unsystematic risk. Correlation matters: Negative correlation best, low positive correlation good, high positive correlation limited benefit.",
                "relevance": "high",
            },
            {
                "content": "Over-diversification (diworsification): >20-30 stocks dilutes returns without significant risk reduction. Focus on uncorrelated assets.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-019",
        "category": "portfolio",
        "query": "rebalancing frequency",
        "relevant_docs": [
            {
                "content": "Rebalancing frequencies: Monthly (active), Quarterly (balanced), Annually (passive). More frequent = higher costs but better risk control.",
                "relevance": "high",
            },
            {
                "content": "Threshold-based rebalancing: Rebalance when allocation drifts >5% from target. Combines time and deviation triggers.",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
    {
        "id": "KB-020",
        "category": "portfolio",
        "query": "correlation vs covariance",
        "relevant_docs": [
            {
                "content": "Correlation: Standardized measure (-1 to +1) of linear relationship. Covariance: Unstandardized measure. Correlation = Covariance / (σ1 × σ2).",
                "relevance": "high",
            },
            {
                "content": "For portfolio optimization, correlation is easier to interpret but covariance is used in calculations (Markowitz model).",
                "relevance": "medium",
            },
        ],
        "quality_thresholds": {
            "recall@3": 1.0,
            "top1_relevance": ["high"],
        },
    },
]

# Additional 30 test cases (condensed for brevity)
ADDITIONAL_KB_CASES = [
    {"id": "KB-021", "query": "volatility clustering", "category": "market_behavior"},
    {"id": "KB-022", "query": "fat tails in returns", "category": "statistics"},
    {"id": "KB-023", "query": "regime change detection", "category": "market_behavior"},
    {"id": "KB-024", "query": "earnings announcement impact", "category": "events"},
    {"id": "KB-025", "query": "seasonal patterns", "category": "market_behavior"},
    {"id": "KB-026", "query": "liquidity crisis", "category": "risk"},
    {"id": "KB-027", "query": "flash crash", "category": "risk"},
    {"id": "KB-028", "query": "circuit breaker", "category": "cn_market"},
    {"id": "KB-029", "query": "margin requirements", "category": "trading"},
    {"id": "KB-030", "query": "short selling restrictions", "category": "cn_market"},
    {"id": "KB-031", "query": "order types limit vs market", "category": "trading"},
    {"id": "KB-032", "query": "slippage estimation", "category": "costs"},
    {"id": "KB-033", "query": "commission structure", "category": "costs"},
    {"id": "KB-034", "query": "tax implications", "category": "costs"},
    {"id": "KB-035", "query": "benchmark selection", "category": "performance"},
    {"id": "KB-036", "query": "alpha vs beta", "category": "performance"},
    {"id": "KB-037", "query": "tracking error", "category": "performance"},
    {"id": "KB-038", "query": "information ratio", "category": "metrics"},
    {"id": "KB-039", "query": "Sortino ratio", "category": "metrics"},
    {"id": "KB-040", "query": "Calmar ratio", "category": "metrics"},
    {"id": "KB-041", "query": "momentum indicators", "category": "indicators"},
    {"id": "KB-042", "query": "volume analysis", "category": "indicators"},
    {"id": "KB-043", "query": "candlestick patterns", "category": "technical"},
    {"id": "KB-044", "query": "support and resistance", "category": "technical"},
    {"id": "KB-045", "query": "trend lines", "category": "technical"},
    {"id": "KB-046", "query": "breakout trading", "category": "strategy"},
    {"id": "KB-047", "query": "pairs trading", "category": "strategy"},
    {"id": "KB-048", "query": "statistical arbitrage", "category": "strategy"},
    {"id": "KB-049", "query": "market making", "category": "strategy"},
    {"id": "KB-050", "query": "high frequency trading", "category": "strategy"},
]

# Total: 20 detailed + 30 condensed = 50 test cases
