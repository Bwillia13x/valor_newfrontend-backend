"""
Advanced Analytics API Routes for Valor IVX Platform
Phase 9: Advanced Analytics and Machine Learning

This module provides API endpoints for:
- Real-time market analysis
- Sentiment analysis
- Risk modeling and assessment
- Portfolio optimization
- Performance analytics
- Predictive analytics
- Business intelligence
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, g
from pydantic import BaseModel, ValidationError
import pandas as pd
import numpy as np

from ..analytics_engine import analytics_engine, MarketSignal, RiskMetrics, SentimentAnalysis
from ..auth import auth_required
from ..rate_limiter import rate_limit
from ..middleware.tenant import tenant_required
from ..settings import settings

logger = logging.getLogger(__name__)

# Create blueprint
advanced_analytics_bp = Blueprint('advanced_analytics', __name__, url_prefix='/api/advanced-analytics')


# Pydantic schemas for request validation
class SentimentAnalysisRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    include_sources: Optional[List[str]] = None


class RiskAnalysisRequest(BaseModel):
    portfolio_data: Dict[str, Any]
    historical_data: Optional[List[Dict[str, Any]]] = None
    risk_metrics: Optional[List[str]] = None


class PortfolioOptimizationRequest(BaseModel):
    assets: List[str]
    constraints: Dict[str, Any]
    optimization_method: str = "efficient_frontier"
    risk_free_rate: float = 0.02


class MarketSignalsRequest(BaseModel):
    symbol: str
    indicators: Optional[List[str]] = None
    timeframe: str = "1d"


class RevenuePredictionRequest(BaseModel):
    company_data: Dict[str, Any]
    forecast_periods: int = 12
    confidence_level: float = 0.95


class PerformanceAnalyticsRequest(BaseModel):
    portfolio_data: Dict[str, Any]
    benchmark: Optional[str] = "SPY"
    include_attribution: bool = True


class RealTimeDashboardRequest(BaseModel):
    symbols: List[str]
    include_alerts: bool = True
    include_sentiment: bool = True


class AnomalyDetectionRequest(BaseModel):
    data: List[Dict[str, Any]]
    detection_method: str = "isolation_forest"
    sensitivity: float = 0.1


# API Routes
@advanced_analytics_bp.route("/sentiment", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def analyze_sentiment():
    """Analyze market sentiment for a given symbol"""
    try:
        data = request.get_json() or {}
        try:
            payload = SentimentAnalysisRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Run sentiment analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            sentiment_result = loop.run_until_complete(
                analytics_engine.analyze_market_sentiment(
                    symbol=payload.symbol,
                    timeframe=payload.timeframe
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": {
                "symbol": payload.symbol,
                "sentiment": sentiment_result.overall_sentiment,
                "sentiment_score": sentiment_result.sentiment_score,
                "confidence": sentiment_result.confidence,
                "sources": sentiment_result.sources,
                "keywords": sentiment_result.keywords,
                "breakdown": sentiment_result.breakdown,
                "timestamp": sentiment_result.timestamp.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/risk-analysis", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def analyze_risk():
    """Perform comprehensive risk analysis"""
    try:
        data = request.get_json() or {}
        try:
            payload = RiskAnalysisRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Convert historical data to DataFrame if provided
        historical_data = None
        if payload.historical_data:
            historical_data = pd.DataFrame(payload.historical_data)
        
        # Run risk analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            risk_metrics = loop.run_until_complete(
                analytics_engine.calculate_risk_metrics(
                    portfolio_data=payload.portfolio_data,
                    historical_data=historical_data
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": {
                "var_95": risk_metrics.var_95,
                "var_99": risk_metrics.var_99,
                "expected_shortfall": risk_metrics.expected_shortfall,
                "volatility": risk_metrics.volatility,
                "beta": risk_metrics.beta,
                "sharpe_ratio": risk_metrics.sharpe_ratio,
                "sortino_ratio": risk_metrics.sortino_ratio,
                "max_drawdown": risk_metrics.max_drawdown,
                "correlation_matrix": risk_metrics.correlation_matrix.tolist(),
                "stress_test_results": risk_metrics.stress_test_results
            }
        })
        
    except Exception as e:
        logger.error(f"Error in risk analysis: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/market-signals", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def generate_market_signals():
    """Generate trading signals based on technical indicators"""
    try:
        data = request.get_json() or {}
        try:
            payload = MarketSignalsRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Generate market signals
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            signals = loop.run_until_complete(
                analytics_engine.generate_market_signals(
                    symbol=payload.symbol,
                    indicators=payload.indicators
                )
            )
        finally:
            loop.close()
        
        # Convert signals to serializable format
        signals_data = []
        for signal in signals:
            signals_data.append({
                "symbol": signal.symbol,
                "signal_type": signal.signal_type,
                "confidence": signal.confidence,
                "strength": signal.strength,
                "timestamp": signal.timestamp.isoformat(),
                "indicators": signal.indicators,
                "description": signal.description
            })
        
        return jsonify({
            "success": True,
            "data": {
                "symbol": payload.symbol,
                "signals": signals_data,
                "total_signals": len(signals_data),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating market signals: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/portfolio-optimization", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def optimize_portfolio():
    """Optimize portfolio allocation using advanced algorithms"""
    try:
        data = request.get_json() or {}
        try:
            payload = PortfolioOptimizationRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Run portfolio optimization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            optimization_result = loop.run_until_complete(
                analytics_engine.optimize_portfolio(
                    assets=payload.assets,
                    constraints=payload.constraints
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": {
                "weights": optimization_result["weights"],
                "expected_return": optimization_result["expected_return"],
                "volatility": optimization_result["volatility"],
                "sharpe_ratio": optimization_result["sharpe_ratio"],
                "assets": optimization_result["assets"],
                "optimization_method": optimization_result["optimization_method"],
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in portfolio optimization: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/revenue-prediction", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def predict_revenue():
    """Predict company revenue using ML models"""
    try:
        data = request.get_json() or {}
        try:
            payload = RevenuePredictionRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Run revenue prediction
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            prediction_result = loop.run_until_complete(
                analytics_engine.predict_revenue(
                    company_data=payload.company_data,
                    forecast_periods=payload.forecast_periods
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": {
                "predictions": prediction_result["predictions"],
                "confidence_intervals": prediction_result["confidence_intervals"],
                "forecast_periods": prediction_result["forecast_periods"],
                "model_confidence": prediction_result["model_confidence"],
                "last_updated": prediction_result["last_updated"]
            }
        })
        
    except Exception as e:
        logger.error(f"Error in revenue prediction: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/performance-analytics", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def run_performance_analytics():
    """Run comprehensive performance analytics"""
    try:
        data = request.get_json() or {}
        try:
            payload = PerformanceAnalyticsRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Run performance analytics
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            performance_result = loop.run_until_complete(
                analytics_engine.run_performance_analytics(
                    portfolio_data=payload.portfolio_data
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": performance_result
        })
        
    except Exception as e:
        logger.error(f"Error in performance analytics: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/real-time-dashboard", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def create_real_time_dashboard():
    """Create real-time dashboard data for multiple symbols"""
    try:
        data = request.get_json() or {}
        try:
            payload = RealTimeDashboardRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Create real-time dashboard
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            dashboard_data = loop.run_until_complete(
                analytics_engine.create_real_time_dashboard(
                    symbols=payload.symbols
                )
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error creating real-time dashboard: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/anomaly-detection", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def detect_anomalies():
    """Detect anomalies in financial data"""
    try:
        data = request.get_json() or {}
        try:
            payload = AnomalyDetectionRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Convert data to DataFrame
        df = pd.DataFrame(payload.data)
        
        # Detect anomalies using isolation forest
        from sklearn.ensemble import IsolationForest
        
        # Prepare features (assuming numeric columns)
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) == 0:
            return jsonify({"error": "No numeric columns found for anomaly detection"}), 400
        
        features = df[numeric_columns].fillna(0)
        
        # Fit isolation forest
        iso_forest = IsolationForest(
            contamination=payload.sensitivity,
            random_state=42
        )
        anomaly_scores = iso_forest.fit_predict(features)
        
        # Identify anomalies
        anomalies = df[anomaly_scores == -1]
        normal_data = df[anomaly_scores == 1]
        
        return jsonify({
            "success": True,
            "data": {
                "anomalies": anomalies.to_dict('records'),
                "normal_data": normal_data.to_dict('records'),
                "anomaly_count": len(anomalies),
                "total_count": len(df),
                "anomaly_percentage": len(anomalies) / len(df) * 100,
                "detection_method": payload.detection_method,
                "sensitivity": payload.sensitivity,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in anomaly detection: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/sentiment/batch", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def analyze_sentiment_batch():
    """Analyze sentiment for multiple symbols in batch"""
    try:
        data = request.get_json() or {}
        symbols = data.get("symbols", [])
        timeframe = data.get("timeframe", "1d")
        
        if not symbols:
            return jsonify({"error": "No symbols provided"}), 400
        
        # Run batch sentiment analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tasks = []
            for symbol in symbols:
                task = analytics_engine.analyze_market_sentiment(symbol, timeframe)
                tasks.append(task)
            
            results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.close()
        
        # Process results
        sentiment_results = {}
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                sentiment_results[symbol] = {"error": str(result)}
            else:
                sentiment_results[symbol] = {
                    "sentiment": result.overall_sentiment,
                    "confidence": result.confidence,
                    "keywords": result.keywords,
                    "timestamp": result.timestamp.isoformat()
                }
        
        return jsonify({
            "success": True,
            "data": {
                "results": sentiment_results,
                "total_symbols": len(symbols),
                "successful_analyses": len([r for r in results if not isinstance(r, Exception)]),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in batch sentiment analysis: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/market-overview", methods=["GET"])
@rate_limit("analytics")
@tenant_required
def get_market_overview():
    """Get market overview data"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            market_overview = loop.run_until_complete(
                analytics_engine._get_market_overview()
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": market_overview
        })
        
    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/alerts", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def generate_alerts():
    """Generate alerts for symbols"""
    try:
        data = request.get_json() or {}
        symbols = data.get("symbols", [])
        
        if not symbols:
            return jsonify({"error": "No symbols provided"}), 400
        
        # Generate alerts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            alerts = loop.run_until_complete(
                analytics_engine._generate_alerts(symbols)
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": {
                "alerts": alerts,
                "total_alerts": len(alerts),
                "symbols_monitored": len(symbols),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating alerts: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/technical-indicators/<symbol>", methods=["GET"])
