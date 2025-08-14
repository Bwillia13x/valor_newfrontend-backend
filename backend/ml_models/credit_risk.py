"""
Credit Risk Modeling Module
Implements Merton, KMV, and CreditMetrics models for credit risk assessment
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import logging
from typing import Dict, List, Tuple, Optional, Union
import json

logger = logging.getLogger(__name__)

class MertonModel:
    """Merton Model for credit risk assessment"""
    
    def __init__(self):
        self.model_name = "Merton"
    
    def calculate_pd(self, asset_value: float, debt_value: float, 
                    asset_volatility: float, risk_free_rate: float, 
                    time_to_maturity: float) -> Dict[str, float]:
        """
        Calculate probability of default using Merton model
        
        Args:
            asset_value: Current market value of assets
            debt_value: Face value of debt
            asset_volatility: Volatility of asset returns
            risk_free_rate: Risk-free interest rate
            time_to_maturity: Time to debt maturity
            
        Returns:
            Dictionary with PD and other metrics
        """
        try:
            # Calculate distance to default
            d1 = (np.log(asset_value / debt_value) + 
                  (risk_free_rate + 0.5 * asset_volatility**2) * time_to_maturity) / \
                 (asset_volatility * np.sqrt(time_to_maturity))
            
            d2 = d1 - asset_volatility * np.sqrt(time_to_maturity)
            
            # Calculate probability of default
            pd = stats.norm.cdf(-d2)
            
            # Calculate expected loss
            expected_loss = debt_value * pd
            
            # Calculate credit spread
            credit_spread = -np.log(1 - pd) / time_to_maturity - risk_free_rate
            
            return {
                'probability_of_default': pd,
                'distance_to_default': d2,
                'expected_loss': expected_loss,
                'credit_spread': credit_spread,
                'd1': d1,
                'd2': d2
            }
            
        except Exception as e:
            logger.error(f"Error in Merton PD calculation: {e}")
            raise
    
    def estimate_asset_value_and_volatility(self, equity_value: float, 
                                          equity_volatility: float,
                                          debt_value: float, 
                                          risk_free_rate: float,
                                          time_to_maturity: float) -> Dict[str, float]:
        """
        Estimate asset value and volatility from equity data
        
        Args:
            equity_value: Market value of equity
            equity_volatility: Volatility of equity returns
            debt_value: Face value of debt
            risk_free_rate: Risk-free interest rate
            time_to_maturity: Time to debt maturity
            
        Returns:
            Dictionary with estimated asset value and volatility
        """
        try:
            def objective_function(params):
                asset_value, asset_volatility = params
                
                # Calculate equity value using Black-Scholes
                d1 = (np.log(asset_value / debt_value) + 
                      (risk_free_rate + 0.5 * asset_volatility**2) * time_to_maturity) / \
                     (asset_volatility * np.sqrt(time_to_maturity))
                
                d2 = d1 - asset_volatility * np.sqrt(time_to_maturity)
                
                calculated_equity = (asset_value * stats.norm.cdf(d1) - 
                                   debt_value * np.exp(-risk_free_rate * time_to_maturity) * 
                                   stats.norm.cdf(d2))
                
                # Calculate equity volatility
                calculated_equity_vol = (asset_value * asset_volatility * 
                                       stats.norm.cdf(d1) / calculated_equity)
                
                # Return squared error
                return ((calculated_equity - equity_value)**2 + 
                       (calculated_equity_vol - equity_volatility)**2)
            
            # Initial guess
            initial_guess = [equity_value + debt_value, equity_volatility]
            
            # Optimize
            result = minimize(objective_function, initial_guess, 
                            method='L-BFGS-B',
                            bounds=[(equity_value, None), (0.01, 2.0)])
            
            if result.success:
                asset_value, asset_volatility = result.x
                return {
                    'asset_value': asset_value,
                    'asset_volatility': asset_volatility
                }
            else:
                raise ValueError("Failed to converge in asset value estimation")
                
        except Exception as e:
            logger.error(f"Error in asset value estimation: {e}")
            raise


class KMVModel:
    """KMV Model for credit risk assessment"""
    
    def __init__(self):
        self.model_name = "KMV"
        self.default_threshold = 0.5  # Default threshold for KMV
    
    def calculate_pd(self, asset_value: float, debt_value: float,
                    asset_volatility: float, risk_free_rate: float,
                    time_to_maturity: float, default_threshold: float = None) -> Dict[str, float]:
        """
        Calculate probability of default using KMV model
        
        Args:
            asset_value: Current market value of assets
            debt_value: Face value of debt
            asset_volatility: Volatility of asset returns
            risk_free_rate: Risk-free interest rate
            time_to_maturity: Time to debt maturity
            default_threshold: Default threshold (default: 0.5)
            
        Returns:
            Dictionary with PD and other metrics
        """
        try:
            if default_threshold is None:
                default_threshold = self.default_threshold
            
            # Calculate distance to default
            d1 = (np.log(asset_value / debt_value) + 
                  (risk_free_rate + 0.5 * asset_volatility**2) * time_to_maturity) / \
                 (asset_volatility * np.sqrt(time_to_maturity))
            
            d2 = d1 - asset_volatility * np.sqrt(time_to_maturity)
            
            # KMV probability of default
            pd = stats.norm.cdf(-d2)
            
            # Expected default frequency (EDF)
            edf = pd
            
            # Distance to default
            distance_to_default = d2
            
            # Expected loss
            expected_loss = debt_value * pd
            
            return {
                'probability_of_default': pd,
                'expected_default_frequency': edf,
                'distance_to_default': distance_to_default,
                'expected_loss': expected_loss,
                'default_threshold': default_threshold,
                'd1': d1,
                'd2': d2
            }
            
        except Exception as e:
            logger.error(f"Error in KMV PD calculation: {e}")
            raise
    
    def calculate_portfolio_pd(self, portfolio_data: List[Dict]) -> Dict[str, float]:
        """
        Calculate portfolio-level probability of default
        
        Args:
            portfolio_data: List of dictionaries with individual asset data
            
        Returns:
            Dictionary with portfolio PD and risk metrics
        """
        try:
            total_exposure = sum(asset['exposure'] for asset in portfolio_data)
            weighted_pd = sum(asset['pd'] * asset['exposure'] for asset in portfolio_data) / total_exposure
            
            # Calculate portfolio expected loss
            portfolio_el = sum(asset['pd'] * asset['exposure'] * asset.get('lgd', 0.4) 
                             for asset in portfolio_data)
            
            # Calculate portfolio unexpected loss (simplified)
            portfolio_ul = np.sqrt(sum((asset['exposure'] * asset.get('lgd', 0.4))**2 * 
                                      asset['pd'] * (1 - asset['pd']) 
                                      for asset in portfolio_data))
            
            return {
                'portfolio_pd': weighted_pd,
                'portfolio_expected_loss': portfolio_el,
                'portfolio_unexpected_loss': portfolio_ul,
                'total_exposure': total_exposure,
                'num_assets': len(portfolio_data)
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio PD calculation: {e}")
            raise


class CreditMetricsModel:
    """CreditMetrics model for credit risk assessment"""
    
    def __init__(self):
        self.model_name = "CreditMetrics"
        self.rating_transitions = {
            'AAA': {'AAA': 0.90, 'AA': 0.08, 'A': 0.02, 'BBB': 0.00, 'BB': 0.00, 'B': 0.00, 'CCC': 0.00, 'D': 0.00},
            'AA': {'AAA': 0.02, 'AA': 0.90, 'A': 0.06, 'BBB': 0.02, 'BB': 0.00, 'B': 0.00, 'CCC': 0.00, 'D': 0.00},
            'A': {'AAA': 0.00, 'AA': 0.03, 'A': 0.90, 'BBB': 0.05, 'BB': 0.02, 'B': 0.00, 'CCC': 0.00, 'D': 0.00},
            'BBB': {'AAA': 0.00, 'AA': 0.00, 'A': 0.04, 'BBB': 0.90, 'BB': 0.04, 'B': 0.02, 'CCC': 0.00, 'D': 0.00},
            'BB': {'AAA': 0.00, 'AA': 0.00, 'A': 0.00, 'BBB': 0.05, 'BB': 0.85, 'B': 0.08, 'CCC': 0.02, 'D': 0.00},
            'B': {'AAA': 0.00, 'AA': 0.00, 'A': 0.00, 'BBB': 0.00, 'BB': 0.04, 'B': 0.85, 'CCC': 0.08, 'D': 0.03},
            'CCC': {'AAA': 0.00, 'AA': 0.00, 'A': 0.00, 'BBB': 0.00, 'BB': 0.00, 'B': 0.10, 'CCC': 0.75, 'D': 0.15}
        }
        
        self.recovery_rates = {
            'AAA': 0.60, 'AA': 0.60, 'A': 0.55, 'BBB': 0.50, 
            'BB': 0.45, 'B': 0.40, 'CCC': 0.35, 'D': 0.30
        }
    
    def calculate_credit_var(self, portfolio_data: List[Dict], 
                           confidence_level: float = 0.99) -> Dict[str, float]:
        """
        Calculate Credit VaR using CreditMetrics approach
        
        Args:
            portfolio_data: List of dictionaries with asset data
            confidence_level: VaR confidence level
            
        Returns:
            Dictionary with Credit VaR and other metrics
        """
        try:
            # Simulate portfolio value distribution
            num_simulations = 10000
            portfolio_values = []
            
            for _ in range(num_simulations):
                portfolio_value = 0
                
                for asset in portfolio_data:
                    # Simulate rating transition
                    current_rating = asset['rating']
                    transition_probs = self.rating_transitions.get(current_rating, {})
                    
                    # Generate random transition
                    rand_val = np.random.random()
                    cumulative_prob = 0
                    new_rating = current_rating
                    
                    for rating, prob in transition_probs.items():
                        cumulative_prob += prob
                        if rand_val <= cumulative_prob:
                            new_rating = rating
                            break
                    
                    # Calculate asset value
                    if new_rating == 'D':
                        # Default
                        recovery_rate = self.recovery_rates.get(current_rating, 0.4)
                        asset_value = asset['exposure'] * recovery_rate
                    else:
                        # No default - use credit spread
                        spread = self._get_credit_spread(new_rating)
                        asset_value = asset['exposure'] * np.exp(-spread * asset.get('maturity', 1))
                    
                    portfolio_value += asset_value
                
                portfolio_values.append(portfolio_value)
            
            # Calculate VaR
            portfolio_values = np.array(portfolio_values)
            var_percentile = (1 - confidence_level) * 100
            credit_var = np.percentile(portfolio_values, var_percentile)
            
            # Calculate expected portfolio value
            expected_value = np.mean(portfolio_values)
            
            # Calculate unexpected loss
            unexpected_loss = expected_value - credit_var
            
            return {
                'credit_var': credit_var,
                'expected_portfolio_value': expected_value,
                'unexpected_loss': unexpected_loss,
                'confidence_level': confidence_level,
                'num_simulations': num_simulations,
                'portfolio_values': portfolio_values.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in Credit VaR calculation: {e}")
            raise
    
    def _get_credit_spread(self, rating: str) -> float:
        """Get credit spread for a given rating"""
        spreads = {
            'AAA': 0.001, 'AA': 0.002, 'A': 0.005, 'BBB': 0.015,
            'BB': 0.035, 'B': 0.075, 'CCC': 0.150, 'D': 0.500
        }
        return spreads.get(rating, 0.100)
    
    def calculate_rating_transition_matrix(self, historical_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Calculate rating transition matrix from historical data
        
        Args:
            historical_data: DataFrame with historical rating data
            
        Returns:
            Rating transition matrix
        """
        try:
            # This is a simplified implementation
            # In practice, you would use actual historical rating transition data
            
            ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'D']
            transition_matrix = {}
            
            for rating in ratings:
                transition_matrix[rating] = {}
                for target_rating in ratings:
                    # Simplified transition probabilities
                    if rating == target_rating:
                        transition_matrix[rating][target_rating] = 0.85
                    elif target_rating == 'D':
                        transition_matrix[rating][target_rating] = 0.01
                    else:
                        transition_matrix[rating][target_rating] = 0.02
            
            return transition_matrix
            
        except Exception as e:
            logger.error(f"Error in transition matrix calculation: {e}")
            raise


