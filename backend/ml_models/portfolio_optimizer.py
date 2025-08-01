"""
Enhanced Portfolio Optimization Module
Implements comprehensive portfolio optimization and analysis tools
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy import stats
import logging
from typing import Dict, List, Tuple, Optional, Union
import json

logger = logging.getLogger(__name__)

class MeanVarianceOptimizer:
    """Mean-Variance Portfolio Optimization"""
    
    def __init__(self):
        self.model_name = "Mean-Variance"
    
    def optimize(self, returns: pd.DataFrame, risk_free_rate: float = 0.02,
                target_return: float = None, target_volatility: float = None,
                constraints: Dict = None) -> Dict[str, any]:
        """
        Mean-variance portfolio optimization
        
        Args:
            returns: Asset returns DataFrame
            risk_free_rate: Risk-free rate
            target_return: Target portfolio return (optional)
            target_volatility: Target portfolio volatility (optional)
            constraints: Optimization constraints
            
        Returns:
            Optimization results
        """
        try:
            # Calculate expected returns and covariance matrix
            expected_returns = returns.mean()
            cov_matrix = returns.cov()
            
            n_assets = len(expected_returns)
            
            # Define objective function (minimize portfolio variance)
            def objective(weights):
                portfolio_var = np.dot(weights.T, np.dot(cov_matrix, weights))
                return portfolio_var
            
            # Define constraints
            constraints_list = []
            
            # Budget constraint (weights sum to 1)
            constraints_list.append({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            
            # Target return constraint (if specified)
            if target_return is not None:
                constraints_list.append({
                    'type': 'eq', 
                    'fun': lambda x: np.dot(x, expected_returns) - target_return
                })
            
            # Target volatility constraint (if specified)
            if target_volatility is not None:
                constraints_list.append({
                    'type': 'eq',
                    'fun': lambda x: np.sqrt(np.dot(x.T, np.dot(cov_matrix, x))) - target_volatility
                })
            
            # Additional constraints
            if constraints:
                if 'min_weight' in constraints:
                    min_weight = constraints['min_weight']
                    for i in range(n_assets):
                        constraints_list.append({
                            'type': 'ineq',
                            'fun': lambda x, i=i: x[i] - min_weight
                        })
                
                if 'max_weight' in constraints:
                    max_weight = constraints['max_weight']
                    for i in range(n_assets):
                        constraints_list.append({
                            'type': 'ineq',
                            'fun': lambda x, i=i: max_weight - x[i]
                        })
            
            # Initial guess (equal weights)
            initial_weights = np.array([1/n_assets] * n_assets)
            
            # Optimize
            result = minimize(objective, initial_weights, 
                            method='SLSQP',
                            constraints=constraints_list,
                            bounds=[(0, 1)] * n_assets)
            
            if result.success:
                optimal_weights = result.x
                portfolio_return = np.dot(optimal_weights, expected_returns)
                portfolio_volatility = np.sqrt(np.dot(optimal_weights.T, 
                                                    np.dot(cov_matrix, optimal_weights)))
                sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
                
                return {
                    'weights': optimal_weights.tolist(),
                    'expected_return': portfolio_return,
                    'volatility': portfolio_volatility,
                    'sharpe_ratio': sharpe_ratio,
                    'optimization_success': True,
                    'assets': expected_returns.index.tolist()
                }
            else:
                raise ValueError(f"Optimization failed: {result.message}")
                
        except Exception as e:
            logger.error(f"Error in mean-variance optimization: {e}")
            raise
    
    def calculate_efficient_frontier(self, returns: pd.DataFrame, 
                                   risk_free_rate: float = 0.02,
                                   num_portfolios: int = 100) -> Dict[str, any]:
        """
        Calculate efficient frontier
        
        Args:
            returns: Asset returns DataFrame
            risk_free_rate: Risk-free rate
            num_portfolios: Number of portfolios to generate
            
        Returns:
            Efficient frontier data
        """
        try:
            expected_returns = returns.mean()
            cov_matrix = returns.cov()
            
            # Generate target returns
            min_return = expected_returns.min()
            max_return = expected_returns.max()
            target_returns = np.linspace(min_return, max_return, num_portfolios)
            
            efficient_portfolios = []
            
            for target_return in target_returns:
                try:
                    result = self.optimize(returns, risk_free_rate, target_return)
                    if result['optimization_success']:
                        efficient_portfolios.append({
                            'return': result['expected_return'],
                            'volatility': result['volatility'],
                            'sharpe_ratio': result['sharpe_ratio'],
                            'weights': result['weights']
                        })
                except:
                    continue
            
            return {
                'efficient_frontier': efficient_portfolios,
                'risk_free_rate': risk_free_rate,
                'num_portfolios': len(efficient_portfolios)
            }
            
        except Exception as e:
            logger.error(f"Error in efficient frontier calculation: {e}")
            raise


class BlackLittermanOptimizer:
    """Black-Litterman Portfolio Optimization"""
    
    def __init__(self):
        self.model_name = "Black-Litterman"
    
    def optimize(self, market_caps: pd.Series, returns: pd.DataFrame,
                views: Dict[str, any], view_confidences: Dict[str, float],
                risk_aversion: float = 2.5, tau: float = 0.05) -> Dict[str, any]:
        """
        Black-Litterman portfolio optimization
        
        Args:
            market_caps: Market capitalization weights
            returns: Asset returns DataFrame
            views: Investor views (dictionary with view specifications)
            view_confidences: Confidence levels for views
            risk_aversion: Risk aversion parameter
            tau: Prior uncertainty parameter
            
        Returns:
            Black-Litterman optimization results
        """
        try:
            # Calculate market equilibrium returns
            cov_matrix = returns.cov()
            market_weights = market_caps / market_caps.sum()
            equilibrium_returns = risk_aversion * np.dot(cov_matrix, market_weights)
            
            # Process views
            P, Q, Omega = self._process_views(views, view_confidences, returns.columns)
            
            # Calculate posterior returns and covariance
            tau_cov = tau * cov_matrix
            M1 = np.linalg.inv(tau_cov)
            M2 = np.dot(P.T, np.dot(np.linalg.inv(Omega), P))
            M3 = np.dot(M1, equilibrium_returns)
            M4 = np.dot(P.T, np.dot(np.linalg.inv(Omega), Q))
            
            posterior_cov = np.linalg.inv(M1 + M2)
            posterior_returns = np.dot(posterior_cov, M3 + M4)
            
            # Optimize using mean-variance with posterior estimates
            mv_optimizer = MeanVarianceOptimizer()
            
            # Create returns DataFrame with posterior returns
            posterior_returns_series = pd.Series(posterior_returns, index=returns.columns)
            
            # Use historical covariance but posterior returns
            result = mv_optimizer.optimize(returns, target_return=posterior_returns_series.mean())
            
            result['model'] = 'Black-Litterman'
            result['posterior_returns'] = posterior_returns.tolist()
            result['equilibrium_returns'] = equilibrium_returns.tolist()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Black-Litterman optimization: {e}")
            raise
    
    def _process_views(self, views: Dict[str, any], view_confidences: Dict[str, float],
                      asset_names: List[str]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Process investor views into matrices
        
        Args:
            views: Investor views
            view_confidences: Confidence levels
            asset_names: Asset names
            
        Returns:
            P, Q, Omega matrices
        """
        try:
            num_views = len(views)
            num_assets = len(asset_names)
            
            P = np.zeros((num_views, num_assets))
            Q = np.zeros(num_views)
            Omega = np.zeros((num_views, num_views))
            
            for i, (view_name, view_data) in enumerate(views.items()):
                # Extract view components
                assets = view_data['assets']
                weights = view_data['weights']
                expected_return = view_data['expected_return']
                
                # Build P matrix
                for j, asset in enumerate(assets):
                    # Convert asset_names to list if it's a pandas Index
                    asset_names_list = asset_names.tolist() if hasattr(asset_names, 'tolist') else asset_names
                    asset_idx = asset_names_list.index(asset)
                    P[i, asset_idx] = weights[j]
                
                # Build Q matrix
                Q[i] = expected_return
                
                # Build Omega matrix (diagonal with view confidences)
                confidence = view_confidences.get(view_name, 0.5)
                Omega[i, i] = 1 / confidence
            
            return P, Q, Omega
            
        except Exception as e:
            logger.error(f"Error in view processing: {e}")
            raise


