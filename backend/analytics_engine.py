"""
Advanced Analytics Engine for Valor IVX Platform
Phase 9: Advanced Analytics and Machine Learning

This module provides comprehensive analytics capabilities including:
- Real-time market analysis
- Sentiment analysis
- Risk modeling
- Performance analytics
- Predictive analytics
- Business intelligence
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import yfinance as yf
import requests
from textblob import TextBlob
import redis
from collections import defaultdict, deque

from .ml_models.registry import ModelRegistry
from .ml_models.sentiment_analyzer import SentimentAnalyzer
from .ml_models.risk_assessor import RiskAssessor
from .ml_models.portfolio_optimizer import PortfolioOptimizer
from .ml_models.revenue_predictor import RevenuePredictor
from .cache import cache_manager
from .settings import settings

logger = logging.getLogger(__name__)


@dataclass
class MarketSignal:
    """Market signal data structure"""
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold', 'alert'
    confidence: float
    strength: float
    timestamp: datetime
    indicators: Dict[str, Any]
    description: str


@dataclass
class RiskMetrics:
    """Risk metrics data structure"""
    var_95: float  # Value at Risk 95%
    var_99: float  # Value at Risk 99%
    expected_shortfall: float
    volatility: float
    beta: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    correlation_matrix: np.ndarray
    stress_test_results: Dict[str, float]


@dataclass
class SentimentAnalysis:
    """Sentiment analysis results"""
    overall_sentiment: float  # -1 to 1
    sentiment_score: float
    confidence: float
    sources: List[str]
    keywords: List[str]
    timestamp: datetime
    breakdown: Dict[str, float]


class AdvancedAnalyticsEngine:
    """Advanced analytics engine for real-time financial analysis"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.model_registry = ModelRegistry()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.risk_assessor = RiskAssessor()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.revenue_predictor = RevenuePredictor()
        
        # Initialize caches
        self.market_data_cache = {}
        self.sentiment_cache = {}
        self.risk_cache = {}
        
        # Real-time data streams
        self.market_streams = {}
        self.alert_streams = {}
        
        # Performance tracking
        self.performance_metrics = defaultdict(list)
        self.analytics_history = deque(maxlen=1000)
        
        logger.info("Advanced Analytics Engine initialized")
    
    async def analyze_market_sentiment(self, symbol: str, timeframe: str = "1d") -> SentimentAnalysis:
        """Analyze market sentiment for a given symbol"""
        cache_key = f"sentiment:{symbol}:{timeframe}"
        
        # Check cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            return SentimentAnalysis(**cached_result)
        
        try:
            # Get news and social media data
            news_data = await self._fetch_news_data(symbol)
            social_data = await self._fetch_social_data(symbol)
            
            # Analyze sentiment
            news_sentiment = self.sentiment_analyzer.analyze_text_list([item['title'] + ' ' + item.get('content', '') for item in news_data])
            social_sentiment = self.sentiment_analyzer.analyze_text_list([item['text'] for item in social_data])
            
            # Combine sentiments with weights
            overall_sentiment = (news_sentiment['sentiment'] * 0.7 + social_sentiment['sentiment'] * 0.3)
            confidence = (news_sentiment['confidence'] * 0.7 + social_sentiment['confidence'] * 0.3)
            
            # Extract keywords
            keywords = self._extract_keywords(news_data + social_data)
            
            result = SentimentAnalysis(
                overall_sentiment=overall_sentiment,
                sentiment_score=overall_sentiment,
                confidence=confidence,
                sources=['news', 'social_media'],
                keywords=keywords,
                timestamp=datetime.utcnow(),
                breakdown={
                    'news': news_sentiment['sentiment'],
                    'social_media': social_sentiment['sentiment']
                }
            )
            
            # Cache result
            await cache_manager.set(cache_key, result.__dict__, ttl=300)  # 5 minutes
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            return SentimentAnalysis(
                overall_sentiment=0.0,
                sentiment_score=0.0,
                confidence=0.0,
                sources=[],
                keywords=[],
                timestamp=datetime.utcnow(),
                breakdown={}
            )
    
    async def calculate_risk_metrics(self, portfolio_data: Dict[str, Any], 
                                   historical_data: pd.DataFrame) -> RiskMetrics:
        """Calculate comprehensive risk metrics for a portfolio"""
        try:
            # Calculate returns
            returns = historical_data.pct_change().dropna()
            
            # Value at Risk calculations
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            
            # Expected Shortfall (Conditional VaR)
            expected_shortfall = returns[returns <= var_95].mean()
            
            # Volatility
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
            # Beta (assuming market data available)
            market_returns = await self._get_market_returns()
            if market_returns is not None:
                beta = np.cov(returns, market_returns)[0, 1] / np.var(market_returns)
            else:
                beta = 1.0
            
            # Sharpe Ratio
            risk_free_rate = 0.02  # 2% annual risk-free rate
            excess_returns = returns - risk_free_rate / 252
            sharpe_ratio = excess_returns.mean() / returns.std() * np.sqrt(252)
            
            # Sortino Ratio
            downside_returns = returns[returns < 0]
            sortino_ratio = excess_returns.mean() / downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
            
            # Maximum Drawdown
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # Correlation matrix
            correlation_matrix = returns.corr().values
            
            # Stress test results
            stress_test_results = await self._run_stress_tests(portfolio_data, historical_data)
            
            return RiskMetrics(
                var_95=var_95,
                var_99=var_99,
                expected_shortfall=expected_shortfall,
                volatility=volatility,
                beta=beta,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                correlation_matrix=correlation_matrix,
                stress_test_results=stress_test_results
            )
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            raise
    
    async def generate_market_signals(self, symbol: str, 
                                    indicators: Optional[List[str]] = None) -> List[MarketSignal]:
        """Generate trading signals based on technical indicators"""
        if indicators is None:
            indicators = ['rsi', 'macd', 'bollinger_bands', 'moving_averages']
        
        try:
            # Get historical data
            historical_data = await self._get_historical_data(symbol, period="1y")
            if historical_data is None or historical_data.empty:
                return []
            
            signals = []
            
            # RSI Analysis
            if 'rsi' in indicators:
                rsi_signals = self._analyze_rsi(historical_data)
                signals.extend(rsi_signals)
            
            # MACD Analysis
            if 'macd' in indicators:
                macd_signals = self._analyze_macd(historical_data)
                signals.extend(macd_signals)
            
            # Bollinger Bands Analysis
            if 'bollinger_bands' in indicators:
                bb_signals = self._analyze_bollinger_bands(historical_data)
                signals.extend(bb_signals)
            
            # Moving Averages Analysis
            if 'moving_averages' in indicators:
                ma_signals = self._analyze_moving_averages(historical_data)
                signals.extend(ma_signals)
            
            # Sentiment-based signals
            sentiment = await self.analyze_market_sentiment(symbol)
            if abs(sentiment.overall_sentiment) > 0.3:
                sentiment_signal = MarketSignal(
                    symbol=symbol,
                    signal_type='buy' if sentiment.overall_sentiment > 0 else 'sell',
                    confidence=sentiment.confidence,
                    strength=abs(sentiment.overall_sentiment),
                    timestamp=datetime.utcnow(),
                    indicators={'sentiment': sentiment.overall_sentiment},
                    description=f"Sentiment-based signal: {sentiment.overall_sentiment:.2f}"
                )
                signals.append(sentiment_signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating market signals for {symbol}: {e}")
            return []
    
    async def optimize_portfolio(self, assets: List[str], 
                               constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize portfolio allocation using advanced algorithms"""
        try:
            # Get historical data for all assets
            historical_data = {}
            for asset in assets:
                data = await self._get_historical_data(asset, period="2y")
                if data is not None:
                    historical_data[asset] = data['Close']
            
            if len(historical_data) < 2:
                raise ValueError("Insufficient data for portfolio optimization")
            
            # Create returns dataframe
            returns_df = pd.DataFrame(historical_data).pct_change().dropna()
            
            # Calculate expected returns and covariance matrix
            expected_returns = returns_df.mean() * 252  # Annualized
            covariance_matrix = returns_df.cov() * 252  # Annualized
            
            # Run portfolio optimization
            optimal_weights = self.portfolio_optimizer.optimize(
                expected_returns=expected_returns,
                covariance_matrix=covariance_matrix,
                constraints=constraints
            )
            
            # Calculate portfolio metrics
            portfolio_return = (optimal_weights * expected_returns).sum()
            portfolio_volatility = np.sqrt(optimal_weights.T @ covariance_matrix @ optimal_weights)
            sharpe_ratio = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
            
            return {
                'weights': dict(zip(assets, optimal_weights)),
                'expected_return': portfolio_return,
                'volatility': portfolio_volatility,
                'sharpe_ratio': sharpe_ratio,
                'assets': assets,
                'optimization_method': 'efficient_frontier'
            }
            
        except Exception as e:
            logger.error(f"Error optimizing portfolio: {e}")
            raise
    
    async def predict_revenue(self, company_data: Dict[str, Any], 
                            forecast_periods: int = 12) -> Dict[str, Any]:
        """Predict company revenue using ML models"""
        try:
            # Prepare features
            features = self._prepare_revenue_features(company_data)
            
            # Get prediction from model
            prediction = self.revenue_predictor.predict(
                features=features,
                periods=forecast_periods
            )
            
            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(prediction)
            
            return {
                'predictions': prediction.tolist(),
                'confidence_intervals': confidence_intervals,
                'forecast_periods': forecast_periods,
                'model_confidence': 0.85,  # Placeholder
                'last_updated': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting revenue: {e}")
            raise
    
    async def run_performance_analytics(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive performance analytics"""
        try:
            # Calculate various performance metrics
            metrics = {}
            
            # Return metrics
            metrics['total_return'] = self._calculate_total_return(portfolio_data)
            metrics['annualized_return'] = self._calculate_annualized_return(portfolio_data)
            metrics['volatility'] = self._calculate_volatility(portfolio_data)
            
            # Risk-adjusted metrics
            metrics['sharpe_ratio'] = self._calculate_sharpe_ratio(portfolio_data)
            metrics['sortino_ratio'] = self._calculate_sortino_ratio(portfolio_data)
            metrics['calmar_ratio'] = self._calculate_calmar_ratio(portfolio_data)
            
            # Drawdown metrics
            metrics['max_drawdown'] = self._calculate_max_drawdown(portfolio_data)
            metrics['avg_drawdown'] = self._calculate_avg_drawdown(portfolio_data)
            
            # Benchmark comparison
            benchmark_data = await self._get_benchmark_data(portfolio_data.get('benchmark', 'SPY'))
            if benchmark_data:
                metrics['benchmark_comparison'] = self._compare_to_benchmark(portfolio_data, benchmark_data)
            
            # Attribution analysis
            metrics['attribution'] = await self._run_attribution_analysis(portfolio_data)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error running performance analytics: {e}")
            raise
    
    async def create_real_time_dashboard(self, symbols: List[str]) -> Dict[str, Any]:
        """Create real-time dashboard data for multiple symbols"""
        try:
            dashboard_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'symbols': {},
                'market_overview': {},
                'alerts': []
            }
            
            # Process symbols in parallel
            tasks = []
            for symbol in symbols:
                tasks.append(self._process_symbol_data(symbol))
            
            symbol_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, symbol in enumerate(symbols):
                if isinstance(symbol_results[i], Exception):
                    logger.error(f"Error processing {symbol}: {symbol_results[i]}")
                    continue
                
                dashboard_data['symbols'][symbol] = symbol_results[i]
            
            # Market overview
            dashboard_data['market_overview'] = await self._get_market_overview()
            
            # Generate alerts
            dashboard_data['alerts'] = await self._generate_alerts(symbols)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error creating real-time dashboard: {e}")
            raise
    
    # Helper methods
    async def _fetch_news_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch news data for a symbol"""
        # Placeholder implementation - would integrate with news APIs
        return [
            {'title': f'News about {symbol}', 'content': 'Sample content', 'source': 'Reuters'},
            {'title': f'Analysis: {symbol} performance', 'content': 'Sample analysis', 'source': 'Bloomberg'}
        ]
    
    async def _fetch_social_data(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch social media data for a symbol"""
        # Placeholder implementation - would integrate with social media APIs
        return [
            {'text': f'$#{symbol} looking bullish today!', 'source': 'twitter'},
            {'text': f'#{symbol} earnings beat expectations', 'source': 'reddit'}
        ]
    
    def _extract_keywords(self, data: List[Dict[str, Any]]) -> List[str]:
        """Extract keywords from text data"""
        # Simple keyword extraction - could be enhanced with NLP
        keywords = []
        for item in data:
            text = item.get('title', '') + ' ' + item.get('content', '') + ' ' + item.get('text', '')
            words = text.lower().split()
            keywords.extend([word for word in words if len(word) > 3])
        
        # Return most common keywords
        from collections import Counter
        return [word for word, count in Counter(keywords).most_common(10)]
    
    async def _get_historical_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """Get historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None
    
    async def _get_market_returns(self) -> Optional[pd.Series]:
        """Get market returns for beta calculation"""
        try:
            market_data = await self._get_historical_data("SPY", period="1y")
            if market_data is not None:
                return market_data['Close'].pct_change().dropna()
            return None
        except Exception as e:
            logger.error(f"Error fetching market returns: {e}")
            return None
    
    async def _run_stress_tests(self, portfolio_data: Dict[str, Any], 
                              historical_data: pd.DataFrame) -> Dict[str, float]:
        """Run stress tests on portfolio"""
        stress_scenarios = {
            'market_crash': -0.20,
            'recession': -0.15,
            'volatility_spike': 0.50,
            'interest_rate_hike': 0.02
        }
        
        results = {}
        for scenario, shock in stress_scenarios.items():
            # Apply shock to portfolio
            stressed_returns = historical_data.pct_change().dropna() * (1 + shock)
            results[scenario] = stressed_returns.mean()
        
        return results
    
    def _analyze_rsi(self, data: pd.DataFrame) -> List[MarketSignal]:
        """Analyze RSI indicator"""
        signals = []
        if len(data) < 14:
            return signals
        
        # Calculate RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < 30:
            signals.append(MarketSignal(
                symbol=data.name if hasattr(data, 'name') else 'UNKNOWN',
                signal_type='buy',
                confidence=0.7,
                strength=0.8,
                timestamp=datetime.utcnow(),
                indicators={'rsi': current_rsi},
                description=f"RSI oversold: {current_rsi:.2f}"
            ))
        elif current_rsi > 70:
            signals.append(MarketSignal(
                symbol=data.name if hasattr(data, 'name') else 'UNKNOWN',
                signal_type='sell',
                confidence=0.7,
                strength=0.8,
                timestamp=datetime.utcnow(),
                indicators={'rsi': current_rsi},
                description=f"RSI overbought: {current_rsi:.2f}"
            ))
        
        return signals
    
    def _analyze_macd(self, data: pd.DataFrame) -> List[MarketSignal]:
        """Analyze MACD indicator"""
        signals = []
        if len(data) < 26:
            return signals
        
        # Calculate MACD
        exp1 = data['Close'].ewm(span=12).mean()
        exp2 = data['Close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        current_macd = macd.iloc[-1]
        current_signal = signal.iloc[-1]
        current_histogram = histogram.iloc[-1]
        prev_histogram = histogram.iloc[-2] if len(histogram) > 1 else 0
        
        # MACD crossover signals
        if current_macd > current_signal and prev_histogram < 0 and current_histogram > 0:
            signals.append(MarketSignal(
                symbol=data.name if hasattr(data, 'name') else 'UNKNOWN',
                signal_type='buy',
                confidence=0.8,
                strength=0.9,
                timestamp=datetime.utcnow(),
                indicators={'macd': current_macd, 'signal': current_signal},
                description="MACD bullish crossover"
            ))
        elif current_macd < current_signal and prev_histogram > 0 and current_histogram < 0:
            signals.append(MarketSignal(
                symbol=data.name if hasattr(data, 'name') else 'UNKNOWN',
                signal_type='sell',
                confidence=0.8,
                strength=0.9,
                timestamp=datetime.utcnow(),
                indicators={'macd': current_macd, 'signal': current_signal},
                description="MACD bearish crossover"
            ))
        
        return signals
    
    def _analyze_bollinger_bands(self, data: pd.DataFrame) -> List[MarketSignal]:
        """Analyze Bollinger Bands"""
        signals = []
        if len(data) < 20:
            return signals
        
        # Calculate Bollinger Bands
        sma = data['Close'].rolling(window=20).mean()
        std = data['Close'].rolling(window=20).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        current_price = data['Close'].iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        
        if current_price <= current_lower:
            signals.append(MarketSignal(
                symbol=data.name if hasattr(data, 'name') else 'UNKNOWN',
                signal_type='buy',
                confidence=0.6,
                strength=0.7,
                timestamp=datetime.utcnow(),
                indicators={'price': current_price, 'lower_band': current_lower},
                description="Price at lower Bollinger Band"
            ))
        elif current_price >= current_upper:
            signals.append(MarketSignal(
                symbol=data.name if hasattr(data, 'name') else 'UNKNOWN',
                signal_type='sell',
                confidence=0.6,
                strength=0.7,
                timestamp=datetime.utcnow(),
                indicators={'price': current_price, 'upper_band': current_upper},
                description="Price at upper Bollinger Band"
            ))
        
        return signals
    
    def _analyze_moving_averages(self, data: pd.DataFrame) -> List[MarketSignal]:
        """Analyze moving averages"""
        signals = []
        if len(data) < 50:
            return signals
        
        # Calculate moving averages
        sma_20 = data['Close'].rolling(window=20).mean()
        sma_50 = data['Close'].rolling(window=50).mean()
        
        current_sma_20 = sma_20.iloc[-1]
        current_sma_50 = sma_50.iloc[-1]
        prev_sma_20 = sma_20.iloc[-2] if len(sma_20) > 1 else current_sma_20
        prev_sma_50 = sma_50.iloc[-2] if len(sma_50) > 1 else current_sma_50
        
        # Golden cross (20-day crosses above 50-day)
        if current_sma_20 > current_sma_50 and prev_sma_20 <= prev_sma_50:
            signals.append(MarketSignal(
                symbol=data.name if hasattr(data, 'name') else 'UNKNOWN',
                signal_type='buy',
                confidence=0.7,
                strength=0.8,
                timestamp=datetime.utcnow(),
                indicators={'sma_20': current_sma_20, 'sma_50': current_sma_50},
                description="Golden cross detected"
            ))
        # Death cross (20-day crosses below 50-day)
        elif current_sma_20 < current_sma_50 and prev_sma_20 >= prev_sma_50:
            signals.append(MarketSignal(
                symbol=data.name if hasattr(data, 'name') else 'UNKNOWN',
                signal_type='sell',
                confidence=0.7,
                strength=0.8,
                timestamp=datetime.utcnow(),
                indicators={'sma_20': current_sma_20, 'sma_50': current_sma_50},
                description="Death cross detected"
            ))
        
        return signals
    
    def _prepare_revenue_features(self, company_data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for revenue prediction"""
        # Extract relevant features from company data
        features = []
        
        # Financial ratios
        features.extend([
            company_data.get('revenue_growth', 0),
            company_data.get('profit_margin', 0),
            company_data.get('debt_to_equity', 0),
            company_data.get('current_ratio', 0),
            company_data.get('roe', 0),
            company_data.get('roa', 0)
        ])
        
        # Market indicators
        features.extend([
            company_data.get('pe_ratio', 0),
            company_data.get('pb_ratio', 0),
            company_data.get('market_cap', 0),
            company_data.get('beta', 1.0)
        ])
        
        return np.array(features).reshape(1, -1)
    
    def _calculate_confidence_intervals(self, predictions: np.ndarray, 
                                      confidence_level: float = 0.95) -> Dict[str, List[float]]:
        """Calculate confidence intervals for predictions"""
        # Simple confidence interval calculation
        std_error = predictions.std() * 0.1  # Placeholder
        z_score = stats.norm.ppf((1 + confidence_level) / 2)
        margin_of_error = z_score * std_error
        
        return {
            'lower': (predictions - margin_of_error).tolist(),
            'upper': (predictions + margin_of_error).tolist()
        }
    
    async def _process_symbol_data(self, symbol: str) -> Dict[str, Any]:
        """Process data for a single symbol"""
        try:
            # Get current price and basic data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get recent price data
            hist = ticker.history(period="5d")
            current_price = hist['Close'].iloc[-1] if not hist.empty else 0
            
            # Get sentiment
            sentiment = await self.analyze_market_sentiment(symbol)
            
            # Get signals
            signals = await self.generate_market_signals(symbol)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'change': hist['Close'].iloc[-1] - hist['Close'].iloc[-2] if len(hist) > 1 else 0,
                'change_percent': ((hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100) if len(hist) > 1 else 0,
                'volume': hist['Volume'].iloc[-1] if not hist.empty else 0,
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'sentiment': sentiment.overall_sentiment,
                'signals': [signal.__dict__ for signal in signals],
                'last_updated': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error processing symbol {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    async def _get_market_overview(self) -> Dict[str, Any]:
        """Get market overview data"""
        try:
            # Get major indices
            indices = ['^GSPC', '^DJI', '^IXIC', '^VIX']
            overview = {}
            
            for index in indices:
                ticker = yf.Ticker(index)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    previous = hist['Close'].iloc[-2] if len(hist) > 1 else current
                    change = current - previous
                    change_percent = ((current / previous - 1) * 100) if previous != 0 else 0
                    
                    overview[index] = {
                        'current': current,
                        'change': change,
                        'change_percent': change_percent
                    }
            
            return overview
        except Exception as e:
            logger.error(f"Error getting market overview: {e}")
            return {}
    
    async def _generate_alerts(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Generate alerts for symbols"""
        alerts = []
        
        for symbol in symbols:
            try:
                # Check for significant price movements
                hist = yf.Ticker(symbol).history(period="2d")
                if len(hist) > 1:
                    change_percent = ((hist['Close'].iloc[-1] / hist['Close'].iloc[-2] - 1) * 100)
                    
                    if abs(change_percent) > 5:  # 5% threshold
                        alerts.append({
                            'symbol': symbol,
                            'type': 'price_alert',
                            'message': f'{symbol} moved {change_percent:.2f}%',
                            'severity': 'high' if abs(change_percent) > 10 else 'medium',
                            'timestamp': datetime.utcnow().isoformat()
                        })
                
                # Check for volume spikes
                if len(hist) > 5:
                    avg_volume = hist['Volume'].iloc[:-1].mean()
                    current_volume = hist['Volume'].iloc[-1]
                    
                    if current_volume > avg_volume * 2:  # 2x average volume
                        alerts.append({
                            'symbol': symbol,
                            'type': 'volume_alert',
                            'message': f'{symbol} volume spike detected',
                            'severity': 'medium',
                            'timestamp': datetime.utcnow().isoformat()
                        })
            
            except Exception as e:
                logger.error(f"Error generating alerts for {symbol}: {e}")
        
        return alerts
    
    # Performance calculation methods
    def _calculate_total_return(self, portfolio_data: Dict[str, Any]) -> float:
        """Calculate total return"""
        # Placeholder implementation
        return 0.15  # 15% example return
    
    def _calculate_annualized_return(self, portfolio_data: Dict[str, Any]) -> float:
        """Calculate annualized return"""
        # Placeholder implementation
        return 0.12  # 12% example annualized return
    
    def _calculate_volatility(self, portfolio_data: Dict[str, Any]) -> float:
        """Calculate volatility"""
        # Placeholder implementation
        return 0.18  # 18% example volatility
    
    def _calculate_sharpe_ratio(self, portfolio_data: Dict[str, Any]) -> float:
        """Calculate Sharpe ratio"""
        # Placeholder implementation
        return 0.67  # Example Sharpe ratio
    
    def _calculate_sortino_ratio(self, portfolio_data: Dict[str, Any]) -> float:
        """Calculate Sortino ratio"""
        # Placeholder implementation
        return 0.85  # Example Sortino ratio
    
    def _calculate_calmar_ratio(self, portfolio_data: Dict[str, Any]) -> float:
        """Calculate Calmar ratio"""
        # Placeholder implementation
        return 0.45  # Example Calmar ratio
    
    def _calculate_max_drawdown(self, portfolio_data: Dict[str, Any]) -> float:
        """Calculate maximum drawdown"""
        # Placeholder implementation
        return -0.08  # -8% example max drawdown
    
    def _calculate_avg_drawdown(self, portfolio_data: Dict[str, Any]) -> float:
        """Calculate average drawdown"""
        # Placeholder implementation
        return -0.03  # -3% example average drawdown
    
    async def _get_benchmark_data(self, benchmark: str) -> Optional[Dict[str, Any]]:
        """Get benchmark data for comparison"""
        # Placeholder implementation
        return {
            'return': 0.10,
            'volatility': 0.15,
            'sharpe_ratio': 0.67
        }
    
    def _compare_to_benchmark(self, portfolio_data: Dict[str, Any], 
                            benchmark_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare portfolio to benchmark"""
        # Placeholder implementation
        return {
            'excess_return': 0.02,
            'information_ratio': 0.25,
            'tracking_error': 0.05
        }
    
    async def _run_attribution_analysis(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run attribution analysis"""
        # Placeholder implementation
        return {
            'asset_allocation': 0.03,
            'stock_selection': 0.01,
            'interaction': 0.01,
            'total_active_return': 0.05
        }


# Global analytics engine instance
analytics_engine = AdvancedAnalyticsEngine()