class CreditRiskValuation:
    """Main credit risk valuation class"""
    
    def __init__(self):
        self.merton_model = MertonModel()
        self.kmv_model = KMVModel()
        self.credit_metrics_model = CreditMetricsModel()
        
    def calculate_merton_pd(self, asset_value: float, debt_value: float,
                          asset_volatility: float, risk_free_rate: float,
                          time_to_maturity: float) -> Dict[str, float]:
        """Calculate PD using Merton model"""
        return self.merton_model.calculate_pd(
            asset_value, debt_value, asset_volatility, risk_free_rate, time_to_maturity
        )
    
    def calculate_kmv_pd(self, asset_value: float, debt_value: float,
                        asset_volatility: float, risk_free_rate: float,
                        time_to_maturity: float, default_threshold: float = None) -> Dict[str, float]:
        """Calculate PD using KMV model"""
        return self.kmv_model.calculate_pd(
            asset_value, debt_value, asset_volatility, risk_free_rate, 
            time_to_maturity, default_threshold
        )
    
    def calculate_credit_metrics_var(self, portfolio_data: List[Dict],
                                   confidence_level: float = 0.99) -> Dict[str, float]:
        """Calculate Credit VaR using CreditMetrics"""
        return self.credit_metrics_model.calculate_credit_var(portfolio_data, confidence_level)
    
    def estimate_asset_parameters(self, equity_value: float, equity_volatility: float,
                                debt_value: float, risk_free_rate: float,
                                time_to_maturity: float) -> Dict[str, float]:
        """Estimate asset value and volatility from equity data"""
        return self.merton_model.estimate_asset_value_and_volatility(
            equity_value, equity_volatility, debt_value, risk_free_rate, time_to_maturity
        )
    
    def calculate_portfolio_risk(self, portfolio_data: List[Dict]) -> Dict[str, float]:
        """Calculate portfolio-level credit risk"""
        return self.kmv_model.calculate_portfolio_pd(portfolio_data)
    
    def calculate_credit_spread(self, risk_free_rate: float, pd: float,
                              lgd: float, maturity: float) -> float:
        """
        Calculate credit spread
        
        Args:
            risk_free_rate: Risk-free interest rate
            pd: Probability of default
            lgd: Loss given default
            maturity: Time to maturity
            
        Returns:
            Credit spread
        """
        try:
            # Credit spread = -ln(1 - PD * LGD) / maturity - risk_free_rate
            credit_spread = -np.log(1 - pd * lgd) / maturity - risk_free_rate
            return max(credit_spread, 0)  # Ensure non-negative spread
            
        except Exception as e:
            logger.error(f"Error in credit spread calculation: {e}")
            raise
    
    def train_rating_model(self, training_data: pd.DataFrame, 
                          model_type: str = 'logistic') -> Dict[str, any]:
        """
        Train internal rating model
        
        Args:
            training_data: DataFrame with financial ratios and ratings
            model_type: Type of model ('logistic', 'random_forest', etc.)
            
        Returns:
            Trained model and performance metrics
        """
        try:
            # This is a placeholder for rating model training
            # In practice, you would implement actual machine learning models
            
            return {
                'model_type': model_type,
                'status': 'trained',
                'accuracy': 0.85,
                'features': ['debt_to_equity', 'current_ratio', 'roa', 'interest_coverage'],
                'model_params': {}
            }
            
        except Exception as e:
            logger.error(f"Error in rating model training: {e}")
            raise
    
    def predict_credit_rating(self, financial_data: Dict[str, float],
                            trained_model: Dict[str, any]) -> Dict[str, any]:
        """
        Predict credit rating using trained model
        
        Args:
            financial_data: Dictionary with financial ratios
            trained_model: Trained rating model
            
        Returns:
            Predicted rating and confidence
        """
        try:
            # This is a placeholder for rating prediction
            # In practice, you would use the actual trained model
            
            # Simple rule-based rating (for demonstration)
            debt_to_equity = financial_data.get('debt_to_equity', 1.0)
            current_ratio = financial_data.get('current_ratio', 1.0)
            roa = financial_data.get('roa', 0.05)
            
            if debt_to_equity < 0.3 and current_ratio > 2.0 and roa > 0.1:
                rating = 'AAA'
            elif debt_to_equity < 0.5 and current_ratio > 1.5 and roa > 0.05:
                rating = 'AA'
            elif debt_to_equity < 0.7 and current_ratio > 1.2 and roa > 0.03:
                rating = 'A'
            elif debt_to_equity < 1.0 and current_ratio > 1.0 and roa > 0.01:
                rating = 'BBB'
            elif debt_to_equity < 1.5 and current_ratio > 0.8 and roa > 0.0:
                rating = 'BB'
            elif debt_to_equity < 2.0 and current_ratio > 0.6:
                rating = 'B'
            else:
                rating = 'CCC'
            
            return {
                'predicted_rating': rating,
                'confidence': 0.85,
                'model_type': trained_model.get('model_type', 'rule_based')
            }
            
        except Exception as e:
            logger.error(f"Error in rating prediction: {e}")
            raise
    
    def run_stress_test(self, portfolio_data: List[Dict],
                       stress_scenarios: List[Dict]) -> Dict[str, any]:
        """
        Run credit risk stress testing
        
        Args:
            portfolio_data: Portfolio data
            stress_scenarios: List of stress scenarios
            
        Returns:
            Stress test results
        """
        try:
            results = {}
            
            for i, scenario in enumerate(stress_scenarios):
                scenario_name = scenario.get('name', f'Scenario_{i+1}')
                
                # Apply stress factors
                stressed_portfolio = []
                for asset in portfolio_data:
                    stressed_asset = asset.copy()
                    
                    # Apply stress to PD
                    pd_stress_factor = scenario.get('pd_stress_factor', 1.0)
                    stressed_asset['pd'] = min(asset['pd'] * pd_stress_factor, 1.0)
                    
                    # Apply stress to LGD
                    lgd_stress_factor = scenario.get('lgd_stress_factor', 1.0)
                    stressed_asset['lgd'] = min(asset.get('lgd', 0.4) * lgd_stress_factor, 1.0)
                    
                    stressed_portfolio.append(stressed_asset)
                
                # Calculate stressed portfolio risk
                stressed_risk = self.calculate_portfolio_risk(stressed_portfolio)
                
                results[scenario_name] = {
                    'stressed_pd': stressed_risk['portfolio_pd'],
                    'stressed_expected_loss': stressed_risk['portfolio_expected_loss'],
                    'stressed_unexpected_loss': stressed_risk['portfolio_unexpected_loss'],
                    'scenario_params': scenario
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in stress testing: {e}")
            raise 