class RiskParityOptimizer:
    """Risk Parity Portfolio Optimization"""
    
    def __init__(self):
        self.model_name = "Risk Parity"
    
    def optimize(self, returns: pd.DataFrame, target_volatility: float = None) -> Dict[str, any]:
        """
        Risk parity portfolio optimization
        
        Args:
            returns: Asset returns DataFrame
            target_volatility: Target portfolio volatility (optional)
            
        Returns:
            Risk parity optimization results
        """
        try:
            cov_matrix = returns.cov()
            n_assets = len(returns.columns)
            
            # Define objective function (minimize variance of risk contributions)
            def objective(weights):
                portfolio_var = np.dot(weights.T, np.dot(cov_matrix, weights))
                portfolio_vol = np.sqrt(portfolio_var)
                
                # Calculate risk contributions
                risk_contributions = []
                for i in range(n_assets):
                    # Convert cov_matrix to numpy array for proper indexing
                    cov_array = cov_matrix.values if hasattr(cov_matrix, 'values') else cov_matrix
                    marginal_risk = np.dot(cov_array[i, :], weights) / portfolio_vol
                    risk_contributions.append(weights[i] * marginal_risk)
                
                # Variance of risk contributions
                risk_contrib_var = np.var(risk_contributions)
                return risk_contrib_var
            
            # Define constraints
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Budget constraint
            ]
            
            if target_volatility is not None:
                constraints.append({
                    'type': 'eq',
                    'fun': lambda x: np.sqrt(np.dot(x.T, np.dot(cov_matrix, x))) - target_volatility
                })
            
            # Initial guess (equal weights)
            initial_weights = np.array([1/n_assets] * n_assets)
            
            # Optimize
            result = minimize(objective, initial_weights,
                            method='SLSQP',
                            constraints=constraints,
                            bounds=[(0, 1)] * n_assets)
            
            if result.success:
                optimal_weights = result.x
                portfolio_var = np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights))
                portfolio_vol = np.sqrt(portfolio_var)
                
                # Calculate risk contributions
                risk_contributions = []
                cov_array = cov_matrix.values if hasattr(cov_matrix, 'values') else cov_matrix
                for i in range(n_assets):
                    marginal_risk = np.dot(cov_array[i, :], optimal_weights) / portfolio_vol
                    risk_contributions.append(optimal_weights[i] * marginal_risk)
                
                return {
                    'weights': optimal_weights.tolist(),
                    'volatility': portfolio_vol,
                    'risk_contributions': risk_contributions,
                    'optimization_success': True,
                    'assets': returns.columns.tolist()
                }
            else:
                raise ValueError(f"Optimization failed: {result.message}")
                
        except Exception as e:
            logger.error(f"Error in risk parity optimization: {e}")
            raise


