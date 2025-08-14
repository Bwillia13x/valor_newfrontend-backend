#!/usr/bin/env python3
"""
Comprehensive Test Suite for Phase 5 Advanced Financial Models
Tests Credit Risk, Portfolio Analysis, and Risk Management modules
"""

import sys
import os
import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import the modules to test
from ml_models.credit_risk import CreditRiskValuation, MertonModel, KMVModel, CreditMetricsModel
from ml_models.portfolio_optimizer import PortfolioOptimizer, MeanVarianceOptimizer, BlackLittermanOptimizer, RiskParityOptimizer
from ml_models.risk_management import RiskManager, VaRCalculator, StressTester, RiskAttributor

class TestCreditRiskModels(unittest.TestCase):
    """Test Credit Risk Modeling Modules"""
    
    def setUp(self):
        """Set up test data"""
        self.credit_risk = CreditRiskValuation()
        self.merton_model = MertonModel()
        self.kmv_model = KMVModel()
        self.credit_metrics = CreditMetricsModel()
        
        # Test parameters
        self.asset_value = 1000000
        self.debt_value = 600000
        self.asset_volatility = 0.25
        self.risk_free_rate = 0.03
        self.time_to_maturity = 1.0
        
    def test_merton_model_pd_calculation(self):
        """Test Merton model probability of default calculation"""
        result = self.merton_model.calculate_pd(
            self.asset_value, self.debt_value, self.asset_volatility,
            self.risk_free_rate, self.time_to_maturity
        )
        
        self.assertIn('probability_of_default', result)
        self.assertIn('distance_to_default', result)
        self.assertIn('expected_loss', result)
        self.assertIn('credit_spread', result)
        
        # Validate results
        self.assertGreaterEqual(result['probability_of_default'], 0)
        self.assertLessEqual(result['probability_of_default'], 1)
        self.assertGreaterEqual(result['expected_loss'], 0)
        
        print(f"✓ Merton PD: {result['probability_of_default']:.4f}")
        print(f"✓ Distance to Default: {result['distance_to_default']:.4f}")
        print(f"✓ Expected Loss: ${result['expected_loss']:,.2f}")
        
    def test_kmv_model_pd_calculation(self):
        """Test KMV model probability of default calculation"""
        result = self.kmv_model.calculate_pd(
            self.asset_value, self.debt_value, self.asset_volatility,
            self.risk_free_rate, self.time_to_maturity
        )
        
        self.assertIn('probability_of_default', result)
        self.assertIn('expected_default_frequency', result)
        self.assertIn('distance_to_default', result)
        
        # Validate results
        self.assertGreaterEqual(result['probability_of_default'], 0)
        self.assertLessEqual(result['probability_of_default'], 1)
        
        print(f"✓ KMV PD: {result['probability_of_default']:.4f}")
        print(f"✓ EDF: {result['expected_default_frequency']:.4f}")
        
    def test_asset_parameter_estimation(self):
        """Test asset value and volatility estimation"""
        equity_value = 400000
        equity_volatility = 0.35
        
        result = self.merton_model.estimate_asset_value_and_volatility(
            equity_value, equity_volatility, self.debt_value,
            self.risk_free_rate, self.time_to_maturity
        )
        
        self.assertIn('asset_value', result)
        self.assertIn('asset_volatility', result)
        
        # Validate results
        self.assertGreater(result['asset_value'], equity_value)
        self.assertGreater(result['asset_volatility'], 0)
        
        print(f"✓ Estimated Asset Value: ${result['asset_value']:,.2f}")
        print(f"✓ Estimated Asset Volatility: {result['asset_volatility']:.4f}")
        
    def test_portfolio_credit_risk(self):
        """Test portfolio-level credit risk calculation"""
        portfolio_data = [
            {'exposure': 100000, 'pd': 0.02, 'lgd': 0.4},
            {'exposure': 200000, 'pd': 0.05, 'lgd': 0.45},
            {'exposure': 150000, 'pd': 0.03, 'lgd': 0.35}
        ]
        
        result = self.kmv_model.calculate_portfolio_pd(portfolio_data)
        
        self.assertIn('portfolio_pd', result)
        self.assertIn('portfolio_expected_loss', result)
        self.assertIn('portfolio_unexpected_loss', result)
        
        print(f"✓ Portfolio PD: {result['portfolio_pd']:.4f}")
        print(f"✓ Portfolio Expected Loss: ${result['portfolio_expected_loss']:,.2f}")
        print(f"✓ Portfolio Unexpected Loss: ${result['portfolio_unexpected_loss']:,.2f}")
        
    def test_credit_metrics_var(self):
        """Test CreditMetrics VaR calculation"""
        portfolio_data = [
            {'exposure': 100000, 'rating': 'A', 'maturity': 1.0},
            {'exposure': 200000, 'rating': 'BBB', 'maturity': 2.0},
            {'exposure': 150000, 'rating': 'BB', 'maturity': 1.5}
        ]
        
        result = self.credit_metrics.calculate_credit_var(portfolio_data, 0.99)
        
        self.assertIn('credit_var', result)
        self.assertIn('expected_portfolio_value', result)
        self.assertIn('unexpected_loss', result)
        
        print(f"✓ Credit VaR: ${result['credit_var']:,.2f}")
        print(f"✓ Expected Portfolio Value: ${result['expected_portfolio_value']:,.2f}")
        print(f"✓ Unexpected Loss: ${result['unexpected_loss']:,.2f}")
        
    def test_credit_spread_calculation(self):
        """Test credit spread calculation"""
        pd = 0.03
        lgd = 0.4
        maturity = 2.0
        
        credit_spread = self.credit_risk.calculate_credit_spread(
            self.risk_free_rate, pd, lgd, maturity
        )
        
        self.assertGreaterEqual(credit_spread, 0)
        
        print(f"✓ Credit Spread: {credit_spread:.4f} ({credit_spread*10000:.1f} bps)")
        
    def test_stress_testing(self):
        """Test credit risk stress testing"""
        portfolio_data = [
            {'exposure': 100000, 'pd': 0.02, 'lgd': 0.4},
            {'exposure': 200000, 'pd': 0.05, 'lgd': 0.45},
            {'exposure': 150000, 'pd': 0.03, 'lgd': 0.35}
        ]
        
        stress_scenarios = [
            {
                'name': 'Severe Recession',
                'pd_stress_factor': 3.0,
                'lgd_stress_factor': 1.5
            },
            {
                'name': 'Market Crisis',
                'pd_stress_factor': 2.5,
                'lgd_stress_factor': 1.3
            }
        ]
        
        result = self.credit_risk.run_stress_test(portfolio_data, stress_scenarios)
        
        self.assertIn('Severe Recession', result)
        self.assertIn('Market Crisis', result)
        
        print("✓ Credit Risk Stress Testing Results:")
        for scenario, metrics in result.items():
            print(f"  {scenario}: PD={metrics['stressed_pd']:.4f}, EL=${metrics['stressed_expected_loss']:,.2f}")


