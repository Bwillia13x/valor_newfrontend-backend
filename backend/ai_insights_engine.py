"""
AI-Powered Insights Engine for Valor IVX Platform
Phase 9: Advanced Analytics and Machine Learning

This module provides AI-powered capabilities including:
- Automated financial analysis
- Intelligent recommendations
- AI-driven insights
- Predictive analytics
- Natural language processing
- Intelligent alerts
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import yfinance as yf
import requests
from textblob import TextBlob
import redis

from .analytics_engine import analytics_engine
from .ml_models.registry import ModelRegistry
from .settings import settings

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    """AI insight data structure"""
    insight_type: str
    symbol: str
    confidence: float
    description: str
    recommendation: str
    reasoning: List[str]
    data_points: Dict[str, Any]
    timestamp: datetime
    priority: str = "medium"  # low, medium, high, critical


@dataclass
class Recommendation:
    """AI recommendation data structure"""
    recommendation_type: str
    symbol: str
    action: str  # buy, sell, hold, watch
    confidence: float
    target_price: Optional[float]
    stop_loss: Optional[float]
    time_horizon: str  # short_term, medium_term, long_term
    reasoning: List[str]
    risk_level: str  # low, medium, high
    timestamp: datetime


@dataclass
class MarketIntelligence:
    """Market intelligence data structure"""
    market_sentiment: float
    sector_performance: Dict[str, float]
    market_regime: str  # bullish, bearish, sideways
    volatility_regime: str  # low, medium, high
    correlation_regime: str  # low, medium, high
    key_drivers: List[str]
    risks: List[str]
    opportunities: List[str]
    timestamp: datetime


class AIInsightsEngine:
    """AI-powered insights engine for financial analysis"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.model_registry = ModelRegistry()
        
        # AI models
        self.price_predictor = None
        self.sentiment_classifier = None
        self.anomaly_detector = None
        self.clustering_model = None
        
        # Initialize models
        self._initialize_models()
        
        # Cache for insights and recommendations
        self.insights_cache = {}
        self.recommendations_cache = {}
        
        # Performance tracking
        self.insights_generated = 0
        self.recommendations_generated = 0
        self.accuracy_metrics = {}
        
        logger.info("AI Insights Engine initialized")
    
    def _initialize_models(self):
        """Initialize AI models"""
        try:
            # Initialize price prediction model
            self.price_predictor = RandomForestRegressor(
                n_estimators=100,
                random_state=42
            )
            
            # Initialize anomaly detection model
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            # Initialize clustering model
            self.clustering_model = KMeans(
                n_clusters=5,
                random_state=42
            )
            
            logger.info("AI models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing AI models: {e}")
    
    async def generate_insights(self, symbol: str, 
                              analysis_types: Optional[List[str]] = None) -> List[Insight]:
        """Generate AI-powered insights for a symbol"""
        if analysis_types is None:
            analysis_types = ["technical", "fundamental", "sentiment", "risk"]
        
        insights = []
        
        try:
            # Technical analysis insights
            if "technical" in analysis_types:
                technical_insights = await self._analyze_technical_patterns(symbol)
                insights.extend(technical_insights)
            
            # Fundamental analysis insights
            if "fundamental" in analysis_types:
                fundamental_insights = await self._analyze_fundamentals(symbol)
                insights.extend(fundamental_insights)
            
            # Sentiment analysis insights
            if "sentiment" in analysis_types:
                sentiment_insights = await self._analyze_sentiment_patterns(symbol)
                insights.extend(sentiment_insights)
            
            # Risk analysis insights
            if "risk" in analysis_types:
                risk_insights = await self._analyze_risk_patterns(symbol)
                insights.extend(risk_insights)
            
            # Update cache
            self.insights_cache[symbol] = insights
            self.insights_generated += len(insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights for {symbol}: {e}")
            return []
    
    async def generate_recommendations(self, symbol: str, 
                                     user_profile: Optional[Dict[str, Any]] = None) -> List[Recommendation]:
        """Generate AI-powered recommendations for a symbol"""
        recommendations = []
        
        try:
            # Get comprehensive analysis
            insights = await self.generate_insights(symbol)
            
            # Generate trading recommendations
            trading_recs = await self._generate_trading_recommendations(symbol, insights, user_profile)
            recommendations.extend(trading_recs)
            
            # Generate portfolio recommendations
            portfolio_recs = await self._generate_portfolio_recommendations(symbol, insights, user_profile)
            recommendations.extend(portfolio_recs)
            
            # Generate risk management recommendations
            risk_recs = await self._generate_risk_recommendations(symbol, insights, user_profile)
            recommendations.extend(risk_recs)
            
            # Update cache
            self.recommendations_cache[symbol] = recommendations
            self.recommendations_generated += len(recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations for {symbol}: {e}")
            return []
    
    async def analyze_market_intelligence(self, symbols: List[str]) -> MarketIntelligence:
        """Analyze market intelligence across multiple symbols"""
        try:
            # Aggregate sentiment analysis
            sentiments = []
            for symbol in symbols:
                sentiment = await analytics_engine.analyze_market_sentiment(symbol)
                sentiments.append(sentiment.overall_sentiment)
            
            market_sentiment = np.mean(sentiments) if sentiments else 0.0
            
            # Analyze sector performance
            sector_performance = await self._analyze_sector_performance(symbols)
            
            # Determine market regime
            market_regime = self._determine_market_regime(symbols)
            
            # Analyze volatility regime
            volatility_regime = await self._analyze_volatility_regime(symbols)
            
            # Analyze correlation regime
            correlation_regime = await self._analyze_correlation_regime(symbols)
            
            # Identify key drivers and risks
            key_drivers = await self._identify_key_drivers(symbols)
            risks = await self._identify_market_risks(symbols)
            opportunities = await self._identify_opportunities(symbols)
            
            return MarketIntelligence(
                market_sentiment=market_sentiment,
                sector_performance=sector_performance,
                market_regime=market_regime,
                volatility_regime=volatility_regime,
                correlation_regime=correlation_regime,
                key_drivers=key_drivers,
                risks=risks,
                opportunities=opportunities,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing market intelligence: {e}")
            return MarketIntelligence(
                market_sentiment=0.0,
                sector_performance={},
                market_regime="unknown",
                volatility_regime="unknown",
                correlation_regime="unknown",
                key_drivers=[],
                risks=[],
                opportunities=[],
                timestamp=datetime.utcnow()
            )
    
    async def predict_price_movement(self, symbol: str, 
                                   timeframe: str = "1d") -> Dict[str, Any]:
        """Predict price movement using AI models"""
        try:
            # Get historical data
            historical_data = await analytics_engine._get_historical_data(symbol, "1y")
            if historical_data is None or historical_data.empty:
                return {"error": "Insufficient data for prediction"}
            
            # Prepare features
            features = self._prepare_price_features(historical_data)
            
            # Make prediction
            prediction = self.price_predictor.predict(features.reshape(1, -1))[0]
            
            # Calculate confidence
            confidence = self._calculate_prediction_confidence(features)
            
            # Determine direction
            current_price = historical_data['Close'].iloc[-1]
            direction = "up" if prediction > current_price else "down"
            
            return {
                "symbol": symbol,
                "current_price": current_price,
                "predicted_price": prediction,
                "direction": direction,
                "confidence": confidence,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting price movement for {symbol}: {e}")
            return {"error": str(e)}
    
    async def detect_anomalies(self, symbol: str, 
                             data_type: str = "price") -> List[Dict[str, Any]]:
        """Detect anomalies in financial data"""
        try:
            # Get data based on type
            if data_type == "price":
                data = await analytics_engine._get_historical_data(symbol, "1y")
                if data is not None:
                    values = data['Close'].values
                else:
                    return []
            elif data_type == "volume":
                data = await analytics_engine._get_historical_data(symbol, "1y")
                if data is not None:
                    values = data['Volume'].values
                else:
                    return []
            else:
                return []
            
            # Detect anomalies
            values_reshaped = values.reshape(-1, 1)
            anomaly_scores = self.anomaly_detector.fit_predict(values_reshaped)
            
            # Identify anomalies
            anomalies = []
            for i, score in enumerate(anomaly_scores):
                if score == -1:  # Anomaly detected
                    anomalies.append({
                        "index": i,
                        "value": values[i],
                        "timestamp": data.index[i].isoformat() if hasattr(data.index[i], 'isoformat') else str(data.index[i]),
                        "anomaly_score": score
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for {symbol}: {e}")
            return []
    
    async def cluster_similar_assets(self, symbols: List[str]) -> Dict[str, List[str]]:
        """Cluster similar assets using AI"""
        try:
            # Get features for all symbols
            features_list = []
            valid_symbols = []
            
            for symbol in symbols:
                try:
                    data = await analytics_engine._get_historical_data(symbol, "1y")
                    if data is not None and not data.empty:
                        features = self._prepare_clustering_features(data)
                        features_list.append(features)
                        valid_symbols.append(symbol)
                except Exception as e:
                    logger.warning(f"Could not get data for {symbol}: {e}")
                    continue
            
            if len(features_list) < 2:
                return {}
            
            # Perform clustering
            features_array = np.array(features_list)
            clusters = self.clustering_model.fit_predict(features_array)
            
            # Group symbols by cluster
            clusters_dict = {}
            for i, cluster_id in enumerate(clusters):
                cluster_key = f"cluster_{cluster_id}"
                if cluster_key not in clusters_dict:
                    clusters_dict[cluster_key] = []
                clusters_dict[cluster_key].append(valid_symbols[i])
            
            return clusters_dict
            
        except Exception as e:
            logger.error(f"Error clustering assets: {e}")
            return {}
    
    async def generate_natural_language_summary(self, symbol: str) -> str:
        """Generate natural language summary of analysis"""
        try:
            # Get comprehensive analysis
            insights = await self.generate_insights(symbol)
            recommendations = await self.generate_recommendations(symbol)
            
            # Generate summary
            summary_parts = []
            
            # Price summary
            price_data = await analytics_engine._get_historical_data(symbol, "1m")
            if price_data is not None and not price_data.empty:
                current_price = price_data['Close'].iloc[-1]
                change = price_data['Close'].iloc[-1] - price_data['Close'].iloc[-2] if len(price_data) > 1 else 0
                change_percent = (change / price_data['Close'].iloc[-2] * 100) if len(price_data) > 1 and price_data['Close'].iloc[-2] != 0 else 0
                
                summary_parts.append(f"{symbol} is currently trading at ${current_price:.2f}")
                if change != 0:
                    direction = "up" if change > 0 else "down"
                    summary_parts.append(f"({direction} {abs(change_percent):.2f}%)")
            
            # Key insights
            if insights:
                key_insights = [insight for insight in insights if insight.priority in ["high", "critical"]]
                if key_insights:
                    summary_parts.append("Key insights:")
                    for insight in key_insights[:3]:  # Top 3 insights
                        summary_parts.append(f"- {insight.description}")
            
            # Recommendations
            if recommendations:
                top_recommendation = max(recommendations, key=lambda x: x.confidence)
                summary_parts.append(f"Recommendation: {top_recommendation.action.upper()} with {top_recommendation.confidence:.1%} confidence")
                summary_parts.append(f"Reasoning: {', '.join(top_recommendation.reasoning[:2])}")
            
            return " ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error generating summary for {symbol}: {e}")
            return f"Analysis for {symbol} is currently unavailable."
    
    # Helper methods for insights generation
    async def _analyze_technical_patterns(self, symbol: str) -> List[Insight]:
        """Analyze technical patterns and generate insights"""
        insights = []
        
        try:
            # Get historical data
            data = await analytics_engine._get_historical_data(symbol, "6m")
            if data is None or data.empty:
                return insights
            
            # RSI analysis
            if len(data) >= 14:
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = rsi.iloc[-1]
                
                if current_rsi < 30:
                    insights.append(Insight(
                        insight_type="technical",
                        symbol=symbol,
                        confidence=0.8,
                        description=f"{symbol} is oversold with RSI at {current_rsi:.1f}",
                        recommendation="Consider buying opportunity",
                        reasoning=["RSI below 30 indicates oversold conditions", "Potential reversal point"],
                        data_points={"rsi": current_rsi, "threshold": 30},
                        timestamp=datetime.utcnow(),
                        priority="high"
                    ))
                elif current_rsi > 70:
                    insights.append(Insight(
                        insight_type="technical",
                        symbol=symbol,
                        confidence=0.8,
                        description=f"{symbol} is overbought with RSI at {current_rsi:.1f}",
                        recommendation="Consider taking profits",
                        reasoning=["RSI above 70 indicates overbought conditions", "Potential reversal point"],
                        data_points={"rsi": current_rsi, "threshold": 70},
                        timestamp=datetime.utcnow(),
                        priority="high"
                    ))
            
            # Moving average analysis
            if len(data) >= 50:
                sma_20 = data['Close'].rolling(window=20).mean()
                sma_50 = data['Close'].rolling(window=50).mean()
                
                current_price = data['Close'].iloc[-1]
                current_sma_20 = sma_20.iloc[-1]
                current_sma_50 = sma_50.iloc[-1]
                
                if current_price > current_sma_20 > current_sma_50:
                    insights.append(Insight(
                        insight_type="technical",
                        symbol=symbol,
                        confidence=0.7,
                        description=f"{symbol} shows bullish trend with price above moving averages",
                        recommendation="Trend following strategy favorable",
                        reasoning=["Price above 20-day and 50-day moving averages", "Uptrend confirmed"],
                        data_points={"price": current_price, "sma_20": current_sma_20, "sma_50": current_sma_50},
                        timestamp=datetime.utcnow(),
                        priority="medium"
                    ))
                elif current_price < current_sma_20 < current_sma_50:
                    insights.append(Insight(
                        insight_type="technical",
                        symbol=symbol,
                        confidence=0.7,
                        description=f"{symbol} shows bearish trend with price below moving averages",
                        recommendation="Consider defensive positioning",
                        reasoning=["Price below 20-day and 50-day moving averages", "Downtrend confirmed"],
                        data_points={"price": current_price, "sma_20": current_sma_20, "sma_50": current_sma_50},
                        timestamp=datetime.utcnow(),
                        priority="medium"
                    ))
            
            # Volume analysis
            if len(data) >= 20:
                avg_volume = data['Volume'].rolling(window=20).mean()
                current_volume = data['Volume'].iloc[-1]
                volume_ratio = current_volume / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 1
                
                if volume_ratio > 2:
                    insights.append(Insight(
                        insight_type="technical",
                        symbol=symbol,
                        confidence=0.6,
                        description=f"{symbol} shows high volume activity ({volume_ratio:.1f}x average)",
                        recommendation="Monitor for potential breakout or breakdown",
                        reasoning=["Volume spike often precedes significant price moves", "Increased market interest"],
                        data_points={"volume_ratio": volume_ratio, "current_volume": current_volume},
                        timestamp=datetime.utcnow(),
                        priority="medium"
                    ))
        
        except Exception as e:
            logger.error(f"Error analyzing technical patterns for {symbol}: {e}")
        
        return insights
    
    async def _analyze_fundamentals(self, symbol: str) -> List[Insight]:
        """Analyze fundamental factors and generate insights"""
        insights = []
        
        try:
            # Get fundamental data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # P/E ratio analysis
            pe_ratio = info.get('trailingPE')
            if pe_ratio:
                if pe_ratio < 15:
                    insights.append(Insight(
                        insight_type="fundamental",
                        symbol=symbol,
                        confidence=0.7,
                        description=f"{symbol} has low P/E ratio of {pe_ratio:.1f}",
                        recommendation="Potential value opportunity",
                        reasoning=["P/E below 15 suggests undervaluation", "Value investing opportunity"],
                        data_points={"pe_ratio": pe_ratio, "threshold": 15},
                        timestamp=datetime.utcnow(),
                        priority="medium"
                    ))
                elif pe_ratio > 30:
                    insights.append(Insight(
                        insight_type="fundamental",
                        symbol=symbol,
                        confidence=0.7,
                        description=f"{symbol} has high P/E ratio of {pe_ratio:.1f}",
                        recommendation="Consider growth expectations",
                        reasoning=["P/E above 30 suggests high growth expectations", "Premium valuation"],
                        data_points={"pe_ratio": pe_ratio, "threshold": 30},
                        timestamp=datetime.utcnow(),
                        priority="medium"
                    ))
            
            # Market cap analysis
            market_cap = info.get('marketCap')
            if market_cap:
                if market_cap < 2e9:  # < $2B
                    insights.append(Insight(
                        insight_type="fundamental",
                        symbol=symbol,
                        confidence=0.6,
                        description=f"{symbol} is a small-cap stock (${market_cap/1e9:.1f}B)",
                        recommendation="Higher volatility expected",
                        reasoning=["Small-cap stocks typically have higher volatility", "Growth potential but higher risk"],
                        data_points={"market_cap": market_cap, "category": "small_cap"},
                        timestamp=datetime.utcnow(),
                        priority="medium"
                    ))
                elif market_cap > 10e9:  # > $10B
                    insights.append(Insight(
                        insight_type="fundamental",
                        symbol=symbol,
                        confidence=0.6,
                        description=f"{symbol} is a large-cap stock (${market_cap/1e9:.1f}B)",
                        recommendation="Stability and lower volatility",
                        reasoning=["Large-cap stocks typically have lower volatility", "Established business model"],
                        data_points={"market_cap": market_cap, "category": "large_cap"},
                        timestamp=datetime.utcnow(),
                        priority="low"
                    ))
        
        except Exception as e:
            logger.error(f"Error analyzing fundamentals for {symbol}: {e}")
        
        return insights
    
    async def _analyze_sentiment_patterns(self, symbol: str) -> List[Insight]:
        """Analyze sentiment patterns and generate insights"""
        insights = []
        
        try:
            # Get sentiment analysis
            sentiment = await analytics_engine.analyze_market_sentiment(symbol)
            
            if sentiment.overall_sentiment > 0.3:
                insights.append(Insight(
                    insight_type="sentiment",
                    symbol=symbol,
                    confidence=sentiment.confidence,
                    description=f"{symbol} shows positive sentiment ({sentiment.overall_sentiment:.2f})",
                    recommendation="Sentiment supports bullish outlook",
                    reasoning=["Positive news and social media sentiment", "Market optimism"],
                    data_points={"sentiment": sentiment.overall_sentiment, "confidence": sentiment.confidence},
                    timestamp=datetime.utcnow(),
                    priority="medium"
                ))
            elif sentiment.overall_sentiment < -0.3:
                insights.append(Insight(
                    insight_type="sentiment",
                    symbol=symbol,
                    confidence=sentiment.confidence,
                    description=f"{symbol} shows negative sentiment ({sentiment.overall_sentiment:.2f})",
                    recommendation="Sentiment suggests caution",
                    reasoning=["Negative news and social media sentiment", "Market pessimism"],
                    data_points={"sentiment": sentiment.overall_sentiment, "confidence": sentiment.confidence},
                    timestamp=datetime.utcnow(),
                    priority="medium"
                ))
        
        except Exception as e:
            logger.error(f"Error analyzing sentiment patterns for {symbol}: {e}")
        
        return insights
    
    async def _analyze_risk_patterns(self, symbol: str) -> List[Insight]:
        """Analyze risk patterns and generate insights"""
        insights = []
        
        try:
            # Get historical data for volatility analysis
            data = await analytics_engine._get_historical_data(symbol, "1y")
            if data is None or data.empty:
                return insights
            
            # Calculate volatility
            returns = data['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized
            
            if volatility > 0.4:  # > 40% annualized volatility
                insights.append(Insight(
                    insight_type="risk",
                    symbol=symbol,
                    confidence=0.8,
                    description=f"{symbol} shows high volatility ({volatility:.1%} annualized)",
                    recommendation="Consider position sizing and risk management",
                    reasoning=["High volatility indicates significant price swings", "Risk management crucial"],
                    data_points={"volatility": volatility, "threshold": 0.4},
                    timestamp=datetime.utcnow(),
                    priority="high"
                ))
            elif volatility < 0.15:  # < 15% annualized volatility
                insights.append(Insight(
                    insight_type="risk",
                    symbol=symbol,
                    confidence=0.8,
                    description=f"{symbol} shows low volatility ({volatility:.1%} annualized)",
                    recommendation="Lower risk profile suitable for conservative investors",
                    reasoning=["Low volatility indicates stable price movements", "Conservative investment option"],
                    data_points={"volatility": volatility, "threshold": 0.15},
                    timestamp=datetime.utcnow(),
                    priority="low"
                ))
        
        except Exception as e:
            logger.error(f"Error analyzing risk patterns for {symbol}: {e}")
        
        return insights
    
    # Helper methods for recommendations generation
    async def _generate_trading_recommendations(self, symbol: str, 
                                              insights: List[Insight], 
                                              user_profile: Optional[Dict[str, Any]]) -> List[Recommendation]:
        """Generate trading recommendations"""
        recommendations = []
        
        try:
            # Analyze insights to determine action
            technical_insights = [i for i in insights if i.insight_type == "technical"]
            sentiment_insights = [i for i in insights if i.insight_type == "sentiment"]
            
            # Determine action based on insights
            action = "hold"
            confidence = 0.5
            reasoning = []
            
            # Technical analysis
            bullish_signals = 0
            bearish_signals = 0
            
            for insight in technical_insights:
                if "oversold" in insight.description.lower() or "bullish" in insight.description.lower():
                    bullish_signals += 1
                elif "overbought" in insight.description.lower() or "bearish" in insight.description.lower():
                    bearish_signals += 1
            
            # Sentiment analysis
            for insight in sentiment_insights:
                if "positive" in insight.description.lower():
                    bullish_signals += 1
                elif "negative" in insight.description.lower():
                    bearish_signals += 1
            
            # Determine action
            if bullish_signals > bearish_signals and bullish_signals >= 2:
                action = "buy"
                confidence = min(0.8, 0.5 + (bullish_signals * 0.1))
                reasoning.append("Multiple bullish signals detected")
            elif bearish_signals > bullish_signals and bearish_signals >= 2:
                action = "sell"
                confidence = min(0.8, 0.5 + (bearish_signals * 0.1))
                reasoning.append("Multiple bearish signals detected")
            else:
                action = "hold"
                confidence = 0.6
                reasoning.append("Mixed signals, maintaining current position")
            
            # Calculate target price and stop loss
            current_price = 0
            target_price = None
            stop_loss = None
            
            try:
                data = await analytics_engine._get_historical_data(symbol, "1m")
                if data is not None and not data.empty:
                    current_price = data['Close'].iloc[-1]
                    
                    if action == "buy":
                        target_price = current_price * 1.1  # 10% upside
                        stop_loss = current_price * 0.95  # 5% downside
                    elif action == "sell":
                        target_price = current_price * 0.9  # 10% downside
                        stop_loss = current_price * 1.05  # 5% upside
            except Exception as e:
                logger.warning(f"Could not calculate price targets for {symbol}: {e}")
            
            # Determine time horizon
            time_horizon = "medium_term"
            if any("short" in insight.description.lower() for insight in technical_insights):
                time_horizon = "short_term"
            elif any("long" in insight.description.lower() for insight in technical_insights):
                time_horizon = "long_term"
            
            # Determine risk level
            risk_level = "medium"
            risk_insights = [i for i in insights if i.insight_type == "risk"]
            for insight in risk_insights:
                if "high volatility" in insight.description.lower():
                    risk_level = "high"
                elif "low volatility" in insight.description.lower():
                    risk_level = "low"
            
            recommendations.append(Recommendation(
                recommendation_type="trading",
                symbol=symbol,
                action=action,
                confidence=confidence,
                target_price=target_price,
                stop_loss=stop_loss,
                time_horizon=time_horizon,
                reasoning=reasoning,
                risk_level=risk_level,
                timestamp=datetime.utcnow()
            ))
        
        except Exception as e:
            logger.error(f"Error generating trading recommendations for {symbol}: {e}")
        
        return recommendations
    
    async def _generate_portfolio_recommendations(self, symbol: str, 
                                                insights: List[Insight], 
                                                user_profile: Optional[Dict[str, Any]]) -> List[Recommendation]:
        """Generate portfolio recommendations"""
        recommendations = []
        
        try:
            # Portfolio allocation recommendations
            fundamental_insights = [i for i in insights if i.insight_type == "fundamental"]
            
            for insight in fundamental_insights:
                if "value opportunity" in insight.recommendation.lower():
                    recommendations.append(Recommendation(
                        recommendation_type="portfolio",
                        symbol=symbol,
                        action="increase_allocation",
                        confidence=insight.confidence,
                        target_price=None,
                        stop_loss=None,
                        time_horizon="long_term",
                        reasoning=["Value investing opportunity", "Undervalued based on fundamentals"],
                        risk_level="medium",
                        timestamp=datetime.utcnow()
                    ))
                elif "premium valuation" in insight.recommendation.lower():
                    recommendations.append(Recommendation(
                        recommendation_type="portfolio",
                        symbol=symbol,
                        action="reduce_allocation",
                        confidence=insight.confidence,
                        target_price=None,
                        stop_loss=None,
                        time_horizon="medium_term",
                        reasoning=["Premium valuation", "Consider rebalancing"],
                        risk_level="medium",
                        timestamp=datetime.utcnow()
                    ))
        
        except Exception as e:
            logger.error(f"Error generating portfolio recommendations for {symbol}: {e}")
        
        return recommendations
    
    async def _generate_risk_recommendations(self, symbol: str, 
                                           insights: List[Insight], 
                                           user_profile: Optional[Dict[str, Any]]) -> List[Recommendation]:
        """Generate risk management recommendations"""
        recommendations = []
        
        try:
            risk_insights = [i for i in insights if i.insight_type == "risk"]
            
            for insight in risk_insights:
                if "high volatility" in insight.description.lower():
                    recommendations.append(Recommendation(
                        recommendation_type="risk_management",
                        symbol=symbol,
                        action="implement_stop_loss",
                        confidence=insight.confidence,
                        target_price=None,
                        stop_loss=None,
                        time_horizon="short_term",
                        reasoning=["High volatility requires risk management", "Protect against downside"],
                        risk_level="high",
                        timestamp=datetime.utcnow()
                    ))
                elif "low volatility" in insight.description.lower():
                    recommendations.append(Recommendation(
                        recommendation_type="risk_management",
                        symbol=symbol,
                        action="reduce_hedging",
                        confidence=insight.confidence,
                        target_price=None,
                        stop_loss=None,
                        time_horizon="medium_term",
                        reasoning=["Low volatility reduces hedging needs", "Cost optimization"],
                        risk_level="low",
                        timestamp=datetime.utcnow()
                    ))
        
        except Exception as e:
            logger.error(f"Error generating risk recommendations for {symbol}: {e}")
        
        return recommendations
    
    # Helper methods for market intelligence
    async def _analyze_sector_performance(self, symbols: List[str]) -> Dict[str, float]:
        """Analyze sector performance"""
        sector_performance = {}
        
        try:
            # Group symbols by sector (simplified)
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    sector = info.get('sector', 'Unknown')
                    
                    if sector not in sector_performance:
                        sector_performance[sector] = []
                    
                    # Get performance data
                    data = await analytics_engine._get_historical_data(symbol, "1m")
                    if data is not None and not data.empty:
                        performance = (data['Close'].iloc[-1] / data['Close'].iloc[0] - 1) * 100
                        sector_performance[sector].append(performance)
                
                except Exception as e:
                    logger.warning(f"Could not analyze sector performance for {symbol}: {e}")
                    continue
            
            # Calculate average performance by sector
            for sector, performances in sector_performance.items():
                if performances:
                    sector_performance[sector] = np.mean(performances)
        
        except Exception as e:
            logger.error(f"Error analyzing sector performance: {e}")
        
        return sector_performance
    
    def _determine_market_regime(self, symbols: List[str]) -> str:
        """Determine market regime"""
        # Simplified market regime detection
        return "bullish"  # Placeholder
    
    async def _analyze_volatility_regime(self, symbols: List[str]) -> str:
        """Analyze volatility regime"""
        try:
            volatilities = []
            for symbol in symbols:
                try:
                    data = await analytics_engine._get_historical_data(symbol, "1m")
                    if data is not None and not data.empty:
                        returns = data['Close'].pct_change().dropna()
                        volatility = returns.std() * np.sqrt(252)
                        volatilities.append(volatility)
                except Exception:
                    continue
            
            if volatilities:
                avg_volatility = np.mean(volatilities)
                if avg_volatility > 0.3:
                    return "high"
                elif avg_volatility < 0.15:
                    return "low"
                else:
                    return "medium"
        
        except Exception as e:
            logger.error(f"Error analyzing volatility regime: {e}")
        
        return "unknown"
    
    async def _analyze_correlation_regime(self, symbols: List[str]) -> str:
        """Analyze correlation regime"""
        try:
            if len(symbols) < 2:
                return "unknown"
            
            # Get price data for all symbols
            price_data = {}
            for symbol in symbols:
                try:
                    data = await analytics_engine._get_historical_data(symbol, "1m")
                    if data is not None and not data.empty:
                        price_data[symbol] = data['Close']
                except Exception:
                    continue
            
            if len(price_data) < 2:
                return "unknown"
            
            # Calculate correlations
            df = pd.DataFrame(price_data)
            returns = df.pct_change().dropna()
            correlation_matrix = returns.corr()
            
            # Calculate average correlation
            correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr = correlation_matrix.iloc[i, j]
                    if not np.isnan(corr):
                        correlations.append(abs(corr))
            
            if correlations:
                avg_correlation = np.mean(correlations)
                if avg_correlation > 0.7:
                    return "high"
                elif avg_correlation < 0.3:
                    return "low"
                else:
                    return "medium"
        
        except Exception as e:
            logger.error(f"Error analyzing correlation regime: {e}")
        
        return "unknown"
    
    async def _identify_key_drivers(self, symbols: List[str]) -> List[str]:
        """Identify key market drivers"""
        # Placeholder implementation
        return ["Earnings season", "Federal Reserve policy", "Economic data releases"]
    
    async def _identify_market_risks(self, symbols: List[str]) -> List[str]:
        """Identify market risks"""
        # Placeholder implementation
        return ["Geopolitical tensions", "Inflation concerns", "Interest rate uncertainty"]
    
    async def _identify_opportunities(self, symbols: List[str]) -> List[str]:
        """Identify market opportunities"""
        # Placeholder implementation
        return ["Sector rotation", "Value investing", "Emerging markets"]
    
    # Helper methods for data preparation
    def _prepare_price_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for price prediction"""
        try:
            # Calculate technical indicators
            returns = data['Close'].pct_change().dropna()
            
            features = []
            
            # Price-based features
            features.extend([
                returns.mean(),
                returns.std(),
                returns.skew(),
                returns.kurtosis()
            ])
            
            # Moving averages
            if len(data) >= 20:
                sma_20 = data['Close'].rolling(window=20).mean()
                features.append(data['Close'].iloc[-1] / sma_20.iloc[-1] - 1)
            else:
                features.append(0)
            
            if len(data) >= 50:
                sma_50 = data['Close'].rolling(window=50).mean()
                features.append(data['Close'].iloc[-1] / sma_50.iloc[-1] - 1)
            else:
                features.append(0)
            
            # RSI
            if len(data) >= 14:
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                features.append(rsi.iloc[-1] / 100)  # Normalize to 0-1
            else:
                features.append(0.5)
            
            # Volume features
            if 'Volume' in data.columns:
                volume_ratio = data['Volume'].iloc[-1] / data['Volume'].rolling(window=20).mean().iloc[-1]
                features.append(volume_ratio if not np.isnan(volume_ratio) else 1)
            else:
                features.append(1)
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error preparing price features: {e}")
            return np.zeros(8)  # Default feature vector
    
    def _prepare_clustering_features(self, data: pd.DataFrame) -> np.ndarray:
        """Prepare features for clustering"""
        try:
            returns = data['Close'].pct_change().dropna()
            
            features = [
                returns.mean(),
                returns.std(),
                returns.skew(),
                returns.kurtosis(),
                data['Close'].iloc[-1] / data['Close'].iloc[0] - 1,  # Total return
                len(returns[returns > 0]) / len(returns) if len(returns) > 0 else 0.5  # Win rate
            ]
            
            return np.array(features)
            
        except Exception as e:
            logger.error(f"Error preparing clustering features: {e}")
            return np.zeros(6)
    
    def _calculate_prediction_confidence(self, features: np.ndarray) -> float:
        """Calculate confidence in prediction"""
        # Simplified confidence calculation
        # In practice, this would use model uncertainty or ensemble methods
        return 0.7  # Placeholder confidence


# Global AI insights engine instance
ai_insights_engine = AIInsightsEngine() 