@rate_limit("analytics")
@tenant_required
def get_technical_indicators(symbol):
    """Get technical indicators for a symbol"""
    try:
        timeframe = request.args.get("timeframe", "1y")
        
        # Get historical data
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            historical_data = loop.run_until_complete(
                analytics_engine._get_historical_data(symbol, timeframe)
            )
        finally:
            loop.close()
        
        if historical_data is None or historical_data.empty:
            return jsonify({"error": "No data available for symbol"}), 404
        
        # Calculate technical indicators
        indicators = {}
        
        # RSI
        if len(historical_data) >= 14:
            delta = historical_data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            indicators["rsi"] = rsi.iloc[-1]
        
        # Moving Averages
        if len(historical_data) >= 20:
            indicators["sma_20"] = historical_data['Close'].rolling(window=20).mean().iloc[-1]
        if len(historical_data) >= 50:
            indicators["sma_50"] = historical_data['Close'].rolling(window=50).mean().iloc[-1]
        if len(historical_data) >= 200:
            indicators["sma_200"] = historical_data['Close'].rolling(window=200).mean().iloc[-1]
        
        # MACD
        if len(historical_data) >= 26:
            exp1 = historical_data['Close'].ewm(span=12).mean()
            exp2 = historical_data['Close'].ewm(span=26).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=9).mean()
            indicators["macd"] = macd.iloc[-1]
            indicators["macd_signal"] = signal.iloc[-1]
            indicators["macd_histogram"] = (macd - signal).iloc[-1]
        
        # Bollinger Bands
        if len(historical_data) >= 20:
            sma = historical_data['Close'].rolling(window=20).mean()
            std = historical_data['Close'].rolling(window=20).std()
            upper_band = sma + (std * 2)
            lower_band = sma - (std * 2)
            indicators["bb_upper"] = upper_band.iloc[-1]
            indicators["bb_middle"] = sma.iloc[-1]
            indicators["bb_lower"] = lower_band.iloc[-1]
            indicators["bb_width"] = (upper_band - lower_band).iloc[-1] / sma.iloc[-1]
        
        # Volume indicators
        if len(historical_data) >= 20:
            indicators["volume_sma"] = historical_data['Volume'].rolling(window=20).mean().iloc[-1]
            indicators["volume_ratio"] = historical_data['Volume'].iloc[-1] / indicators["volume_sma"]
        
        return jsonify({
            "success": True,
            "data": {
                "symbol": symbol,
                "indicators": indicators,
                "current_price": historical_data['Close'].iloc[-1],
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting technical indicators for {symbol}: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/correlation-matrix", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def calculate_correlation_matrix():
    """Calculate correlation matrix for multiple assets"""
    try:
        data = request.get_json() or {}
        symbols = data.get("symbols", [])
        timeframe = data.get("timeframe", "1y")
        
        if len(symbols) < 2:
            return jsonify({"error": "At least 2 symbols required"}), 400
        
        # Get historical data for all symbols
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tasks = []
            for symbol in symbols:
                task = analytics_engine._get_historical_data(symbol, timeframe)
                tasks.append(task)
            
            results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.close()
        
        # Process results and calculate correlations
        price_data = {}
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                continue
            if result is not None and not result.empty:
                price_data[symbol] = result['Close']
        
        if len(price_data) < 2:
            return jsonify({"error": "Insufficient data for correlation analysis"}), 400
        
        # Create DataFrame and calculate correlations
        df = pd.DataFrame(price_data)
        returns = df.pct_change().dropna()
        correlation_matrix = returns.corr()
        
        return jsonify({
            "success": True,
            "data": {
                "symbols": list(correlation_matrix.columns),
                "correlation_matrix": correlation_matrix.values.tolist(),
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating correlation matrix: {e}")
        return jsonify({"error": str(e)}), 500


@advanced_analytics_bp.route("/volatility-analysis", methods=["POST"])
@auth_required
@rate_limit("analytics")
@tenant_required
def analyze_volatility():
    """Analyze volatility patterns for assets"""
    try:
        data = request.get_json() or {}
        symbols = data.get("symbols", [])
        timeframe = data.get("timeframe", "1y")
        window = data.get("window", 30)
        
        if not symbols:
            return jsonify({"error": "No symbols provided"}), 400
        
        # Get historical data
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tasks = []
            for symbol in symbols:
                task = analytics_engine._get_historical_data(symbol, timeframe)
                tasks.append(task)
            
            results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.close()
        
        # Analyze volatility
        volatility_analysis = {}
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                volatility_analysis[symbol] = {"error": str(result)}
                continue
            
            if result is not None and not result.empty:
                returns = result['Close'].pct_change().dropna()
                
                # Calculate rolling volatility
                rolling_vol = returns.rolling(window=window).std() * np.sqrt(252)
                
                volatility_analysis[symbol] = {
                    "current_volatility": rolling_vol.iloc[-1] if not rolling_vol.empty else None,
                    "avg_volatility": rolling_vol.mean(),
                    "volatility_trend": rolling_vol.iloc[-10:].tolist() if len(rolling_vol) >= 10 else [],
                    "volatility_percentile": (rolling_vol.iloc[-1] / rolling_vol.max() * 100) if not rolling_vol.empty else None
                }
        
        return jsonify({
            "success": True,
            "data": {
                "volatility_analysis": volatility_analysis,
                "window": window,
                "timeframe": timeframe,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing volatility: {e}")
        return jsonify({"error": str(e)}), 500


# Health check endpoint
@advanced_analytics_bp.route("/health", methods=["GET"])
def health_check():
    """Health check for advanced analytics service"""
    return jsonify({
        "status": "healthy",
        "service": "advanced_analytics",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })


# Error handlers
@advanced_analytics_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Advanced analytics endpoint not found"}), 404


@advanced_analytics_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Advanced analytics internal error: {error}")
    return jsonify({"error": "Internal server error in advanced analytics"}), 500 