class MaxSharpeOptimizer:
    """Maximum Sharpe Ratio Portfolio Optimization"""
    
    def __init__(self):
        self.model_name = "Maximum Sharpe Ratio"
    
    def optimize(self, returns: pd.DataFrame, risk_free_rate: float = 0.02,
                constraints: Dict = None) -> Dict[str, any]:
        """
        Maximum Sharpe ratio portfolio optimization
        
        Args:
            returns: Asset returns DataFrame
            risk_free_rate: Risk-free rate
            constraints: Optimization constraints
            
        Returns:
            Maximum Sharpe ratio optimization results
        """
        try:
            expected_returns = returns.mean()
            cov_matrix = returns.cov()
            
            # Define objective function (maximize Sharpe ratio = minimize negative Sharpe ratio)
            def objective(weights):
                portfolio_return = np.dot(weights, expected_returns)
                portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_vol
                return -sharpe_ratio  # Minimize negative Sharpe ratio
            
            # Define constraints
            constraints_list = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}  # Budget constraint
            ]
            
            # Additional constraints
            if constraints:
                if 'min_weight' in constraints:
                    min_weight = constraints['min_weight']
                    for i in range(len(expected_returns)):
                        constraints_list.append({
                            'type': 'ineq',
                            'fun': lambda x, i=i: x[i] - min_weight
                        })
                
                if 'max_weight' in constraints:
                    max_weight = constraints['max_weight']
                    for i in range(len(expected_returns)):
                        constraints_list.append({
                            'type': 'ineq',
                            'fun': lambda x, i=i: max_weight - x[i]
                        })
            
            # Initial guess (equal weights)
            initial_weights = np.array([1/len(expected_returns)] * len(expected_returns))
            
            # Optimize
            result = minimize(objective, initial_weights,
                            method='SLSQP',
                            constraints=constraints_list,
                            bounds=[(0, 1)] * len(expected_returns))
            
            if result.success:
                optimal_weights = result.x
                portfolio_return = np.dot(optimal_weights, expected_returns)
                portfolio_vol = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
                sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_vol
                
                return {
                    'weights': optimal_weights.tolist(),
                    'expected_return': portfolio_return,
                    'volatility': portfolio_vol,
                    'sharpe_ratio': sharpe_ratio,
                    'optimization_success': True,
                    'assets': expected_returns.index.tolist()
                }
            else:
                raise ValueError(f"Optimization failed: {result.message}")
                
        except Exception as e:
            logger.error(f"Error in maximum Sharpe ratio optimization: {e}")
            raise


