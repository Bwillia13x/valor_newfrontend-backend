"""
Advanced Analytics Engine for Valor IVX
Phase 7 Implementation

This module provides machine learning and advanced analytics capabilities:
- Predictive modeling for financial metrics
- Risk assessment and scoring
- Market trend analysis
- Anomaly detection
- Portfolio optimization
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Result of a prediction analysis"""
    predicted_value: float
    confidence_interval: Tuple[float, float]
    confidence_level: float
    model_accuracy: float
    features_importance: Dict[str, float]
    timestamp: datetime

@dataclass
class RiskAssessment:
    """Risk assessment result"""
    risk_score: float
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    risk_factors: List[str]
    recommendations: List[str]
    confidence: float

@dataclass
class MarketTrend:
    """Market trend analysis result"""
    trend_direction: str  # 'bullish', 'bearish', 'neutral'
    trend_strength: float
    trend_duration: int  # days
    support_level: float
    resistance_level: float
    confidence: float

class AnalyticsEngine:
    """Advanced analytics engine with machine learning capabilities"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance_cache = {}
        self.model_accuracy_cache = {}
        
        # Initialize models
        self._initialize_models()
        from ml_models.portfolio_optimizer import PortfolioOptimizer
        from ml_models.sentiment_analyzer import SentimentAnalyzer
    
    def _initialize_models(self):
        """Dynamically initialize machine learning models from the ml_models directory."""
        from ml_models.revenue_predictor import RevenuePredictor
        from ml_models.risk_assessor import RiskAssessor
        from ml_models.portfolio_optimizer import PortfolioOptimizer
        from ml_models.sentiment_analyzer import SentimentAnalyzer

        self.models = {
            'revenue': RevenuePredictor(),
            'risk': RiskAssessor(),
            'portfolio': PortfolioOptimizer(),
            'sentiment': SentimentAnalyzer(),
            'market_trend': LinearRegression()
        }
        
        # Initialize scalers
        self.scalers['revenue_prediction'] = StandardScaler()
        self.scalers['risk_assessment'] = StandardScaler()
        self.scalers['market_trend'] = StandardScaler()
        logger.info("Analytics models initialized: %s", list(self.models.keys()))
    
    def predict_revenue_growth(self, financial_data: Dict[str, Any], 
                             forecast_periods: int = 5) -> PredictionResult:
        """Predict revenue growth using machine learning"""
        try:
            # Extract features from financial data
            features = self._extract_revenue_features(financial_data)
            
            if len(features) < 10:  # Need minimum data points
                raise ValueError("Insufficient data for prediction")
            
            # Prepare training data
            X, y = self._prepare_revenue_training_data(features)
            
            if len(X) < 5:  # Need minimum training samples
                raise ValueError("Insufficient training data")
            
            # Train model
            model = self.models['revenue_prediction']
            scaler = self.scalers['revenue_prediction']
            
            X_scaled = scaler.fit_transform(X)
            model.fit(X_scaled, y)
            
            # Make prediction
            latest_features = features[-1]
            latest_scaled = scaler.transform([latest_features])
            prediction = model.predict(latest_scaled)[0]
            
            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(
                model, X_scaled, y, prediction
            )
            
            # Calculate model accuracy
            y_pred = model.predict(X_scaled)
            accuracy = r2_score(y, y_pred)
            
            # Get feature importance
            feature_names = ['revenue', 'ebit_margin', 'growth_rate', 'market_cap', 
                           'debt_ratio', 'cash_flow', 'roic', 'pe_ratio']
            importance = dict(zip(feature_names, model.feature_importances_))
            
            return PredictionResult(
                predicted_value=prediction,
                confidence_interval=confidence_interval,
                confidence_level=0.95,
                model_accuracy=accuracy,
                features_importance=importance,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error in revenue prediction: {str(e)}")
            raise
    
    def assess_risk(self, financial_data: Dict[str, Any]) -> RiskAssessment:
        """Assess financial risk using machine learning"""
        try:
            # Extract risk features
            risk_features = self._extract_risk_features(financial_data)
            
            if len(risk_features) < 5:
                raise ValueError("Insufficient data for risk assessment")
            
            # Prepare data
            X = np.array(risk_features).reshape(-1, 1)
            scaler = self.scalers['risk_assessment']
            X_scaled = scaler.fit_transform(X)
            
            # Train isolation forest for anomaly detection
            model = self.models['risk_assessment']
            model.fit(X_scaled)
            
            # Calculate risk score
            risk_scores = model.decision_function(X_scaled)
            avg_risk_score = np.mean(risk_scores)
            
            # Determine risk level
            risk_level = self._determine_risk_level(avg_risk_score)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(financial_data)
            
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(risk_level, risk_factors)
            
            # Calculate confidence
            confidence = self._calculate_risk_confidence(risk_scores)
            
            return RiskAssessment(
                risk_score=avg_risk_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                recommendations=recommendations,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error in risk assessment: {str(e)}")
            raise
    
    def analyze_market_trend(self, price_data: List[Dict[str, Any]], 
                           period: int = 30) -> MarketTrend:
        """Analyze market trends using machine learning"""
        try:
            if len(price_data) < period:
                raise ValueError(f"Insufficient price data. Need at least {period} data points")
            
            # Extract trend features
            trend_features = self._extract_trend_features(price_data, period)
            
            # Prepare training data
            X, y = self._prepare_trend_training_data(trend_features)
            
            if len(X) < 10:
                raise ValueError("Insufficient data for trend analysis")
            
            # Train model
            model = self.models['market_trend']
            scaler = self.scalers['market_trend']
            
            X_scaled = scaler.fit_transform(X)
            model.fit(X_scaled, y)
            
            # Make prediction
            latest_features = trend_features[-1]
            latest_scaled = scaler.transform([latest_features])
            trend_prediction = model.predict(latest_scaled)[0]
            
            # Determine trend direction and strength
            trend_direction = self._determine_trend_direction(trend_prediction)
            trend_strength = abs(trend_prediction)
            
            # Calculate support and resistance levels
            support_level, resistance_level = self._calculate_support_resistance(price_data)
            
            # Calculate trend duration
            trend_duration = self._calculate_trend_duration(price_data, trend_direction)
            
            # Calculate confidence
            confidence = self._calculate_trend_confidence(model, X_scaled, y)
            
            return MarketTrend(
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                trend_duration=trend_duration,
                support_level=support_level,
                resistance_level=resistance_level,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error in market trend analysis: {str(e)}")
            raise
    
    def optimize_portfolio(self, assets: List[Dict[str, Any]], 
                          target_return: float = 0.10,
                          risk_tolerance: float = 0.15) -> Dict[str, Any]:
        """Optimize portfolio allocation using modern portfolio theory"""
        try:
            if len(assets) < 2:
                raise ValueError("Need at least 2 assets for portfolio optimization")
            
            # Extract asset data
            asset_data = self._extract_portfolio_data(assets)
            
            # Calculate expected returns and covariance matrix
            expected_returns = self._calculate_expected_returns(asset_data)
            covariance_matrix = self._calculate_covariance_matrix(asset_data)
            
            # Optimize portfolio weights
            optimal_weights = self._optimize_portfolio_weights(
                expected_returns, covariance_matrix, target_return, risk_tolerance
            )
            
            # Calculate portfolio metrics
            portfolio_return = np.sum(expected_returns * optimal_weights)
            portfolio_risk = np.sqrt(
                optimal_weights.T @ covariance_matrix @ optimal_weights
            )
            sharpe_ratio = portfolio_return / portfolio_risk if portfolio_risk > 0 else 0
            
            return {
                'weights': dict(zip([asset['symbol'] for asset in assets], optimal_weights)),
                'expected_return': portfolio_return,
                'expected_risk': portfolio_risk,
                'sharpe_ratio': sharpe_ratio,
                'diversification_ratio': self._calculate_diversification_ratio(
                    optimal_weights, covariance_matrix
                ),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {str(e)}")
            raise
    
    def detect_anomalies(self, financial_data: List[Dict[str, Any]], 
                        metric: str = 'revenue') -> List[Dict[str, Any]]:
        """Detect anomalies in financial data"""
        try:
            # Extract metric data
            metric_data = [data.get(metric, 0) for data in financial_data]
            
            if len(metric_data) < 10:
                raise ValueError("Insufficient data for anomaly detection")
            
            # Prepare data for anomaly detection
            X = np.array(metric_data).reshape(-1, 1)
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train isolation forest
            anomaly_model = IsolationForest(contamination=0.1, random_state=42)
            anomaly_model.fit(X_scaled)
            
            # Detect anomalies
            anomaly_scores = anomaly_model.decision_function(X_scaled)
            anomaly_predictions = anomaly_model.predict(X_scaled)
            
            # Identify anomalies
            anomalies = []
            for i, (score, prediction) in enumerate(zip(anomaly_scores, anomaly_predictions)):
                if prediction == -1:  # Anomaly detected
                    anomalies.append({
                        'index': i,
                        'value': metric_data[i],
                        'score': score,
                        'severity': 'high' if score < -0.5 else 'medium',
                        'timestamp': financial_data[i].get('timestamp', ''),
                        'metric': metric
                    })
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
            raise
    
    def _extract_revenue_features(self, financial_data: Dict[str, Any]) -> List[List[float]]:
        """Extract features for revenue prediction"""
        features = []
        
        # Extract historical data
        revenue_history = financial_data.get('revenue_history', [])
        ebit_history = financial_data.get('ebit_history', [])
        
        for i in range(len(revenue_history) - 1):
            feature_vector = [
                revenue_history[i],
                ebit_history[i] / revenue_history[i] if revenue_history[i] > 0 else 0,
                (revenue_history[i+1] - revenue_history[i]) / revenue_history[i] if revenue_history[i] > 0 else 0,
                financial_data.get('market_cap', 0),
                financial_data.get('total_debt', 0) / financial_data.get('total_assets', 1),
                financial_data.get('operating_cash_flow', 0),
                financial_data.get('roic', 0),
                financial_data.get('pe_ratio', 0)
            ]
            features.append(feature_vector)
        
        return features
    
    def _extract_risk_features(self, financial_data: Dict[str, Any]) -> List[float]:
        """Extract features for risk assessment"""
        return [
            financial_data.get('debt_to_equity', 0),
            financial_data.get('current_ratio', 0),
            financial_data.get('quick_ratio', 0),
            financial_data.get('interest_coverage', 0),
            financial_data.get('cash_flow_coverage', 0),
            financial_data.get('asset_turnover', 0),
            financial_data.get('inventory_turnover', 0),
            financial_data.get('days_sales_outstanding', 0)
        ]
    
    def _extract_trend_features(self, price_data: List[Dict[str, Any]], period: int) -> List[List[float]]:
        """Extract features for trend analysis"""
        features = []
        
        for i in range(period, len(price_data)):
            prices = [p['close'] for p in price_data[i-period:i]]
            volumes = [p.get('volume', 0) for p in price_data[i-period:i]]
            
            feature_vector = [
                np.mean(prices),
                np.std(prices),
                (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0,
                np.mean(volumes),
                np.std(volumes),
                len([p for p in prices if p > np.mean(prices)]) / len(prices)
            ]
            features.append(feature_vector)
        
        return features
    
    def _prepare_revenue_training_data(self, features: List[List[float]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for revenue prediction"""
        X = np.array(features[:-1])  # Features
        y = np.array([f[2] for f in features[1:]])  # Growth rate as target
        return X, y
    
    def _prepare_trend_training_data(self, features: List[List[float]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for trend analysis"""
        X = np.array(features[:-1])
        y = np.array([f[2] for f in features[1:]])  # Price change as target
        return X, y
    
    def _calculate_confidence_interval(self, model, X, y, prediction) -> Tuple[float, float]:
        """Calculate confidence interval for prediction"""
        # Simple confidence interval calculation
        y_pred = model.predict(X)
        mse = mean_squared_error(y, y_pred)
        std_error = np.sqrt(mse)
        
        confidence_interval = (
            prediction - 1.96 * std_error,
            prediction + 1.96 * std_error
        )
        
        return confidence_interval
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on risk score"""
        if risk_score > 0.5:
            return 'low'
        elif risk_score > 0:
            return 'medium'
        elif risk_score > -0.5:
            return 'high'
        else:
            return 'critical'
    
    def _identify_risk_factors(self, financial_data: Dict[str, Any]) -> List[str]:
        """Identify specific risk factors"""
        risk_factors = []
        
        if financial_data.get('debt_to_equity', 0) > 2:
            risk_factors.append('High debt-to-equity ratio')
        
        if financial_data.get('current_ratio', 0) < 1:
            risk_factors.append('Low current ratio')
        
        if financial_data.get('interest_coverage', 0) < 2:
            risk_factors.append('Low interest coverage')
        
        if financial_data.get('cash_flow_coverage', 0) < 1.5:
            risk_factors.append('Low cash flow coverage')
        
        return risk_factors
    
    def _generate_risk_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if risk_level in ['high', 'critical']:
            recommendations.append('Consider reducing debt levels')
            recommendations.append('Improve cash flow management')
            recommendations.append('Strengthen working capital position')
        
        if 'High debt-to-equity ratio' in risk_factors:
            recommendations.append('Focus on debt reduction strategies')
        
        if 'Low current ratio' in risk_factors:
            recommendations.append('Improve short-term liquidity')
        
        return recommendations
    
    def _calculate_risk_confidence(self, risk_scores: np.ndarray) -> float:
        """Calculate confidence in risk assessment"""
        return 1 - np.std(risk_scores)  # Higher consistency = higher confidence
    
    def _determine_trend_direction(self, prediction: float) -> str:
        """Determine trend direction from prediction"""
        if prediction > 0.02:
            return 'bullish'
        elif prediction < -0.02:
            return 'bearish'
        else:
            return 'neutral'
    
    def _calculate_support_resistance(self, price_data: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Calculate support and resistance levels"""
        prices = [p['close'] for p in price_data]
        
        # Simple support/resistance calculation
        support_level = np.percentile(prices, 25)
        resistance_level = np.percentile(prices, 75)
        
        return support_level, resistance_level
    
    def _calculate_trend_duration(self, price_data: List[Dict[str, Any]], direction: str) -> int:
        """Calculate trend duration in days"""
        # Simple trend duration calculation
        return len(price_data) // 4  # Approximate duration
    
    def _calculate_trend_confidence(self, model, X, y) -> float:
        """Calculate confidence in trend analysis"""
        y_pred = model.predict(X)
        return r2_score(y, y_pred)
    
    def _extract_portfolio_data(self, assets: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Extract portfolio data for optimization"""
        portfolio_data = {}
        
        for asset in assets:
            symbol = asset['symbol']
            returns = asset.get('returns', [])
            if returns:
                portfolio_data[symbol] = returns
        
        return portfolio_data
    
    def _calculate_expected_returns(self, asset_data: Dict[str, List[float]]) -> np.ndarray:
        """Calculate expected returns for assets"""
        expected_returns = []
        
        for symbol, returns in asset_data.items():
            if returns:
                expected_return = np.mean(returns)
                expected_returns.append(expected_return)
            else:
                expected_returns.append(0.05)  # Default return
        
        return np.array(expected_returns)
    
    def _calculate_covariance_matrix(self, asset_data: Dict[str, List[float]]) -> np.ndarray:
        """Calculate covariance matrix for assets"""
        # Align return series
        min_length = min(len(returns) for returns in asset_data.values()) if asset_data else 0
        
        if min_length < 2:
            # Return identity matrix if insufficient data
            n_assets = len(asset_data)
            return np.eye(n_assets) * 0.1
        
        aligned_returns = []
        for symbol, returns in asset_data.items():
            aligned_returns.append(returns[-min_length:])
        
        returns_matrix = np.array(aligned_returns).T
        return np.cov(returns_matrix, rowvar=False)
    
    def _optimize_portfolio_weights(self, expected_returns: np.ndarray, 
                                  covariance_matrix: np.ndarray,
                                  target_return: float, risk_tolerance: float) -> np.ndarray:
        """Optimize portfolio weights using modern portfolio theory"""
        n_assets = len(expected_returns)
        
        # Simple optimization: equal weight with target return constraint
        weights = np.ones(n_assets) / n_assets
        
        # Adjust weights to meet target return
        current_return = np.sum(expected_returns * weights)
        if current_return < target_return:
            # Increase weights for higher return assets
            high_return_indices = np.argsort(expected_returns)[-n_assets//2:]
            weights[high_return_indices] *= 1.2
            weights /= np.sum(weights)  # Normalize
        
        return weights
    
    def _calculate_diversification_ratio(self, weights: np.ndarray, 
                                       covariance_matrix: np.ndarray) -> float:
        """Calculate portfolio diversification ratio"""
        portfolio_variance = weights.T @ covariance_matrix @ weights
        weighted_asset_variance = np.sum(weights * np.diag(covariance_matrix))
        
        if weighted_asset_variance > 0:
            return portfolio_variance / weighted_asset_variance
        else:
            return 1.0
    
    def save_model(self, model_name: str, filepath: str):
        """Save trained model to file"""
        if model_name in self.models:
            joblib.dump(self.models[model_name], filepath)
            logger.info(f"Model {model_name} saved to {filepath}")
    
    def load_model(self, model_name: str, filepath: str):
        """Load trained model from file"""
        try:
            self.models[model_name] = joblib.load(filepath)
            logger.info(f"Model {model_name} loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {str(e)}")
    
    def get_model_statistics(self) -> Dict[str, Any]:
        """Get analytics engine statistics"""
        return {
            'total_models': len(self.models),
            'model_names': list(self.models.keys()),
            'cache_size': len(self.feature_importance_cache),
            'timestamp': datetime.utcnow().isoformat()
        }

    def predict(self, model_name: str, data: Dict[str, Any]) -> Any:
        """Unified prediction method for all models."""
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found.")

        model = self.models[model_name]
        
        # Each model should have a 'predict' method that takes the data dict
        if hasattr(model, 'predict') and callable(getattr(model, 'predict')):
            return model.predict(data)
        else:
            # Fallback for sklearn-like models that don't have a custom predict method
            # This part may need customization based on the model's expected input format
            if 'features' in data:
                features = np.array(data['features']).reshape(1, -1)
                return model.predict(features)
            else:
                raise NotImplementedError(f"Prediction for model '{model_name}' is not implemented in the unified engine.")
