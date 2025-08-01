"""
Analytics API Routes for Valor IVX
Phase 8 Implementation - Advanced Analytics and Enterprise Features

This module provides comprehensive analytics endpoints that integrate all ML models:
- Revenue prediction
- Risk assessment
- Portfolio optimization
- Sentiment analysis
- Market trend analysis
- Anomaly detection
"""

from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

# Import analytics engine and ML models
from analytics_engine import AnalyticsEngine
from ml_models.revenue_predictor import RevenuePredictor
from ml_models.risk_assessor import RiskAssessor
from ml_models.portfolio_optimizer import PortfolioOptimizer
from ml_models.sentiment_analyzer import SentimentAnalyzer
from ml_models.credit_risk import CreditRiskModel
from ml_models.real_options import RealOptionsModel
from ml_models.risk_management import RiskManagementModel

# Import RBAC for multi-tenant support
from models.rbac import RBACManager, Permission

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

# Initialize analytics engine and RBAC manager
analytics_engine = AnalyticsEngine()
rbac_manager = RBACManager()

# Initialize ML models
revenue_predictor = RevenuePredictor()
risk_assessor = RiskAssessor()
portfolio_optimizer = PortfolioOptimizer()
sentiment_analyzer = SentimentAnalyzer()
credit_risk_model = CreditRiskModel()
real_options_model = RealOptionsModel()
risk_management_model = RiskManagementModel()