class PortfolioOptimizer:
    """Main portfolio optimization class"""
    
    def __init__(self):
        self.mean_variance_optimizer = MeanVarianceOptimizer()
        self.black_litterman_optimizer = BlackLittermanOptimizer()
        self.risk_parity_optimizer = RiskParityOptimizer()
        self.max_sharpe_optimizer = MaxSharpeOptimizer()
    
    def optimize_mean_variance(self, returns: pd.DataFrame, risk_free_rate: float = 0.02,
                             target_return: float = None, target_volatility: float = None,
                             constraints: Dict = None) -> Dict[str, any]:
        """Mean-variance optimization"""
        return self.mean_variance_optimizer.optimize(
            returns, risk_free_rate, target_return, target_volatility, constraints
        )
    
    def optimize_black_litterman(self, market_caps: pd.Series, returns: pd.DataFrame,
                                views: Dict[str, any], view_confidences: Dict[str, float],
                                risk_aversion: float = 2.5, tau: float = 0.05) -> Dict[str, any]:
        """Black-Litterman optimization"""
        return self.black_litterman_optimizer.optimize(
            market_caps, returns, views, view_confidences, risk_aversion, tau
        )
    
    def optimize_risk_parity(self, returns: pd.DataFrame, 
                           target_volatility: float = None) -> Dict[str, any]:
        """Risk parity optimization"""
        return self.risk_parity_optimizer.optimize(returns, target_volatility)
    
    def optimize_max_sharpe(self, returns: pd.DataFrame, risk_free_rate: float = 0.02,
                           constraints: Dict = None) -> Dict[str, any]:
        """Maximum Sharpe ratio optimization"""
        return self.max_sharpe_optimizer.optimize(returns, risk_free_rate, constraints)
    
    def calculate_efficient_frontier(self, returns: pd.DataFrame, 
                                   risk_free_rate: float = 0.02,
                                   num_portfolios: int = 100) -> Dict[str, any]:
        """Calculate efficient frontier"""
        return self.mean_variance_optimizer.calculate_efficient_frontier(
            returns, risk_free_rate, num_portfolios
        )
    
    def estimate_expected_returns(self, historical_returns: pd.DataFrame, 
                                method: str = 'historical') -> pd.Series:
        """
        Estimate expected returns
        
        Args:
            historical_returns: Historical returns DataFrame
            method: Estimation method ('historical', 'capm', 'factor_model')
            
        Returns:
            Expected returns Series
        """
        try:
            if method == 'historical':
                return historical_returns.mean()
            elif method == 'capm':
                # CAPM-based expected returns (simplified)
                market_return = historical_returns.mean().mean()  # Average market return
                risk_free_rate = 0.02
                betas = self._calculate_betas(historical_returns)
                return risk_free_rate + betas * (market_return - risk_free_rate)
            else:
                return historical_returns.mean()
                
        except Exception as e:
            logger.error(f"Error in expected returns estimation: {e}")
            raise
    
    def estimate_covariance_matrix(self, returns: pd.DataFrame, 
                                 method: str = 'sample') -> pd.DataFrame:
        """
        Estimate covariance matrix
        
        Args:
            returns: Returns DataFrame
            method: Estimation method ('sample', 'shrinkage', 'factor_model')
            
        Returns:
            Covariance matrix DataFrame
        """
        try:
            if method == 'sample':
                return returns.cov()
            elif method == 'shrinkage':
                # Ledoit-Wolf shrinkage estimator (simplified)
                sample_cov = returns.cov()
                target = np.eye(len(returns.columns)) * sample_cov.values.diagonal().mean()
                shrinkage = 0.1
                return pd.DataFrame(
                    (1 - shrinkage) * sample_cov + shrinkage * target,
                    index=returns.columns,
                    columns=returns.columns
                )
            else:
                return returns.cov()
                
        except Exception as e:
            logger.error(f"Error in covariance matrix estimation: {e}")
            raise
    
    def _calculate_betas(self, returns: pd.DataFrame) -> pd.Series:
        """Calculate asset betas relative to market"""
        try:
            market_returns = returns.mean(axis=1)  # Equal-weighted market
            betas = {}
            
            for asset in returns.columns:
                asset_returns = returns[asset]
                beta = np.cov(asset_returns, market_returns)[0, 1] / np.var(market_returns)
                betas[asset] = beta
            
            return pd.Series(betas)
            
        except Exception as e:
            logger.error(f"Error in beta calculation: {e}")
            raise
    
    def calculate_portfolio_metrics(self, weights: np.ndarray, returns: pd.DataFrame,
                                  risk_free_rate: float = 0.02) -> Dict[str, float]:
        """
        Calculate portfolio performance metrics
        
        Args:
            weights: Portfolio weights
            returns: Asset returns DataFrame
            risk_free_rate: Risk-free rate
            
        Returns:
            Portfolio metrics
        """
        try:
            expected_returns = returns.mean()
            cov_matrix = returns.cov()
            
            portfolio_return = np.dot(weights, expected_returns)
            portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_vol
            
            # Calculate VaR (simplified)
            portfolio_returns = np.dot(returns, weights)
            var_95 = np.percentile(portfolio_returns, 5)
            cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
            
            # Calculate maximum drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            return {
                'expected_return': portfolio_return,
                'volatility': portfolio_vol,
                'sharpe_ratio': sharpe_ratio,
                'var_95': var_95,
                'cvar_95': cvar_95,
                'max_drawdown': max_drawdown,
                'skewness': stats.skew(portfolio_returns),
                'kurtosis': stats.kurtosis(portfolio_returns)
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio metrics calculation: {e}")
            raise
    
    def rebalance_portfolio(self, current_weights: np.ndarray, target_weights: np.ndarray,
                           transaction_costs: float = 0.001) -> Dict[str, any]:
        """
        Calculate optimal rebalancing considering transaction costs
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            transaction_costs: Transaction cost rate
            
        Returns:
            Rebalancing results
        """
        try:
            # Calculate required trades
            trades = target_weights - current_weights
            
            # Calculate transaction costs
            total_transaction_cost = np.sum(np.abs(trades)) * transaction_costs
            
            # Calculate net portfolio value after costs
            net_value = 1 - total_transaction_cost
            
            return {
                'trades': trades.tolist(),
                'transaction_costs': total_transaction_cost,
                'net_value': net_value,
                'rebalancing_efficiency': net_value
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio rebalancing: {e}")
            raise
