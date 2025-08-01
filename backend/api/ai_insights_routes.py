"""
AI Insights API Routes for Valor IVX Platform
Phase 9: Advanced Analytics and Machine Learning

This module provides API endpoints for:
- AI-powered insights generation
- Intelligent recommendations
- Predictive analytics
- Natural language processing
- Market intelligence
- Anomaly detection
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

from ..ai_insights_engine import ai_insights_engine, Insight, Recommendation, MarketIntelligence
from ..auth import auth_required
from ..rate_limiter import rate_limit
from ..middleware.tenant import tenant_required
from ..settings import settings

logger = logging.getLogger(__name__)

# Create blueprint
ai_insights_bp = Blueprint('ai_insights', __name__, url_prefix='/api/ai-insights')


# Pydantic schemas for request validation
class InsightsRequest(BaseModel):
    symbol: str
    analysis_types: Optional[List[str]] = None
    include_recommendations: bool = True


class RecommendationsRequest(BaseModel):
    symbol: str
    user_profile: Optional[Dict[str, Any]] = None
    recommendation_types: Optional[List[str]] = None


class MarketIntelligenceRequest(BaseModel):
    symbols: List[str]
    include_sector_analysis: bool = True
    include_regime_analysis: bool = True


class PricePredictionRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    confidence_level: float = 0.95


class AnomalyDetectionRequest(BaseModel):
    symbol: str
    data_type: str = "price"
    sensitivity: float = 0.1


class ClusteringRequest(BaseModel):
    symbols: List[str]
    n_clusters: Optional[int] = None
    features: Optional[List[str]] = None


class NaturalLanguageRequest(BaseModel):
    symbol: str
    summary_type: str = "comprehensive"  # comprehensive, technical, fundamental, sentiment


# API Routes
@ai_insights_bp.route("/insights", methods=["POST"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def generate_insights():
    """Generate AI-powered insights for a symbol"""
    try:
        data = request.get_json() or {}
        try:
            payload = InsightsRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Generate insights
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            insights = loop.run_until_complete(
                ai_insights_engine.generate_insights(
                    symbol=payload.symbol,
                    analysis_types=payload.analysis_types
                )
            )
            
            # Generate recommendations if requested
            recommendations = []
            if payload.include_recommendations:
                recommendations = loop.run_until_complete(
                    ai_insights_engine.generate_recommendations(payload.symbol)
                )
        finally:
            loop.close()
        
        # Convert insights to serializable format
        insights_data = []
        for insight in insights:
            insights_data.append({
                "insight_type": insight.insight_type,
                "symbol": insight.symbol,
                "confidence": insight.confidence,
                "description": insight.description,
                "recommendation": insight.recommendation,
                "reasoning": insight.reasoning,
                "data_points": insight.data_points,
                "priority": insight.priority,
                "timestamp": insight.timestamp.isoformat()
            })
        
        # Convert recommendations to serializable format
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                "recommendation_type": rec.recommendation_type,
                "symbol": rec.symbol,
                "action": rec.action,
                "confidence": rec.confidence,
                "target_price": rec.target_price,
                "stop_loss": rec.stop_loss,
                "time_horizon": rec.time_horizon,
                "reasoning": rec.reasoning,
                "risk_level": rec.risk_level,
                "timestamp": rec.timestamp.isoformat()
            })
        
        return jsonify({
            "success": True,
            "data": {
                "symbol": payload.symbol,
                "insights": insights_data,
                "recommendations": recommendations_data,
                "total_insights": len(insights),
                "total_recommendations": len(recommendations),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/recommendations", methods=["POST"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def generate_recommendations():
    """Generate AI-powered recommendations for a symbol"""
    try:
        data = request.get_json() or {}
        try:
            payload = RecommendationsRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Generate recommendations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            recommendations = loop.run_until_complete(
                ai_insights_engine.generate_recommendations(
                    symbol=payload.symbol,
                    user_profile=payload.user_profile
                )
            )
        finally:
            loop.close()
        
        # Convert to serializable format
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                "recommendation_type": rec.recommendation_type,
                "symbol": rec.symbol,
                "action": rec.action,
                "confidence": rec.confidence,
                "target_price": rec.target_price,
                "stop_loss": rec.stop_loss,
                "time_horizon": rec.time_horizon,
                "reasoning": rec.reasoning,
                "risk_level": rec.risk_level,
                "timestamp": rec.timestamp.isoformat()
            })
        
        return jsonify({
            "success": True,
            "data": {
                "symbol": payload.symbol,
                "recommendations": recommendations_data,
                "total_recommendations": len(recommendations),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/market-intelligence", methods=["POST"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def analyze_market_intelligence():
    """Analyze market intelligence across multiple symbols"""
    try:
        data = request.get_json() or {}
        try:
            payload = MarketIntelligenceRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Analyze market intelligence
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            market_intelligence = loop.run_until_complete(
                ai_insights_engine.analyze_market_intelligence(payload.symbols)
            )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": {
                "market_sentiment": market_intelligence.market_sentiment,
                "sector_performance": market_intelligence.sector_performance,
                "market_regime": market_intelligence.market_regime,
                "volatility_regime": market_intelligence.volatility_regime,
                "correlation_regime": market_intelligence.correlation_regime,
                "key_drivers": market_intelligence.key_drivers,
                "risks": market_intelligence.risks,
                "opportunities": market_intelligence.opportunities,
                "symbols_analyzed": len(payload.symbols),
                "timestamp": market_intelligence.timestamp.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing market intelligence: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/price-prediction", methods=["POST"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def predict_price_movement():
    """Predict price movement using AI models"""
    try:
        data = request.get_json() or {}
        try:
            payload = PricePredictionRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Make price prediction
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            prediction = loop.run_until_complete(
                ai_insights_engine.predict_price_movement(
                    symbol=payload.symbol,
                    timeframe=payload.timeframe
                )
        finally:
            loop.close()
        
        if "error" in prediction:
            return jsonify({"error": prediction["error"]}), 400
        
        return jsonify({
            "success": True,
            "data": prediction
        })
        
    except Exception as e:
        logger.error(f"Error predicting price movement: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/anomaly-detection", methods=["POST"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def detect_anomalies():
    """Detect anomalies in financial data"""
    try:
        data = request.get_json() or {}
        try:
            payload = AnomalyDetectionRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Detect anomalies
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            anomalies = loop.run_until_complete(
                ai_insights_engine.detect_anomalies(
                    symbol=payload.symbol,
                    data_type=payload.data_type
                )
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": {
                "symbol": payload.symbol,
                "data_type": payload.data_type,
                "anomalies": anomalies,
                "total_anomalies": len(anomalies),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/clustering", methods=["POST"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def cluster_assets():
    """Cluster similar assets using AI"""
    try:
        data = request.get_json() or {}
        try:
            payload = ClusteringRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Perform clustering
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            clusters = loop.run_until_complete(
                ai_insights_engine.cluster_similar_assets(payload.symbols)
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": {
                "clusters": clusters,
                "total_clusters": len(clusters),
                "symbols_analyzed": len(payload.symbols),
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error clustering assets: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/natural-language-summary", methods=["POST"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def generate_natural_language_summary():
    """Generate natural language summary of analysis"""
    try:
        data = request.get_json() or {}
        try:
            payload = NaturalLanguageRequest.model_validate(data)
        except ValidationError as e:
            return jsonify({"error": "ValidationError", "details": e.errors()}), 400
        
        # Generate summary
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            summary = loop.run_until_complete(
                ai_insights_engine.generate_natural_language_summary(payload.symbol)
        finally:
            loop.close()
        
        return jsonify({
            "success": True,
            "data": {
                "symbol": payload.symbol,
                "summary": summary,
                "summary_type": payload.summary_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating natural language summary: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/insights/batch", methods=["POST"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def generate_insights_batch():
    """Generate insights for multiple symbols in batch"""
    try:
        data = request.get_json() or {}
        symbols = data.get("symbols", [])
        analysis_types = data.get("analysis_types", ["technical", "fundamental", "sentiment", "risk"])
        
        if not symbols:
            return jsonify({"error": "No symbols provided"}), 400
        
        # Generate insights for all symbols
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tasks = []
            for symbol in symbols:
                task = ai_insights_engine.generate_insights(symbol, analysis_types)
                tasks.append(task)
            
            results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.close()
        
        # Process results
        insights_results = {}
        total_insights = 0
        
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                insights_results[symbol] = {"error": str(result)}
            else:
                insights_data = []
                for insight in result:
                    insights_data.append({
                        "insight_type": insight.insight_type,
                        "confidence": insight.confidence,
                        "description": insight.description,
                        "recommendation": insight.recommendation,
                        "priority": insight.priority,
                        "timestamp": insight.timestamp.isoformat()
                    })
                insights_results[symbol] = {"insights": insights_data}
                total_insights += len(result)
        
        return jsonify({
            "success": True,
            "data": {
                "results": insights_results,
                "total_symbols": len(symbols),
                "successful_analyses": len([r for r in results if not isinstance(r, Exception)]),
                "total_insights": total_insights,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating batch insights: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/recommendations/batch", methods=["POST"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def generate_recommendations_batch():
    """Generate recommendations for multiple symbols in batch"""
    try:
        data = request.get_json() or {}
        symbols = data.get("symbols", [])
        user_profile = data.get("user_profile")
        
        if not symbols:
            return jsonify({"error": "No symbols provided"}), 400
        
        # Generate recommendations for all symbols
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tasks = []
            for symbol in symbols:
                task = ai_insights_engine.generate_recommendations(symbol, user_profile)
                tasks.append(task)
            
            results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            loop.close()
        
        # Process results
        recommendations_results = {}
        total_recommendations = 0
        
        for i, result in enumerate(results):
            symbol = symbols[i]
            if isinstance(result, Exception):
                recommendations_results[symbol] = {"error": str(result)}
            else:
                recommendations_data = []
                for rec in result:
                    recommendations_data.append({
                        "recommendation_type": rec.recommendation_type,
                        "action": rec.action,
                        "confidence": rec.confidence,
                        "target_price": rec.target_price,
                        "stop_loss": rec.stop_loss,
                        "time_horizon": rec.time_horizon,
                        "risk_level": rec.risk_level,
                        "timestamp": rec.timestamp.isoformat()
                    })
                recommendations_results[symbol] = {"recommendations": recommendations_data}
                total_recommendations += len(result)
        
        return jsonify({
            "success": True,
            "data": {
                "results": recommendations_results,
                "total_symbols": len(symbols),
                "successful_analyses": len([r for r in results if not isinstance(r, Exception)]),
                "total_recommendations": total_recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating batch recommendations: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/insights/<symbol>", methods=["GET"])
@rate_limit("ai_insights")
@tenant_required
def get_cached_insights(symbol):
    """Get cached insights for a symbol"""
    try:
        # Get cached insights
        cached_insights = ai_insights_engine.insights_cache.get(symbol, [])
        
        # Convert to serializable format
        insights_data = []
        for insight in cached_insights:
            insights_data.append({
                "insight_type": insight.insight_type,
                "symbol": insight.symbol,
                "confidence": insight.confidence,
                "description": insight.description,
                "recommendation": insight.recommendation,
                "reasoning": insight.reasoning,
                "data_points": insight.data_points,
                "priority": insight.priority,
                "timestamp": insight.timestamp.isoformat()
            })
        
        return jsonify({
            "success": True,
            "data": {
                "symbol": symbol,
                "insights": insights_data,
                "total_insights": len(insights_data),
                "cached": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting cached insights for {symbol}: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/recommendations/<symbol>", methods=["GET"])
@rate_limit("ai_insights")
@tenant_required
def get_cached_recommendations(symbol):
    """Get cached recommendations for a symbol"""
    try:
        # Get cached recommendations
        cached_recommendations = ai_insights_engine.recommendations_cache.get(symbol, [])
        
        # Convert to serializable format
        recommendations_data = []
        for rec in cached_recommendations:
            recommendations_data.append({
                "recommendation_type": rec.recommendation_type,
                "symbol": rec.symbol,
                "action": rec.action,
                "confidence": rec.confidence,
                "target_price": rec.target_price,
                "stop_loss": rec.stop_loss,
                "time_horizon": rec.time_horizon,
                "reasoning": rec.reasoning,
                "risk_level": rec.risk_level,
                "timestamp": rec.timestamp.isoformat()
            })
        
        return jsonify({
            "success": True,
            "data": {
                "symbol": symbol,
                "recommendations": recommendations_data,
                "total_recommendations": len(recommendations_data),
                "cached": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting cached recommendations for {symbol}: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/metrics", methods=["GET"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def get_ai_metrics():
    """Get AI insights engine metrics"""
    try:
        metrics = {
            "insights_generated": ai_insights_engine.insights_generated,
            "recommendations_generated": ai_insights_engine.recommendations_generated,
            "accuracy_metrics": ai_insights_engine.accuracy_metrics,
            "cache_stats": {
                "insights_cache_size": len(ai_insights_engine.insights_cache),
                "recommendations_cache_size": len(ai_insights_engine.recommendations_cache)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return jsonify({
            "success": True,
            "data": metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting AI metrics: {e}")
        return jsonify({"error": str(e)}), 500


@ai_insights_bp.route("/clear-cache", methods=["POST"])
@auth_required
@rate_limit("ai_insights")
@tenant_required
def clear_cache():
    """Clear AI insights cache"""
    try:
        data = request.get_json() or {}
        symbol = data.get("symbol")
        
        if symbol:
            # Clear cache for specific symbol
            if symbol in ai_insights_engine.insights_cache:
                del ai_insights_engine.insights_cache[symbol]
            if symbol in ai_insights_engine.recommendations_cache:
                del ai_insights_engine.recommendations_cache[symbol]
            
            message = f"Cache cleared for {symbol}"
        else:
            # Clear all cache
            ai_insights_engine.insights_cache.clear()
            ai_insights_engine.recommendations_cache.clear()
            message = "All cache cleared"
        
        return jsonify({
            "success": True,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({"error": str(e)}), 500


# Health check endpoint
@ai_insights_bp.route("/health", methods=["GET"])
def health_check():
    """Health check for AI insights service"""
    return jsonify({
        "status": "healthy",
        "service": "ai_insights",
        "models_loaded": all([
            ai_insights_engine.price_predictor is not None,
            ai_insights_engine.anomaly_detector is not None,
            ai_insights_engine.clustering_model is not None
        ]),
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })


# Error handlers
@ai_insights_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "AI insights endpoint not found"}), 404


@ai_insights_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"AI insights internal error: {error}")
    return jsonify({"error": "Internal server error in AI insights"}), 500 