@analytics_bp.route('/health', methods=['GET'])
def analytics_health():
    """Health check for analytics services"""
    try:
        # Check all ML models
        model_status = {
            'revenue_predictor': hasattr(revenue_predictor, 'predict'),
            'risk_assessor': hasattr(risk_assessor, 'assess'),
            'portfolio_optimizer': hasattr(portfolio_optimizer, 'optimize'),
            'sentiment_analyzer': hasattr(sentiment_analyzer, 'analyze'),
            'credit_risk_model': hasattr(credit_risk_model, 'assess'),
            'real_options_model': hasattr(real_options_model, 'value'),
            'risk_management_model': hasattr(risk_management_model, 'manage')
        }
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'models': model_status,
            'analytics_engine': analytics_engine.get_model_statistics()
        }), 200
    except Exception as e:
        logger.error(f"Analytics health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@analytics_bp.route('/revenue/predict', methods=['POST'])
def predict_revenue():
    """Predict revenue growth using ML models"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract financial data
        financial_data = data.get('financial_data', {})
        forecast_periods = data.get('forecast_periods', 5)
        
        # Validate required data
        required_fields = ['revenue_history', 'ebit_history']
        for field in required_fields:
            if field not in financial_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Use analytics engine for prediction
        prediction_result = analytics_engine.predict_revenue_growth(
            financial_data, forecast_periods
        )
        
        # Also use dedicated revenue predictor
        ml_prediction = revenue_predictor.predict(financial_data)
        
        result = {
            'predicted_growth_rate': prediction_result.predicted_value,
            'confidence_interval': prediction_result.confidence_interval,
            'confidence_level': prediction_result.confidence_level,
            'model_accuracy': prediction_result.model_accuracy,
            'feature_importance': prediction_result.features_importance,
            'ml_prediction': ml_prediction,
            'timestamp': prediction_result.timestamp.isoformat(),
            'forecast_periods': forecast_periods
        }
        
        # Emit real-time update if WebSocket is available
        try:
            from websocket_manager import socketio
            socketio.emit('analytics_update', {
                'type': 'revenue_prediction',
                'data': result
            })
        except:
            pass
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Revenue prediction failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/risk/assess', methods=['POST'])
def assess_risk():
    """Comprehensive risk assessment using multiple ML models"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        financial_data = data.get('financial_data', {})
        risk_type = data.get('risk_type', 'comprehensive')  # comprehensive, credit, market, operational
        
        results = {}
        
        # Use analytics engine for general risk assessment
        if risk_type in ['comprehensive', 'general']:
            risk_assessment = analytics_engine.assess_risk(financial_data)
            results['general_risk'] = {
                'risk_score': risk_assessment.risk_score,
                'risk_level': risk_assessment.risk_level,
                'risk_factors': risk_assessment.risk_factors,
                'recommendations': risk_assessment.recommendations,
                'confidence': risk_assessment.confidence
            }
        
        # Use dedicated risk assessor
        if risk_type in ['comprehensive', 'operational']:
            operational_risk = risk_assessor.assess(financial_data)
            results['operational_risk'] = operational_risk
        
        # Use credit risk model
        if risk_type in ['comprehensive', 'credit']:
            credit_risk = credit_risk_model.assess(financial_data)
            results['credit_risk'] = credit_risk
        
        # Use risk management model
        if risk_type in ['comprehensive', 'management']:
            risk_management = risk_management_model.manage(financial_data)
            results['risk_management'] = risk_management
        
        result = {
            'risk_assessment': results,
            'timestamp': datetime.utcnow().isoformat(),
            'risk_type': risk_type
        }
        
        # Emit real-time update
        try:
            from websocket_manager import socketio
            socketio.emit('analytics_update', {
                'type': 'risk_assessment',
                'data': result
            })
        except:
            pass
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/portfolio/optimize', methods=['POST'])
def optimize_portfolio():
    """Optimize portfolio allocation using ML models"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        assets = data.get('assets', [])
        target_return = data.get('target_return', 0.10)
        risk_tolerance = data.get('risk_tolerance', 0.15)
        optimization_method = data.get('method', 'modern_portfolio_theory')
        
        if len(assets) < 2:
            return jsonify({'error': 'Need at least 2 assets for optimization'}), 400
        
        results = {}
        
        # Use analytics engine for portfolio optimization
        analytics_optimization = analytics_engine.optimize_portfolio(
            assets, target_return, risk_tolerance
        )
        results['analytics_optimization'] = analytics_optimization
        
        # Use dedicated portfolio optimizer
        portfolio_optimization = portfolio_optimizer.optimize({
            'assets': assets,
            'target_return': target_return,
            'risk_tolerance': risk_tolerance,
            'method': optimization_method
        })
        results['portfolio_optimization'] = portfolio_optimization
        
        result = {
            'portfolio_optimization': results,
            'timestamp': datetime.utcnow().isoformat(),
            'method': optimization_method
        }
        
        # Emit real-time update
        try:
            from websocket_manager import socketio
            socketio.emit('analytics_update', {
                'type': 'portfolio_optimization',
                'data': result
            })
        except:
            pass
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Portfolio optimization failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/sentiment/analyze', methods=['POST'])
def analyze_sentiment():
    """Analyze market sentiment using ML models"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        text_data = data.get('text_data', [])
        news_data = data.get('news_data', [])
        social_data = data.get('social_data', [])
        
        if not any([text_data, news_data, social_data]):
            return jsonify({'error': 'No text, news, or social data provided'}), 400
        
        results = {}
        
        # Analyze text sentiment
        if text_data:
            text_sentiment = sentiment_analyzer.analyze(text_data)
            results['text_sentiment'] = text_sentiment
        
        # Analyze news sentiment
        if news_data:
            news_sentiment = sentiment_analyzer.analyze(news_data)
            results['news_sentiment'] = news_sentiment
        
        # Analyze social media sentiment
        if social_data:
            social_sentiment = sentiment_analyzer.analyze(social_data)
            results['social_sentiment'] = social_sentiment
        
        # Calculate overall sentiment score
        sentiment_scores = []
        for sentiment_data in results.values():
            if isinstance(sentiment_data, dict) and 'score' in sentiment_data:
                sentiment_scores.append(sentiment_data['score'])
        
        overall_sentiment = {
            'score': np.mean(sentiment_scores) if sentiment_scores else 0,
            'confidence': np.std(sentiment_scores) if sentiment_scores else 0,
            'sources': len(results)
        }
        
        result = {
            'sentiment_analysis': results,
            'overall_sentiment': overall_sentiment,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Emit real-time update
        try:
            from websocket_manager import socketio
            socketio.emit('analytics_update', {
                'type': 'sentiment_analysis',
                'data': result
            })
        except:
            pass
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/market/trend', methods=['POST'])
def analyze_market_trend():
    """Analyze market trends using ML models"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        price_data = data.get('price_data', [])
        period = data.get('period', 30)
        
        if len(price_data) < period:
            return jsonify({'error': f'Insufficient price data. Need at least {period} data points'}), 400
        
        # Use analytics engine for trend analysis
        trend_analysis = analytics_engine.analyze_market_trend(price_data, period)
        
        result = {
            'trend_direction': trend_analysis.trend_direction,
            'trend_strength': trend_analysis.trend_strength,
            'trend_duration': trend_analysis.trend_duration,
            'support_level': trend_analysis.support_level,
            'resistance_level': trend_analysis.resistance_level,
            'confidence': trend_analysis.confidence,
            'timestamp': datetime.utcnow().isoformat(),
            'period': period
        }
        
        # Emit real-time update
        try:
            from websocket_manager import socketio
            socketio.emit('analytics_update', {
                'type': 'market_trend',
                'data': result
            })
        except:
            pass
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Market trend analysis failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/anomalies/detect', methods=['POST'])
def detect_anomalies():
    """Detect anomalies in financial data"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        financial_data = data.get('financial_data', [])
        metric = data.get('metric', 'revenue')
        threshold = data.get('threshold', 0.1)
        
        if len(financial_data) < 10:
            return jsonify({'error': 'Insufficient data for anomaly detection'}), 400
        
        # Use analytics engine for anomaly detection
        anomalies = analytics_engine.detect_anomalies(financial_data, metric)
        
        result = {
            'anomalies': anomalies,
            'total_anomalies': len(anomalies),
            'metric': metric,
            'threshold': threshold,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Emit real-time update
        try:
            from websocket_manager import socketio
            socketio.emit('analytics_update', {
                'type': 'anomaly_detection',
                'data': result
            })
        except:
            pass
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/real-options/value', methods=['POST'])
def value_real_options():
    """Value real options using ML models"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        project_data = data.get('project_data', {})
        option_type = data.get('option_type', 'expand')  # expand, abandon, defer, switch
        
        # Use real options model
        option_value = real_options_model.value({
            'project_data': project_data,
            'option_type': option_type
        })
        
        result = {
            'option_value': option_value,
            'option_type': option_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Emit real-time update
        try:
            from websocket_manager import socketio
            socketio.emit('analytics_update', {
                'type': 'real_options_valuation',
                'data': result
            })
        except:
            pass
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Real options valuation failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/comprehensive', methods=['POST'])
def comprehensive_analysis():
    """Perform comprehensive financial analysis using all ML models"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        financial_data = data.get('financial_data', {})
        assets = data.get('assets', [])
        text_data = data.get('text_data', [])
        price_data = data.get('price_data', [])
        
        results = {}
        
        # Revenue prediction
        try:
            revenue_prediction = analytics_engine.predict_revenue_growth(financial_data)
            results['revenue_prediction'] = {
                'predicted_growth_rate': revenue_prediction.predicted_value,
                'confidence_interval': revenue_prediction.confidence_interval,
                'model_accuracy': revenue_prediction.model_accuracy
            }
        except Exception as e:
            results['revenue_prediction'] = {'error': str(e)}
        
        # Risk assessment
        try:
            risk_assessment = analytics_engine.assess_risk(financial_data)
            results['risk_assessment'] = {
                'risk_score': risk_assessment.risk_score,
                'risk_level': risk_assessment.risk_level,
                'risk_factors': risk_assessment.risk_factors,
                'recommendations': risk_assessment.recommendations
            }
        except Exception as e:
            results['risk_assessment'] = {'error': str(e)}
        
        # Portfolio optimization
        if assets:
            try:
                portfolio_optimization = analytics_engine.optimize_portfolio(assets)
                results['portfolio_optimization'] = portfolio_optimization
            except Exception as e:
                results['portfolio_optimization'] = {'error': str(e)}
        
        # Sentiment analysis
        if text_data:
            try:
                sentiment_analysis = sentiment_analyzer.analyze(text_data)
                results['sentiment_analysis'] = sentiment_analysis
            except Exception as e:
                results['sentiment_analysis'] = {'error': str(e)}
        
        # Market trend analysis
        if price_data:
            try:
                market_trend = analytics_engine.analyze_market_trend(price_data)
                results['market_trend'] = {
                    'trend_direction': market_trend.trend_direction,
                    'trend_strength': market_trend.trend_strength,
                    'support_level': market_trend.support_level,
                    'resistance_level': market_trend.resistance_level
                }
            except Exception as e:
                results['market_trend'] = {'error': str(e)}
        
        # Anomaly detection
        try:
            anomalies = analytics_engine.detect_anomalies([financial_data])
            results['anomaly_detection'] = {
                'anomalies': anomalies,
                'total_anomalies': len(anomalies)
            }
        except Exception as e:
            results['anomaly_detection'] = {'error': str(e)}
        
        result = {
            'comprehensive_analysis': results,
            'timestamp': datetime.utcnow().isoformat(),
            'models_used': list(results.keys())
        }
        
        # Emit real-time update
        try:
            from websocket_manager import socketio
            socketio.emit('analytics_update', {
                'type': 'comprehensive_analysis',
                'data': result
            })
        except:
            pass
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/models/status', methods=['GET'])
def get_models_status():
    """Get status of all ML models"""
    try:
        model_status = {
            'revenue_predictor': {
                'status': 'active' if hasattr(revenue_predictor, 'predict') else 'inactive',
                'type': 'regression',
                'description': 'Predicts revenue growth based on financial metrics'
            },
            'risk_assessor': {
                'status': 'active' if hasattr(risk_assessor, 'assess') else 'inactive',
                'type': 'classification',
                'description': 'Assesses operational and financial risks'
            },
            'portfolio_optimizer': {
                'status': 'active' if hasattr(portfolio_optimizer, 'optimize') else 'inactive',
                'type': 'optimization',
                'description': 'Optimizes portfolio allocation using modern portfolio theory'
            },
            'sentiment_analyzer': {
                'status': 'active' if hasattr(sentiment_analyzer, 'analyze') else 'inactive',
                'type': 'nlp',
                'description': 'Analyzes market sentiment from text data'
            },
            'credit_risk_model': {
                'status': 'active' if hasattr(credit_risk_model, 'assess') else 'inactive',
                'type': 'classification',
                'description': 'Assesses credit risk and default probability'
            },
            'real_options_model': {
                'status': 'active' if hasattr(real_options_model, 'value') else 'inactive',
                'type': 'valuation',
                'description': 'Values real options using option pricing models'
            },
            'risk_management_model': {
                'status': 'active' if hasattr(risk_management_model, 'manage') else 'inactive',
                'type': 'management',
                'description': 'Provides risk management strategies and recommendations'
            }
        }
        
        return jsonify({
            'models': model_status,
            'analytics_engine': analytics_engine.get_model_statistics(),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get models status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    """Get key metrics for analytics dashboard"""
    try:
        # Get model statistics
        model_stats = analytics_engine.get_model_statistics()
        
        # Calculate dashboard metrics
        metrics = {
            'total_models': model_stats['total_models'],
            'active_models': len([m for m in model_stats['model_names'] if m]),
            'cache_size': model_stats['cache_size'],
            'last_updated': model_stats['timestamp'],
            'system_health': 'healthy',
            'performance_score': 95.5  # Mock performance score
        }
        
        return jsonify({
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500 