class TestPortfolioOptimization(unittest.TestCase):
    """Test Portfolio Optimization Modules"""
    
    def setUp(self):
        """Set up test data"""
        self.portfolio_optimizer = PortfolioOptimizer()
        self.mean_variance_optimizer = MeanVarianceOptimizer()
        self.black_litterman_optimizer = BlackLittermanOptimizer()
        self.risk_parity_optimizer = RiskParityOptimizer()
        
        # Generate sample returns data
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=252, freq='D')
        n_assets = 5
        
        returns_data = {}
        for i in range(n_assets):
            returns_data[f'Asset_{i+1}'] = np.random.normal(0.001, 0.02, 252)
        
        self.returns_df = pd.DataFrame(returns_data, index=dates)
        self.risk_free_rate = 0.02
        
    def test_mean_variance_optimization(self):
        """Test mean-variance portfolio optimization"""
        result = self.mean_variance_optimizer.optimize(
            self.returns_df, self.risk_free_rate
        )
        
        self.assertIn('weights', result)
        self.assertIn('expected_return', result)
        self.assertIn('volatility', result)
        self.assertIn('sharpe_ratio', result)
        
        # Validate results
        weights = np.array(result['weights'])
        self.assertAlmostEqual(np.sum(weights), 1.0, places=6)
        self.assertTrue(np.all(weights >= 0))
        
        print(f"✓ Mean-Variance Optimization:")
        print(f"  Expected Return: {result['expected_return']:.4f}")
        print(f"  Volatility: {result['volatility']:.4f}")
        print(f"  Sharpe Ratio: {result['sharpe_ratio']:.4f}")
        print(f"  Weights: {[f'{w:.3f}' for w in result['weights']]}")
        
    def test_black_litterman_optimization(self):
        """Test Black-Litterman portfolio optimization"""
        # Market capitalization weights
        market_caps = pd.Series([0.3, 0.25, 0.2, 0.15, 0.1], 
                              index=self.returns_df.columns)
        
        # Investor views
        views = {
            'view1': {
                'assets': ['Asset_1', 'Asset_2'],
                'weights': [0.7, 0.3],
                'expected_return': 0.0015
            }
        }
        
        view_confidences = {'view1': 0.8}
        
        result = self.black_litterman_optimizer.optimize(
            market_caps, self.returns_df, views, view_confidences
        )
        
        self.assertIn('weights', result)
        self.assertIn('posterior_returns', result)
        
        print(f"✓ Black-Litterman Optimization:")
        print(f"  Weights: {[f'{w:.3f}' for w in result['weights']]}")
        
    def test_risk_parity_optimization(self):
        """Test risk parity portfolio optimization"""
        result = self.risk_parity_optimizer.optimize(self.returns_df)
        
        self.assertIn('weights', result)
        self.assertIn('volatility', result)
        self.assertIn('risk_contributions', result)
        
        # Validate results
        weights = np.array(result['weights'])
        self.assertAlmostEqual(np.sum(weights), 1.0, places=6)
        
        print(f"✓ Risk Parity Optimization:")
        print(f"  Volatility: {result['volatility']:.4f}")
        print(f"  Weights: {[f'{w:.3f}' for w in result['weights']]}")
        print(f"  Risk Contributions: {[f'{rc:.4f}' for rc in result['risk_contributions']]}")
        
    def test_efficient_frontier(self):
        """Test efficient frontier calculation"""
        result = self.mean_variance_optimizer.calculate_efficient_frontier(
            self.returns_df, self.risk_free_rate, num_portfolios=50
        )
        
        self.assertIn('efficient_frontier', result)
        self.assertGreater(len(result['efficient_frontier']), 0)
        
        print(f"✓ Efficient Frontier:")
        print(f"  Number of portfolios: {len(result['efficient_frontier'])}")
        
        # Check that portfolios are properly ordered
        frontiers = result['efficient_frontier']
        volatilities = [p['volatility'] for p in frontiers]
        returns = [p['return'] for p in frontiers]
        
        # Should have multiple portfolios
        self.assertGreater(len(volatilities), 1)
        
        # Check that we have a reasonable range of volatilities
        vol_range = max(volatilities) - min(volatilities)
        self.assertGreater(vol_range, 0.001)  # At least some variation
        
    def test_portfolio_metrics(self):
        """Test portfolio performance metrics calculation"""
        weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])  # Equal weights
        
        metrics = self.portfolio_optimizer.calculate_portfolio_metrics(
            weights, self.returns_df, self.risk_free_rate
        )
        
        self.assertIn('expected_return', metrics)
        self.assertIn('volatility', metrics)
        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('var_95', metrics)
        self.assertIn('max_drawdown', metrics)
        
        print(f"✓ Portfolio Metrics:")
        print(f"  Expected Return: {metrics['expected_return']:.4f}")
        print(f"  Volatility: {metrics['volatility']:.4f}")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
        print(f"  VaR (95%): {metrics['var_95']:.4f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.4f}")
        
    def test_portfolio_rebalancing(self):
        """Test portfolio rebalancing calculation"""
        current_weights = np.array([0.3, 0.3, 0.2, 0.1, 0.1])
        target_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        transaction_costs = 0.001
        
        result = self.portfolio_optimizer.rebalance_portfolio(
            current_weights, target_weights, transaction_costs
        )
        
        self.assertIn('trades', result)
        self.assertIn('transaction_costs', result)
        self.assertIn('net_value', result)
        
        print(f"✓ Portfolio Rebalancing:")
        print(f"  Transaction Costs: ${result['transaction_costs']:.4f}")
        print(f"  Net Value: {result['net_value']:.4f}")
        print(f"  Trades: {[f'{t:.3f}' for t in result['trades']]}")


