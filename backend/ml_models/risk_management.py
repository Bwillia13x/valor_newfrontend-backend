"""
Risk Management Module
Implements VaR, stress testing, and risk attribution capabilities
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
import logging
from typing import Dict, List, Tuple, Optional, Union
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VaRCalculator:
    """Value at Risk (VaR) Calculator"""
    
    def __init__(self):
        self.model_name = "VaR Calculator"
    
    def calculate_historical_var(self, returns: pd.Series, confidence_level: float = 0.95,
                               time_horizon: int = 1) -> Dict[str, float]:
        """
        Calculate historical VaR
        
        Args:
            returns: Asset or portfolio returns
            confidence_level: VaR confidence level (e.g., 0.95 for 95%)
            time_horizon: Time horizon in days
            
        Returns:
            Historical VaR results
        """
        try:
            # Calculate VaR percentile
            var_percentile = (1 - confidence_level) * 100
            
            # Calculate historical VaR
            historical_var = np.percentile(returns, var_percentile)
            
            # Scale for time horizon
            scaled_var = historical_var * np.sqrt(time_horizon)
            
            # Calculate Conditional VaR (Expected Shortfall)
            cvar_threshold = returns <= historical_var
            conditional_var = returns[cvar_threshold].mean()
            scaled_cvar = conditional_var * np.sqrt(time_horizon)
            
            return {
                'historical_var': historical_var,
                'scaled_var': scaled_var,
                'conditional_var': conditional_var,
                'scaled_cvar': scaled_cvar,
                'confidence_level': confidence_level,
                'time_horizon': time_horizon,
                'var_percentile': var_percentile
            }
            
        except Exception as e:
            logger.error(f"Error in historical VaR calculation: {e}")
            raise
    
    def calculate_parametric_var(self, returns: pd.Series, confidence_level: float = 0.95,
                               time_horizon: int = 1, distribution: str = 'normal') -> Dict[str, float]:
        """
        Calculate parametric VaR
        
        Args:
            returns: Asset or portfolio returns
            confidence_level: VaR confidence level
            time_horizon: Time horizon in days
            distribution: Distribution assumption ('normal', 't', 'skewed_t')
            
        Returns:
            Parametric VaR results
        """
        try:
            mean_return = returns.mean()
            std_return = returns.std()
            
            if distribution == 'normal':
                # Normal distribution
                z_score = stats.norm.ppf(1 - confidence_level)
                parametric_var = mean_return - z_score * std_return
                
            elif distribution == 't':
                # Student's t-distribution
                df = len(returns) - 1  # Degrees of freedom
                t_score = stats.t.ppf(1 - confidence_level, df)
                parametric_var = mean_return - t_score * std_return
                
            elif distribution == 'skewed_t':
                # Skewed t-distribution (simplified)
                skewness = stats.skew(returns)
                kurtosis = stats.kurtosis(returns)
                
                # Cornish-Fisher expansion
                z_score = stats.norm.ppf(1 - confidence_level)
                skewness_adjustment = (skewness / 6) * (z_score**2 - 1)
                kurtosis_adjustment = (kurtosis / 24) * (z_score**3 - 3*z_score)
                
                adjusted_z = z_score + skewness_adjustment + kurtosis_adjustment
                parametric_var = mean_return - adjusted_z * std_return
                
            else:
                raise ValueError(f"Unsupported distribution: {distribution}")
            
            # Scale for time horizon
            scaled_var = parametric_var * np.sqrt(time_horizon)
            
            return {
                'parametric_var': parametric_var,
                'scaled_var': scaled_var,
                'mean_return': mean_return,
                'std_return': std_return,
                'confidence_level': confidence_level,
                'time_horizon': time_horizon,
                'distribution': distribution
            }
            
        except Exception as e:
            logger.error(f"Error in parametric VaR calculation: {e}")
            raise
    
    def calculate_monte_carlo_var(self, returns: pd.Series, confidence_level: float = 0.95,
                                time_horizon: int = 1, num_simulations: int = 10000,
                                distribution: str = 'normal') -> Dict[str, float]:
        """
        Calculate Monte Carlo VaR
        
        Args:
            returns: Asset or portfolio returns
            confidence_level: VaR confidence level
            time_horizon: Time horizon in days
            num_simulations: Number of Monte Carlo simulations
            distribution: Distribution assumption
            
        Returns:
            Monte Carlo VaR results
        """
        try:
            mean_return = returns.mean()
            std_return = returns.std()
            
            # Generate random returns
            if distribution == 'normal':
                simulated_returns = np.random.normal(mean_return, std_return, num_simulations)
            elif distribution == 't':
                df = len(returns) - 1
                simulated_returns = stats.t.rvs(df, loc=mean_return, scale=std_return, 
                                             size=num_simulations)
            else:
                # Use empirical distribution
                simulated_returns = np.random.choice(returns, size=num_simulations)
            
            # Scale for time horizon
            scaled_returns = simulated_returns * np.sqrt(time_horizon)
            
            # Calculate VaR
            var_percentile = (1 - confidence_level) * 100
            monte_carlo_var = np.percentile(scaled_returns, var_percentile)
            
            # Calculate Conditional VaR
            cvar_threshold = scaled_returns <= monte_carlo_var
            conditional_var = scaled_returns[cvar_threshold].mean()
            
            return {
                'monte_carlo_var': monte_carlo_var,
                'conditional_var': conditional_var,
                'confidence_level': confidence_level,
                'time_horizon': time_horizon,
                'num_simulations': num_simulations,
                'distribution': distribution,
                'simulated_returns': scaled_returns.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in Monte Carlo VaR calculation: {e}")
            raise


class StressTester:
    """Stress Testing Framework"""
    
    def __init__(self):
        self.model_name = "Stress Tester"
        self.default_scenarios = {
            'market_crash': {
                'name': 'Market Crash',
                'equity_shock': -0.30,
                'interest_rate_shock': 0.02,
                'volatility_shock': 2.0,
                'correlation_shock': 0.3
            },
            'recession': {
                'name': 'Economic Recession',
                'equity_shock': -0.20,
                'interest_rate_shock': -0.01,
                'volatility_shock': 1.5,
                'correlation_shock': 0.2
            },
            'inflation_shock': {
                'name': 'Inflation Shock',
                'equity_shock': -0.10,
                'interest_rate_shock': 0.05,
                'volatility_shock': 1.8,
                'correlation_shock': 0.25
            },
            'liquidity_crisis': {
                'name': 'Liquidity Crisis',
                'equity_shock': -0.15,
                'interest_rate_shock': 0.03,
                'volatility_shock': 2.5,
                'correlation_shock': 0.4
            }
        }
    
    def run_stress_test(self, portfolio_data: Dict[str, any], 
                       scenario: Dict[str, any] = None) -> Dict[str, any]:
        """
        Run stress test on portfolio
        
        Args:
            portfolio_data: Portfolio data including weights, returns, etc.
            scenario: Stress scenario parameters
            
        Returns:
            Stress test results
        """
        try:
            if scenario is None:
                scenario = self.default_scenarios['market_crash']
            
            # Extract portfolio components
            weights = np.array(portfolio_data['weights'])
            returns = portfolio_data['returns']
            asset_names = portfolio_data['asset_names']
            
            # Apply stress shocks
            stressed_returns = returns.copy()
            
            # Equity shock
            if 'equity_shock' in scenario:
                equity_assets = [i for i, asset in enumerate(asset_names) 
                               if 'equity' in asset.lower() or 'stock' in asset.lower()]
                for i in equity_assets:
                    stressed_returns.iloc[:, i] += scenario['equity_shock']
            
            # Interest rate shock
            if 'interest_rate_shock' in scenario:
                bond_assets = [i for i, asset in enumerate(asset_names) 
                             if 'bond' in asset.lower() or 'treasury' in asset.lower()]
                for i in bond_assets:
                    stressed_returns.iloc[:, i] += scenario['interest_rate_shock']
            
            # Volatility shock
            if 'volatility_shock' in scenario:
                vol_multiplier = scenario['volatility_shock']
                stressed_returns = stressed_returns * vol_multiplier
            
            # Calculate stressed portfolio returns
            stressed_portfolio_returns = np.dot(stressed_returns, weights)
            
            # Calculate stressed metrics
            stressed_mean = stressed_portfolio_returns.mean()
            stressed_vol = stressed_portfolio_returns.std()
            stressed_var_95 = np.percentile(stressed_portfolio_returns, 5)
            stressed_cvar_95 = stressed_portfolio_returns[stressed_portfolio_returns <= stressed_var_95].mean()
            
            # Calculate impact
            baseline_returns = np.dot(returns, weights)
            baseline_mean = baseline_returns.mean()
            baseline_vol = baseline_returns.std()
            baseline_var_95 = np.percentile(baseline_returns, 5)
            
            return {
                'scenario_name': scenario.get('name', 'Custom Scenario'),
                'stressed_mean_return': stressed_mean,
                'stressed_volatility': stressed_vol,
                'stressed_var_95': stressed_var_95,
                'stressed_cvar_95': stressed_cvar_95,
                'baseline_mean_return': baseline_mean,
                'baseline_volatility': baseline_vol,
                'baseline_var_95': baseline_var_95,
                'return_impact': stressed_mean - baseline_mean,
                'volatility_impact': stressed_vol - baseline_vol,
                'var_impact': stressed_var_95 - baseline_var_95,
                'scenario_params': scenario
            }
            
        except Exception as e:
            logger.error(f"Error in stress testing: {e}")
            raise
    
    def run_multiple_scenarios(self, portfolio_data: Dict[str, any],
                             scenarios: List[Dict[str, any]] = None) -> Dict[str, any]:
        """
        Run multiple stress scenarios
        
        Args:
            portfolio_data: Portfolio data
            scenarios: List of stress scenarios
            
        Returns:
            Multiple scenario results
        """
        try:
            if scenarios is None:
                scenarios = list(self.default_scenarios.values())
            
            results = {}
            
            for scenario in scenarios:
                scenario_name = scenario.get('name', 'Custom Scenario')
                results[scenario_name] = self.run_stress_test(portfolio_data, scenario)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in multiple scenario stress testing: {e}")
            raise


class RiskAttributor:
    """Risk Attribution Analysis"""
    
    def __init__(self):
        self.model_name = "Risk Attributor"
    
    def calculate_risk_attribution(self, portfolio_data: Dict[str, any],
                                 method: str = 'factor') -> Dict[str, any]:
        """
        Calculate risk attribution
        
        Args:
            portfolio_data: Portfolio data
            method: Attribution method ('factor', 'asset', 'systematic')
            
        Returns:
            Risk attribution results
        """
        try:
            weights = np.array(portfolio_data['weights'])
            returns = portfolio_data['returns']
            asset_names = portfolio_data['asset_names']
            
            if method == 'asset':
                return self._asset_attribution(weights, returns, asset_names)
            elif method == 'factor':
                return self._factor_attribution(weights, returns, asset_names)
            elif method == 'systematic':
                return self._systematic_attribution(weights, returns, asset_names)
            else:
                raise ValueError(f"Unsupported attribution method: {method}")
                
        except Exception as e:
            logger.error(f"Error in risk attribution: {e}")
            raise
    
    def _asset_attribution(self, weights: np.ndarray, returns: pd.DataFrame,
                          asset_names: List[str]) -> Dict[str, any]:
        """Asset-level risk attribution"""
        try:
            cov_matrix = returns.cov()
            portfolio_var = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_vol = np.sqrt(portfolio_var)
            
            # Calculate marginal contributions
            marginal_contributions = np.dot(cov_matrix, weights) / portfolio_vol
            
            # Calculate percentage contributions
            percentage_contributions = (weights * marginal_contributions) / portfolio_vol
            
            # Create attribution dictionary
            attribution = {}
            for i, asset in enumerate(asset_names):
                attribution[asset] = {
                    'weight': weights[i],
                    'marginal_contribution': marginal_contributions[i],
                    'percentage_contribution': percentage_contributions[i],
                    'absolute_contribution': weights[i] * marginal_contributions[i]
                }
            
            return {
                'portfolio_volatility': portfolio_vol,
                'attribution': attribution,
                'method': 'asset_level'
            }
            
        except Exception as e:
            logger.error(f"Error in asset attribution: {e}")
            raise
    
    def _factor_attribution(self, weights: np.ndarray, returns: pd.DataFrame,
                          asset_names: List[str]) -> Dict[str, any]:
        """Factor-based risk attribution"""
        try:
            # Simplified factor model (market, size, value factors)
            # In practice, you would use actual factor loadings
            
            # Create synthetic factor loadings
            factor_loadings = pd.DataFrame(index=asset_names, 
                                         columns=['market', 'size', 'value'])
            
            for i, asset in enumerate(asset_names):
                if 'equity' in asset.lower():
                    factor_loadings.iloc[i, 0] = 1.0  # Market factor
                    factor_loadings.iloc[i, 1] = np.random.normal(0, 0.3)  # Size factor
                    factor_loadings.iloc[i, 2] = np.random.normal(0, 0.3)  # Value factor
                else:
                    factor_loadings.iloc[i, 0] = 0.1  # Low market exposure
                    factor_loadings.iloc[i, 1] = 0.0
                    factor_loadings.iloc[i, 2] = 0.0
            
            # Calculate factor exposures
            factor_exposures = np.dot(weights, factor_loadings.values)
            
            # Calculate factor risk contributions
            factor_volatilities = [0.15, 0.10, 0.08]  # Market, size, value volatilities
            factor_contributions = []
            
            for i, factor in enumerate(['market', 'size', 'value']):
                factor_contribution = factor_exposures[i] * factor_volatilities[i]
                factor_contributions.append({
                    'factor': factor,
                    'exposure': factor_exposures[i],
                    'volatility': factor_volatilities[i],
                    'contribution': factor_contribution
                })
            
            return {
                'factor_exposures': factor_exposures.tolist(),
                'factor_contributions': factor_contributions,
                'method': 'factor_based'
            }
            
        except Exception as e:
            logger.error(f"Error in factor attribution: {e}")
            raise
    
    def _systematic_attribution(self, weights: np.ndarray, returns: pd.DataFrame,
                              asset_names: List[str]) -> Dict[str, any]:
        """Systematic vs idiosyncratic risk attribution"""
        try:
            # Calculate total portfolio variance
            cov_matrix = returns.cov()
            total_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            
            # Estimate systematic risk (simplified)
            # In practice, you would use factor models or principal component analysis
            
            # Calculate average correlation
            correlations = returns.corr()
            avg_correlation = (correlations.sum().sum() - len(correlations)) / (len(correlations)**2 - len(correlations))
            
            # Estimate systematic variance
            individual_variances = np.diag(cov_matrix)
            systematic_variance = avg_correlation * np.sum(weights**2 * individual_variances)
            idiosyncratic_variance = total_variance - systematic_variance
            
            return {
                'total_variance': total_variance,
                'systematic_variance': systematic_variance,
                'idiosyncratic_variance': idiosyncratic_variance,
                'systematic_ratio': systematic_variance / total_variance,
                'idiosyncratic_ratio': idiosyncratic_variance / total_variance,
                'average_correlation': avg_correlation,
                'method': 'systematic_idiosyncratic'
            }
            
        except Exception as e:
            logger.error(f"Error in systematic attribution: {e}")
            raise


class RiskManager:
    """Main risk management class"""
    
    def __init__(self):
        self.var_calculator = VaRCalculator()
        self.stress_tester = StressTester()
        self.risk_attributor = RiskAttributor()
    
    def calculate_var(self, returns: pd.Series, method: str = 'historical',
                     confidence_level: float = 0.95, time_horizon: int = 1,
                     **kwargs) -> Dict[str, any]:
        """
        Calculate VaR using specified method
        
        Args:
            returns: Asset or portfolio returns
            method: VaR method ('historical', 'parametric', 'monte_carlo')
            confidence_level: VaR confidence level
            time_horizon: Time horizon in days
            **kwargs: Additional method-specific parameters
            
        Returns:
            VaR results
        """
        try:
            if method == 'historical':
                return self.var_calculator.calculate_historical_var(
                    returns, confidence_level, time_horizon
                )
            elif method == 'parametric':
                distribution = kwargs.get('distribution', 'normal')
                return self.var_calculator.calculate_parametric_var(
                    returns, confidence_level, time_horizon, distribution
                )
            elif method == 'monte_carlo':
                num_simulations = kwargs.get('num_simulations', 10000)
                distribution = kwargs.get('distribution', 'normal')
                return self.var_calculator.calculate_monte_carlo_var(
                    returns, confidence_level, time_horizon, num_simulations, distribution
                )
            else:
                raise ValueError(f"Unsupported VaR method: {method}")
                
        except Exception as e:
            logger.error(f"Error in VaR calculation: {e}")
            raise
    
    def run_stress_test(self, portfolio_data: Dict[str, any],
                       scenario: Dict[str, any] = None) -> Dict[str, any]:
        """Run stress test"""
        return self.stress_tester.run_stress_test(portfolio_data, scenario)
    
    def run_multiple_stress_scenarios(self, portfolio_data: Dict[str, any],
                                    scenarios: List[Dict[str, any]] = None) -> Dict[str, any]:
        """Run multiple stress scenarios"""
        return self.stress_tester.run_multiple_scenarios(portfolio_data, scenarios)
    
    def calculate_risk_attribution(self, portfolio_data: Dict[str, any],
                                 method: str = 'factor') -> Dict[str, any]:
        """Calculate risk attribution"""
        return self.risk_attributor.calculate_risk_attribution(portfolio_data, method)
    
    def calculate_incremental_var(self, portfolio_data: Dict[str, any],
                                new_position: Dict[str, any]) -> Dict[str, any]:
        """
        Calculate incremental VaR
        
        Args:
            portfolio_data: Current portfolio data
            new_position: New position to add
            
        Returns:
            Incremental VaR results
        """
        try:
            # Calculate current portfolio VaR
            current_returns = np.dot(portfolio_data['returns'], portfolio_data['weights'])
            current_var = self.calculate_var(pd.Series(current_returns), method='historical')
            
            # Add new position
            new_weights = np.append(portfolio_data['weights'], new_position['weight'])
            new_returns = portfolio_data['returns'].copy()
            new_returns[new_position['asset']] = new_position['returns']
            
            # Calculate new portfolio VaR
            new_portfolio_returns = np.dot(new_returns, new_weights)
            new_var = self.calculate_var(pd.Series(new_portfolio_returns), method='historical')
            
            # Calculate incremental VaR
            incremental_var = new_var['historical_var'] - current_var['historical_var']
            
            return {
                'current_var': current_var['historical_var'],
                'new_var': new_var['historical_var'],
                'incremental_var': incremental_var,
                'position_size': new_position['weight'],
                'position_asset': new_position['asset']
            }
            
        except Exception as e:
            logger.error(f"Error in incremental VaR calculation: {e}")
            raise
    
    def optimize_risk_budget(self, portfolio_data: Dict[str, any],
                           risk_budget: Dict[str, float],
                           optimization_constraints: Dict = None) -> Dict[str, any]:
        """
        Optimize portfolio weights based on risk budget
        
        Args:
            portfolio_data: Portfolio data
            risk_budget: Target risk budget for each asset
            optimization_constraints: Optimization constraints
            
        Returns:
            Risk budget optimization results
        """
        try:
            weights = np.array(portfolio_data['weights'])
            returns = portfolio_data['returns']
            asset_names = portfolio_data['asset_names']
            
            # Define objective function (minimize tracking error to risk budget)
            def objective(new_weights):
                # Calculate risk contributions
                cov_matrix = returns.cov()
                portfolio_vol = np.sqrt(np.dot(new_weights.T, np.dot(cov_matrix, new_weights)))
                marginal_contributions = np.dot(cov_matrix, new_weights) / portfolio_vol
                risk_contributions = new_weights * marginal_contributions
                
                # Calculate tracking error to risk budget
                tracking_error = 0
                for i, asset in enumerate(asset_names):
                    if asset in risk_budget:
                        target_contribution = risk_budget[asset] * portfolio_vol
                        tracking_error += (risk_contributions[i] - target_contribution)**2
                
                return tracking_error
            
            # Define constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Budget constraint
            ]
            
            if optimization_constraints:
                if 'min_weight' in optimization_constraints:
                    min_weight = optimization_constraints['min_weight']
                    for i in range(len(asset_names)):
                        constraints.append({
                            'type': 'ineq',
                            'fun': lambda x, i=i: x[i] - min_weight
                        })
                
                if 'max_weight' in optimization_constraints:
                    max_weight = optimization_constraints['max_weight']
                    for i in range(len(asset_names)):
                        constraints.append({
                            'type': 'ineq',
                            'fun': lambda x, i=i: max_weight - x[i]
                        })
            
            # Optimize
            result = minimize(objective, weights,
                            method='SLSQP',
                            constraints=constraints,
                            bounds=[(0, 1)] * len(asset_names))
            
            if result.success:
                optimal_weights = result.x
                
                # Calculate optimal risk contributions
                cov_matrix = returns.cov()
                portfolio_vol = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
                marginal_contributions = np.dot(cov_matrix, optimal_weights) / portfolio_vol
                risk_contributions = optimal_weights * marginal_contributions
                
                return {
                    'optimal_weights': optimal_weights.tolist(),
                    'risk_contributions': risk_contributions.tolist(),
                    'portfolio_volatility': portfolio_vol,
                    'optimization_success': True,
                    'tracking_error': result.fun
                }
            else:
                raise ValueError(f"Risk budget optimization failed: {result.message}")
                
        except Exception as e:
            logger.error(f"Error in risk budget optimization: {e}")
            raise
    
    def calculate_tail_risk_measures(self, returns: pd.Series, 
                                   confidence_levels: List[float] = None) -> Dict[str, any]:
        """
        Calculate various tail risk measures
        
        Args:
            returns: Asset or portfolio returns
            confidence_levels: List of confidence levels
            
        Returns:
            Tail risk measures
        """
        try:
            if confidence_levels is None:
                confidence_levels = [0.95, 0.99, 0.995]
            
            tail_measures = {}
            
            for confidence in confidence_levels:
                # VaR
                var_result = self.calculate_var(returns, method='historical', 
                                              confidence_level=confidence)
                tail_measures[f'var_{int(confidence*100)}'] = var_result['historical_var']
                tail_measures[f'cvar_{int(confidence*100)}'] = var_result['conditional_var']
            
            # Additional tail risk measures
            tail_measures['skewness'] = stats.skew(returns)
            tail_measures['kurtosis'] = stats.kurtosis(returns)
            tail_measures['max_drawdown'] = self._calculate_max_drawdown(returns)
            tail_measures['tail_dependence'] = self._calculate_tail_dependence(returns)
            
            return tail_measures
            
        except Exception as e:
            logger.error(f"Error in tail risk measures calculation: {e}")
            raise
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown"""
        try:
            cumulative_returns = (1 + returns).cumprod()
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            return drawdown.min()
        except Exception as e:
            logger.error(f"Error in max drawdown calculation: {e}")
            raise
    
    def _calculate_tail_dependence(self, returns: pd.Series) -> float:
        """Calculate tail dependence (simplified)"""
        try:
            # Simplified tail dependence measure
            threshold = np.percentile(returns, 5)
            tail_events = returns <= threshold
            return tail_events.mean()
        except Exception as e:
            logger.error(f"Error in tail dependence calculation: {e}")
            raise 