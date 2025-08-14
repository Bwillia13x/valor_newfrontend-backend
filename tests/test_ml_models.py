"""
Comprehensive test suite for Phase 2 ML Models
Tests revenue prediction, risk assessment, and analytics engine
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ml_models.revenue_predictor import RevenuePredictor
from ml_models.risk_assessor import RiskAssessor
from ml_models.portfolio_optimizer import PortfolioOptimizer
from ml_models.sentiment_analyzer import SentimentAnalyzer
from analytics_engine import AnalyticsEngine

class MLModelsTestSuite:
    """Test suite for Phase 2 ML models and analytics engine"""
    
    def __init__(self):
        self.test_results = []
        self.revenue_predictor = RevenuePredictor()
        self.risk_assessor = RiskAssessor()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.analytics_engine = AnalyticsEngine()
    
    def run_all_tests(self):
        """Run all ML model tests"""
        print("🧪 Starting Phase 2 ML Models Test Suite...")
        
        self.test_revenue_prediction()
        self.test_risk_assessment()
        self.test_portfolio_optimization()
        self.test_sentiment_analysis()
        self.test_analytics_engine()
        self.test_model_accuracy()
        self.test_performance()
        self.test_edge_cases()
        
        self.print_results()
    
    def test_revenue_prediction(self):
        """Test revenue prediction model"""
        print("Testing Revenue Prediction Model...")
        
        # Create test data
        historical_data = pd.DataFrame({
            'revenue_growth': [0.05, 0.08, 0.12, 0.15, 0.10, 0.07, 0.09],
            'ebitda_margin': [0.20, 0.22, 0.25, 0.28, 0.24, 0.21, 0.23],
            'market_cap': [1000000, 1200000, 1500000, 1800000, 1600000, 1400000, 1700000],
            'industry_avg_growth': [0.04, 0.06, 0.08, 0.10, 0.07, 0.05, 0.09],
            'economic_indicators': [1.0, 1.1, 1.2, 1.3, 1.1, 1.0, 1.2],
            'future_revenue': [1050000, 1080000, 1120000, 1150000, 1100000, 1070000, 1090000]
        })
        
        # Train model
        self.revenue_predictor.train(historical_data)
        
        # Test prediction
        current_data = pd.DataFrame({
            'revenue_growth': [0.11],
            'ebitda_margin': [0.26],
            'market_cap': [1750000],
            'industry_avg_growth': [0.085],
            'economic_indicators': [1.25]
        })
        
        prediction = self.revenue_predictor.predict(current_data)
        
        self.assert_is_number(
            prediction[0],
            'Revenue Prediction',
            'Should return numeric prediction'
        )
        
        self.assert_greater_than(
            prediction[0],
            1000000,
            'Revenue Prediction',
            'Should predict reasonable revenue value'
        )
    
    def test_risk_assessment(self):
        """Test risk assessment models"""
        print("Testing Risk Assessment Models...")
        
        # Test credit risk
        credit_data = pd.DataFrame({
            'debt_to_equity': [0.5, 1.2, 2.1, 0.8, 1.5],
            'interest_coverage': [5.0, 3.2, 1.8, 4.5, 2.5],
            'leverage_ratio': [0.3, 0.6, 0.9, 0.4, 0.7]
        })
        
        credit_labels = pd.Series(['low', 'medium', 'high', 'low', 'medium'])
        
        self.risk_assessor.train_credit_model(
            pd.concat([credit_data, credit_labels.rename('credit_risk')], axis=1)
        )
        
        # Test credit risk prediction
        test_credit = pd.DataFrame({
            'debt_to_equity': [1.0],
            'interest_coverage': [3.5],
            'leverage_ratio': [0.5]
        })
        
        credit_risk = self.risk_assessor.assess_credit_risk(test_credit)
        
        self.assert_is_array(
            credit_risk,
            'Risk Assessment',
            'Should return credit risk probabilities'
        )
        
        # Test market risk
        market_data = pd.DataFrame({
            'volatility': [0.15, 0.25, 0.35, 0.20, 0.30],
            'liquidity_ratio': [1.5, 2.0, 1.2, 1.8, 1.4],
            'market_cap': [1000000, 2000000, 500000, 1500000, 800000]
        })
        
        market_labels = pd.Series(['low', 'medium', 'high', 'medium', 'high'])
        
        self.risk_assessor.train_market_model(
            pd.concat([market_data, market_labels.rename('market_risk')], axis=1)
        )
        
        test_market = pd.DataFrame({
            'volatility': [0.22],
            'liquidity_ratio': [1.6],
            'market_cap': [1200000]
        })
        
        market_risk = self.risk_assessor.assess_market_risk(test_market)
        
        self.assert_is_string(
            market_risk[0],
            'Risk Assessment',
            'Should return market risk classification'
        )
    
    def test_portfolio_optimization(self):
        """Test portfolio optimization model"""
        print("Testing Portfolio Optimization...")
        
        assets = [
            {
                'symbol': 'AAPL',
                'returns': [0.05, 0.08, -0.02, 0.12, 0.07, 0.09, 0.11],
                'volatility': 0.15,
                'expected_return': 0.08
            },
            {
                'symbol': 'GOOGL',
                'returns': [0.03, 0.06, 0.01, 0.09, 0.04, 0.07, 0.05],
                'volatility': 0.12,
                'expected_return': 0.06
            },
            {
                'symbol': 'MSFT',
                'returns': [0.04, 0.07, 0.00, 0.10, 0.05, 0.08, 0.06],
                'volatility': 0.13,
                'expected_return': 0.07
            }
        ]
        
        result = self.portfolio_optimizer.optimize(assets)
        
        self.assert_is_dict(
            result,
            'Portfolio Optimization',
            'Should return optimization result'
        )
        
        self.assert_in(
            'weights',
            result,
            'Portfolio Optimization',
            'Should include portfolio weights'
        )
        
        self.assert_in(
            'expected_return',
            result,
            'Portfolio Optimization',
            'Should include expected return'
        )
        
        self.assert_in(
            'expected_risk',
            result,
            'Portfolio Optimization',
            'Should include expected risk'
        )
        
        # Check weights sum to 1
        total_weight = sum(result['weights'].values())
        self.assert_almost_equal(
            total_weight,
            1.0,
            0.01,
            'Portfolio Optimization',
            'Weights should sum to 1'
        )
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis model"""
        print("Testing Sentiment Analysis...")
        
        texts = [
            "The company reported strong earnings growth this quarter",
            "Revenue declined significantly due to market conditions",
            "Management provided optimistic guidance for next year",
            "The stock price dropped after disappointing results"
        ]
        
        sentiments = self.sentiment_analyzer.analyze(texts)
        
        self.assert_is_list(
            sentiments,
            'Sentiment Analysis',
            'Should return sentiment list'
        )
        
        self.assert_equal(
            len(sentiments),
            len(texts),
            'Sentiment Analysis',
            'Should return sentiment for each text'
        )
        
        for sentiment in sentiments:
            self.assert_in(
                sentiment['sentiment'],
                ['positive', 'negative', 'neutral'],
                'Sentiment Analysis',
                'Should classify sentiment correctly'
            )
    
    def test_analytics_engine(self):
        """Test analytics engine integration"""
        print("Testing Analytics Engine...")
        
        # Test revenue prediction
        financial_data = {
            'revenue_history': [1000000, 1050000, 1100000, 1150000, 1200000],
            'ebit_history': [200000, 210000, 220000, 230000, 240000],
            'market_cap': 15000000,
            'total_debt': 2000000,
            'total_assets': 8000000,
            'operating_cash_flow': 300000,
            'roic': 0.15,
            'pe_ratio': 20
        }
        
        prediction = self.analytics_engine.predict_revenue_growth(
            financial_data,
            forecast_periods=3
        )
        
        self.assert_is_number(
            prediction.predicted_value,
            'Analytics Engine',
            'Should return numeric revenue prediction'
        )
        
        self.assert_greater_than(
            prediction.model_accuracy,
            0.7,
            'Analytics Engine',
            'Should achieve reasonable model accuracy'
        )
        
        # Test risk assessment
        risk_data = {
            'debt_to_equity': 0.5,
            'current_ratio': 1.5,
            'quick_ratio': 1.2,
            'interest_coverage': 4.0,
            'cash_flow_coverage': 2.5,
            'asset_turnover': 1.1,
            'inventory_turnover': 5.2,
            'days_sales_outstanding': 35
        }
        
        risk_assessment = self.analytics_engine.assess_risk(risk_data)
        
        self.assert_is_string(
            risk_assessment.risk_level,
            'Analytics Engine',
            'Should return risk level'
        )
        
        self.assert_in(
            risk_assessment.risk_level,
            ['low', 'medium', 'high', 'critical'],
            'Analytics Engine',
            'Should classify risk correctly'
        )
    
    def test_model_accuracy(self):
        """Test model accuracy metrics"""
        print("Testing Model Accuracy...")
        
        # Test revenue prediction accuracy
        historical_data = pd.DataFrame({
            'revenue_growth': [0.05, 0.08, 0.12, 0.15, 0.10, 0.07, 0.09, 0.11, 0.13, 0.08],
            'ebitda_margin': [0.20, 0.22, 0.25, 0.28, 0.24, 0.21, 0.23, 0.26, 0.27, 0.24],
            'market_cap': [1000000, 1200000, 1500000, 1800000, 1600000, 1400000, 1700000, 1900000, 2000000, 1750000],
            'industry_avg_growth': [0.04, 0.06, 0.08, 0.10, 0.07, 0.05, 0.09, 0.11, 0.10, 0.08],
            'economic_indicators': [1.0, 1.1, 1.2, 1.3, 1.1, 1.0, 1.2, 1.3, 1.4, 1.2],
            'future_revenue': [1050000, 1080000, 1120000, 1150000, 1100000, 1070000, 1090000, 1110000, 1130000, 1100000]
        })
        
        # Split data for training and testing
        train_data = historical_data.iloc[:7]
        test_data = historical_data.iloc[7:]
        
        self.revenue_predictor.train(train_data)
        
        # Test on unseen data
        predictions = []
        actuals = []
        
        for idx, row in test_data.iterrows():
            current_data = pd.DataFrame({
                'revenue_growth': [row['revenue_growth']],
                'ebitda_margin': [row['ebitda_margin']],
                'market_cap': [row['market_cap']],
                'industry_avg_growth': [row['industry_avg_growth']],
                'economic_indicators': [row['economic_indicators']]
            })
            
            prediction = self.revenue_predictor.predict(current_data)[0]
            actual = row['future_revenue']
            
            predictions.append(prediction)
            actuals.append(actual)
        
        # Calculate accuracy metrics
        mae = np.mean(np.abs(np.array(predictions) - np.array(actuals)))
        mape = np.mean(np.abs((np.array(predictions) - np.array(actuals)) / np.array(actuals))) * 100
        
        self.assert_less_than(
            mape,
            15,
            'Model Accuracy',
            f'Should achieve MAPE < 15% (actual: {mape:.2f}%)'
        )
    
    def test_performance(self):
        """Test model performance and speed"""
        print("Testing Performance...")
        
        # Test prediction speed
        import time
        
        # Create large dataset
        large_data = pd.DataFrame({
            'revenue_growth': np.random.normal(0.1, 0.05, 1000),
            'ebitda_margin': np.random.normal(0.25, 0.1, 1000),
            'market_cap': np.random.normal(1500000, 500000, 1000),
            'industry_avg_growth': np.random.normal(0.08, 0.03, 1000),
            'economic_indicators': np.random.normal(1.2, 0.2, 1000),
            'future_revenue': np.random.normal(1100000, 200000, 1000)
        })
        
        # Train model
        start_time = time.time()
        self.revenue_predictor.train(large_data)
        train_time = time.time() - start_time
        
        self.assert_less_than(
            train_time,
            5.0,
            'Performance',
            f'Training should complete in < 5 seconds (actual: {train_time:.2f}s)'
        )
        
        # Test prediction speed
        test_data = pd.DataFrame({
            'revenue_growth': [0.11],
            'ebitda_margin': [0.26],
            'market_cap': [1750000],
            'industry_avg_growth': [0.085],
            'economic_indicators': [1.25]
        })
        
        start_time = time.time()
        for _ in range(100):
            _ = self.revenue_predictor.predict(test_data)
        predict_time = time.time() - start_time
        
        self.assert_less_than(
            predict_time,
            1.0,
            'Performance',
            f'100 predictions should complete in < 1 second (actual: {predict_time:.2f}s)'
        )
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("Testing Edge Cases...")
        
        # Test with empty data
        empty_data = pd.DataFrame({
            'revenue_growth': [],
            'ebitda_margin': [],
            'market_cap': [],
            'industry_avg_growth': [],
            'economic_indicators': [],
            'future_revenue': []
        })
        
        try:
            self.revenue_predictor.train(empty_data)
            self.fail("Should raise error for empty data")
        except ValueError:
            self.pass_test('Edge Cases', 'Should handle empty training data')
        
        # Test with missing features
        incomplete_data = pd.DataFrame({
            'revenue_growth': [0.1],
            'ebitda_margin': [0.25],
            'market_cap': [1000000]
            # Missing other features
        })
        
        try:
            _ = self.revenue_predictor.predict(incomplete_data)
            self.fail("Should raise error for missing features")
        except KeyError:
            self.pass_test('Edge Cases', 'Should handle missing features')
        
        # Test with extreme values
        extreme_data = pd.DataFrame({
            'revenue_growth': [1000],  # Extremely high
            'ebitda_margin': [-50],  # Negative
            'market_cap': [1],       # Extremely low
            'industry_avg_growth': [0.08],
            'economic_indicators': [1.2]
        })
        
        prediction = self.revenue_predictor.predict(extreme_data)
        self.assert_is_number(
            prediction[0],
            'Edge Cases',
            'Should handle extreme values gracefully'
        )
    
    # Helper assertion methods
    def assert_equal(self, actual, expected, test_name, message):
        """Assert equality"""
        if actual == expected:
            self.pass_test(test_name, message)
        else:
            self.fail_test(test_name, f"{message} - Expected: {expected}, Actual: {actual}")
    
    def assert_is_number(self, value, test_name, message):
        """Assert value is numeric"""
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            self.pass_test(test_name, message)
        else:
            self.fail_test(test_name, f"{message} - Expected number, got: {type(value)}")
    
    def assert_is_string(self, value, test_name, message):
        """Assert value is string"""
        if isinstance(value, str):
            self.pass_test(test_name, message)
        else:
            self.fail_test(test_name, f"{message} - Expected string, got: {type(value)}")
    
    def assert_is_list(self, value, test_name, message):
        """Assert value is list"""
        if isinstance(value, list):
            self.pass_test(test_name, message)
        else:
            self.fail_test(test_name, f"{message} - Expected list, got: {type(value)}")
    
    def assert_is_dict(self, value, test_name, message):
        """Assert value is dict"""
        if isinstance(value, dict):
            self.pass_test(test_name, message)
        else:
            self.fail_test(test_name, f"{message} - Expected dict, got: {type(value)}")
    
    def assert_is_array(self, value, test_name, message):
        """Assert value is array-like"""
        if hasattr(value, '__array__') or isinstance(value, (list, tuple)):
            self.pass_test(test_name, message)
        else:
            self.fail_test(test_name, f"{message} - Expected array, got: {type(value)}")
    
    def assert_in(self, value, container, test_name, message):
        """Assert value is in container"""
        if value in container:
            self.pass_test(test_name, message)
        else:
            self.fail_test(test_name, f"{message} - {value} not in {container}")
    
    def assert_greater_than(self, value, threshold, test_name, message):
        """Assert value is greater than threshold"""
        if value > threshold:
            self.pass_test(test_name, message)
        else:
            self.fail_test(test_name, f"{message} - {value} <= {threshold}")
    
    def assert_less_than(self, value, threshold, test_name, message):
        """Assert value is less than threshold"""
        if value < threshold:
            self.pass_test(test_name, message)
        else:
            self.fail_test(test_name, f"{message} - {value} >= {threshold}")
    
    def assert_almost_equal(self, actual, expected, tolerance, test_name, message):
        """Assert values are almost equal within tolerance"""
        if abs(actual - expected) <= tolerance:
            self.pass_test(test_name, message)
        else:
            self.fail_test(test_name, f"{message} - Expected ~{expected}, got {actual}")
    
    def pass_test(self, test_name, message):
        """Record passing test"""
        self.test_results.append({
            'test_name': test_name,
            'message': message,
            'passed': True,
            'timestamp': datetime.now().isoformat()
        })
        print(f"✅ {test_name}: {message}")
    
    def fail_test(self, test_name, message):
        """Record failing test"""
        self.test_results.append({
            'test_name': test_name,
            'message': message,
            'passed': False,
            'timestamp': datetime.now().isoformat()
        })
        print(f"❌ {test_name}: {message}")
    
    def print_results(self):
        """Print test results summary"""
        print("\n📊 ML Models Test Results Summary:")
        print("=================================")
        
        passed = len([r for r in self.test_results if r['passed']])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {((passed / total) * 100):.1f}%")
        
        if passed == total:
            print("🎉 All ML model tests passed!")
        else:
            print("⚠️ Some tests failed. Check the detailed output above.")

if __name__ == "__main__":
    test_suite = MLModelsTestSuite()
    test_suite.run_all_tests()