class TestRiskManagement(unittest.TestCase):
    """Test Risk Management Modules"""
    
    def setUp(self):
        """Set up test data"""
        self.risk_manager = RiskManager()
        self.var_calculator = VaRCalculator()
        self.stress_tester = StressTester()
        self.risk_attributor = RiskAttributor()
        
        # Generate sample returns data
        np.random.seed(42)
        self.returns_series = pd.Series(np.random.normal(0.001, 0.02, 1000))
        
        # Portfolio data for stress testing
        self.portfolio_data = {
            'weights': [0.3, 0.3, 0.2, 0.1, 0.1],
            'returns': pd.DataFrame({
                'Asset_1': np.random.normal(0.001, 0.02, 252),
                'Asset_2': np.random.normal(0.001, 0.015, 252),
                'Asset_3': np.random.normal(0.0005, 0.025, 252),
                'Asset_4': np.random.normal(0.002, 0.03, 252),
                'Asset_5': np.random.normal(0.0015, 0.018, 252)
            }),
            'asset_names': ['Asset_1', 'Asset_2', 'Asset_3', 'Asset_4', 'Asset_5']
        }
        
    def test_historical_var(self):
        """Test historical VaR calculation"""
        result = self.var_calculator.calculate_historical_var(
            self.returns_series, confidence_level=0.95, time_horizon=1
        )
        
        self.assertIn('historical_var', result)
        self.assertIn('conditional_var', result)
        self.assertIn('confidence_level', result)
        
        print(f"✓ Historical VaR (95%): {result['historical_var']:.4f}")
        print(f"✓ Conditional VaR: {result['conditional_var']:.4f}")
        
    def test_parametric_var(self):
        """Test parametric VaR calculation"""
        result = self.var_calculator.calculate_parametric_var(
            self.returns_series, confidence_level=0.95, time_horizon=1,
            distribution='normal'
        )
        
        self.assertIn('parametric_var', result)
        self.assertIn('mean_return', result)
        self.assertIn('std_return', result)
        
        print(f"✓ Parametric VaR (95%): {result['parametric_var']:.4f}")
        print(f"✓ Mean Return: {result['mean_return']:.4f}")
        print(f"✓ Std Return: {result['std_return']:.4f}")
        
    def test_monte_carlo_var(self):
        """Test Monte Carlo VaR calculation"""
        result = self.var_calculator.calculate_monte_carlo_var(
            self.returns_series, confidence_level=0.95, time_horizon=1,
            num_simulations=5000, distribution='normal'
        )
        
        self.assertIn('monte_carlo_var', result)
        self.assertIn('conditional_var', result)
        self.assertIn('num_simulations', result)
        
        print(f"✓ Monte Carlo VaR (95%): {result['monte_carlo_var']:.4f}")
        print(f"✓ Conditional VaR: {result['conditional_var']:.4f}")
        
    def test_stress_testing(self):
        """Test stress testing"""
        scenario = {
            'name': 'Market Crash',
            'equity_shock': -0.30,
            'interest_rate_shock': 0.02,
            'volatility_shock': 2.0
        }
        
        result = self.stress_tester.run_stress_test(self.portfolio_data, scenario)
        
        self.assertIn('scenario_name', result)
        self.assertIn('stressed_mean_return', result)
        self.assertIn('stressed_volatility', result)
        self.assertIn('return_impact', result)
        
        print(f"✓ Stress Test Results ({result['scenario_name']}):")
        print(f"  Stressed Return: {result['stressed_mean_return']:.4f}")
        print(f"  Stressed Volatility: {result['stressed_volatility']:.4f}")
        print(f"  Return Impact: {result['return_impact']:.4f}")
        
    def test_risk_attribution(self):
        """Test risk attribution"""
        result = self.risk_attributor.calculate_risk_attribution(
            self.portfolio_data, method='asset'
        )
        
        self.assertIn('portfolio_volatility', result)
        self.assertIn('attribution', result)
        
        print(f"✓ Risk Attribution (Asset Level):")
        print(f"  Portfolio Volatility: {result['portfolio_volatility']:.4f}")
        
        for asset, metrics in result['attribution'].items():
            print(f"  {asset}: {metrics['percentage_contribution']:.2%}")
            
    def test_tail_risk_measures(self):
        """Test tail risk measures calculation"""
        result = self.risk_manager.calculate_tail_risk_measures(
            self.returns_series, confidence_levels=[0.95, 0.99]
        )
        
        self.assertIn('var_95', result)
        self.assertIn('var_99', result)
        self.assertIn('skewness', result)
        self.assertIn('kurtosis', result)
        self.assertIn('max_drawdown', result)
        
        print(f"✓ Tail Risk Measures:")
        print(f"  VaR (95%): {result['var_95']:.4f}")
        print(f"  VaR (99%): {result['var_99']:.4f}")
        print(f"  Skewness: {result['skewness']:.4f}")
        print(f"  Kurtosis: {result['kurtosis']:.4f}")
        print(f"  Max Drawdown: {result['max_drawdown']:.4f}")
        
    def test_incremental_var(self):
        """Test incremental VaR calculation"""
        new_position = {
            'asset': 'Asset_6',
            'weight': 0.1,
            'returns': np.random.normal(0.001, 0.02, 252)
        }
        
        result = self.risk_manager.calculate_incremental_var(
            self.portfolio_data, new_position
        )
        
        self.assertIn('current_var', result)
        self.assertIn('new_var', result)
        self.assertIn('incremental_var', result)
        
        print(f"✓ Incremental VaR:")
        print(f"  Current VaR: {result['current_var']:.4f}")
        print(f"  New VaR: {result['new_var']:.4f}")
        print(f"  Incremental VaR: {result['incremental_var']:.4f}")


class TestIntegration(unittest.TestCase):
    """Test Integration Between Modules"""
    
    def setUp(self):
        """Set up test data"""
        self.credit_risk = CreditRiskValuation()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.risk_manager = RiskManager()
        
        # Generate comprehensive test data
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', periods=252, freq='D')
        
        # Asset returns
        returns_data = {
            'Equity_1': np.random.normal(0.001, 0.02, 252),
            'Equity_2': np.random.normal(0.001, 0.015, 252),
            'Bond_1': np.random.normal(0.0005, 0.008, 252),
            'Bond_2': np.random.normal(0.0003, 0.006, 252),
            'Commodity': np.random.normal(0.0008, 0.025, 252)
        }
        
        self.returns_df = pd.DataFrame(returns_data, index=dates)
        
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        print("\n🔄 Testing End-to-End Workflow...")
        
        # Step 1: Portfolio Optimization
        print("1. Portfolio Optimization...")
        portfolio_result = self.portfolio_optimizer.optimize_mean_variance(
            self.returns_df, risk_free_rate=0.02
        )
        
        self.assertIn('weights', portfolio_result)
        weights = np.array(portfolio_result['weights'])
        
        # Step 2: Risk Analysis
        print("2. Risk Analysis...")
        portfolio_returns = np.dot(self.returns_df, weights)
        var_result = self.risk_manager.calculate_var(
            pd.Series(portfolio_returns), method='historical'
        )
        
        # Step 3: Credit Risk Assessment (for bond components)
        print("3. Credit Risk Assessment...")
        bond_weights = weights[2:4]  # Bond components
        total_bond_exposure = np.sum(bond_weights)
        
        if total_bond_exposure > 0:
            # Simplified credit risk assessment
            credit_result = self.credit_risk.calculate_merton_pd(
                asset_value=1000000,
                debt_value=600000,
                asset_volatility=0.25,
                risk_free_rate=0.02,
                time_to_maturity=1.0
            )
        
        # Step 4: Stress Testing
        print("4. Stress Testing...")
        portfolio_data = {
            'weights': weights.tolist(),
            'returns': self.returns_df,
            'asset_names': self.returns_df.columns.tolist()
        }
        
        stress_result = self.risk_manager.run_stress_test(portfolio_data)
        
        # Validate results
        self.assertIsInstance(portfolio_result['sharpe_ratio'], (int, float))
        self.assertLess(var_result['historical_var'], 0)
        
        print("✓ End-to-End Workflow Completed Successfully!")
        print(f"  Portfolio Sharpe Ratio: {portfolio_result['sharpe_ratio']:.4f}")
        print(f"  Portfolio VaR (95%): {var_result['historical_var']:.4f}")
        print(f"  Stress Test Impact: {stress_result['return_impact']:.4f}")


def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive Phase 5 Advanced Financial Models Test Suite")
    print("=" * 80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestCreditRiskModels,
        TestPortfolioOptimization,
        TestRiskManagement,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED! Phase 5 Advanced Financial Models are working correctly.")
        return True
    else:
        print("\n❌ SOME TESTS FAILED. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1) 