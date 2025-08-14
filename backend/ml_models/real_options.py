"""
Real Options Valuation Engine
Phase 5A Implementation - Advanced Financial Models

This module implements comprehensive real options analysis for strategic investment decisions.
Includes Black-Scholes, binomial tree, Monte Carlo, and compound options models.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from scipy.optimize import minimize
import logging
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OptionParameters:
    """Data class for option parameters"""
    current_value: float
    exercise_price: float
    time_to_expiry: float
    volatility: float
    risk_free_rate: float
    dividend_yield: float = 0.0

@dataclass
class OptionResults:
    """Data class for option calculation results"""
    option_value: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    intrinsic_value: float
    time_value: float

class BlackScholesModel:
    """Black-Scholes option pricing model for real options"""
    
    def __init__(self):
        self.name = "Black-Scholes"
    
    def calculate_call_option(self, params: OptionParameters) -> OptionResults:
        """Calculate call option value using Black-Scholes"""
        S = params.current_value
        K = params.exercise_price
        T = params.time_to_expiry
        sigma = params.volatility
        r = params.risk_free_rate
        q = params.dividend_yield
        
        if T <= 0:
            return OptionResults(
                option_value=max(S - K, 0),
                delta=1.0 if S > K else 0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0,
                intrinsic_value=max(S - K, 0),
                time_value=0.0
            )
        
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Option value
        call_value = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        
        # Greeks
        delta = np.exp(-q * T) * norm.cdf(d1)
        gamma = np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))
        theta = (-S * np.exp(-q * T) * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - 
                r * K * np.exp(-r * T) * norm.cdf(d2) + 
                q * S * np.exp(-q * T) * norm.cdf(d1)) / 365  # Daily theta
        vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T) / 100  # Per 1% vol change
        rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100  # Per 1% rate change
        
        intrinsic_value = max(S - K, 0)
        time_value = call_value - intrinsic_value
        
        return OptionResults(
            option_value=call_value,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            intrinsic_value=intrinsic_value,
            time_value=time_value
        )
    
    def calculate_put_option(self, params: OptionParameters) -> OptionResults:
        """Calculate put option value using Black-Scholes"""
        S = params.current_value
        K = params.exercise_price
        T = params.time_to_expiry
        sigma = params.volatility
        r = params.risk_free_rate
        q = params.dividend_yield
        
        if T <= 0:
            return OptionResults(
                option_value=max(K - S, 0),
                delta=-1.0 if S < K else 0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0,
                intrinsic_value=max(K - S, 0),
                time_value=0.0
            )
        
        d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        # Option value
        put_value = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
        
        # Greeks
        delta = np.exp(-q * T) * (norm.cdf(d1) - 1)
        gamma = np.exp(-q * T) * norm.pdf(d1) / (S * sigma * np.sqrt(T))
        theta = (-S * np.exp(-q * T) * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) + 
                r * K * np.exp(-r * T) * norm.cdf(-d2) - 
                q * S * np.exp(-q * T) * norm.cdf(-d1)) / 365
        vega = S * np.exp(-q * T) * norm.pdf(d1) * np.sqrt(T) / 100
        rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
        
        intrinsic_value = max(K - S, 0)
        time_value = put_value - intrinsic_value
        
        return OptionResults(
            option_value=put_value,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            intrinsic_value=intrinsic_value,
            time_value=time_value
        )

class BinomialTreeModel:
    """Binomial tree option pricing model"""
    
    def __init__(self, steps: int = 100):
        self.steps = steps
        self.name = "Binomial Tree"
    
    def calculate_option_value(self, params: OptionParameters, option_type: str = 'call') -> OptionResults:
        """Calculate option value using binomial tree"""
        S = params.current_value
        K = params.exercise_price
        T = params.time_to_expiry
        sigma = params.volatility
        r = params.risk_free_rate
        q = params.dividend_yield
        n = self.steps
        
        if T <= 0:
            intrinsic_value = max(S - K, 0) if option_type == 'call' else max(K - S, 0)
            return OptionResults(
                option_value=intrinsic_value,
                delta=1.0 if (option_type == 'call' and S > K) or (option_type == 'put' and S < K) else 0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0,
                intrinsic_value=intrinsic_value,
                time_value=0.0
            )
        
        dt = T / n
        u = np.exp(sigma * np.sqrt(dt))
        d = 1 / u
        p = (np.exp((r - q) * dt) - d) / (u - d)
        
        # Create binomial tree
        option_values = np.zeros((n + 1, n + 1))
        
        # Calculate option values at expiration
        for j in range(n + 1):
            S_T = S * (u ** (n - j)) * (d ** j)
            if option_type == 'call':
                option_values[n, j] = max(S_T - K, 0)
            else:
                option_values[n, j] = max(K - S_T, 0)
        
        # Backward induction
        for i in range(n - 1, -1, -1):
            for j in range(i + 1):
                S_t = S * (u ** (i - j)) * (d ** j)
                option_values[i, j] = np.exp(-r * dt) * (p * option_values[i + 1, j] + 
                                                        (1 - p) * option_values[i + 1, j + 1])
        
        option_value = option_values[0, 0]
        
        # Calculate Greeks (approximate)
        delta = (option_values[1, 0] - option_values[1, 1]) / (S * (u - d))
        gamma = ((option_values[2, 0] - option_values[2, 1]) - 
                (option_values[2, 1] - option_values[2, 2])) / (S * (u - d))**2
        
        intrinsic_value = max(S - K, 0) if option_type == 'call' else max(K - S, 0)
        time_value = option_value - intrinsic_value
        
        return OptionResults(
            option_value=option_value,
            delta=delta,
            gamma=gamma,
            theta=0.0,  # Would need more complex calculation
            vega=0.0,   # Would need more complex calculation
            rho=0.0,    # Would need more complex calculation
            intrinsic_value=intrinsic_value,
            time_value=time_value
        )

class MonteCarloOptionsModel:
    """Monte Carlo simulation for option pricing"""
    
    def __init__(self, simulations: int = 10000):
        self.simulations = simulations
        self.name = "Monte Carlo"
    
    def calculate_option_value(self, params: OptionParameters, option_type: str = 'call') -> OptionResults:
        """Calculate option value using Monte Carlo simulation"""
        S = params.current_value
        K = params.exercise_price
        T = params.time_to_expiry
        sigma = params.volatility
        r = params.risk_free_rate
        q = params.dividend_yield
        n_sims = self.simulations
        
        if T <= 0:
            intrinsic_value = max(S - K, 0) if option_type == 'call' else max(K - S, 0)
            return OptionResults(
                option_value=intrinsic_value,
                delta=1.0 if (option_type == 'call' and S > K) or (option_type == 'put' and S < K) else 0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0,
                intrinsic_value=intrinsic_value,
                time_value=0.0
            )
        
        # Generate random paths
        np.random.seed(42)  # For reproducibility
        Z = np.random.standard_normal(n_sims)
        
        # Calculate stock prices at expiration
        S_T = S * np.exp((r - q - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)
        
        # Calculate option payoffs
        if option_type == 'call':
            payoffs = np.maximum(S_T - K, 0)
        else:
            payoffs = np.maximum(K - S_T, 0)
        
        # Discount to present value
        option_value = np.exp(-r * T) * np.mean(payoffs)
        
        # Calculate Greeks using finite differences
        delta = self._calculate_delta(params, option_type)
        gamma = self._calculate_gamma(params, option_type)
        
        intrinsic_value = max(S - K, 0) if option_type == 'call' else max(K - S, 0)
        time_value = option_value - intrinsic_value
        
        return OptionResults(
            option_value=option_value,
            delta=delta,
            gamma=gamma,
            theta=0.0,  # Would need more complex calculation
            vega=0.0,   # Would need more complex calculation
            rho=0.0,    # Would need more complex calculation
            intrinsic_value=intrinsic_value,
            time_value=time_value
        )
    
    def _calculate_delta(self, params: OptionParameters, option_type: str) -> float:
        """Calculate delta using finite differences"""
        h = params.current_value * 0.01  # 1% change
        
        # Original parameters
        params_orig = OptionParameters(
            current_value=params.current_value,
            exercise_price=params.exercise_price,
            time_to_expiry=params.time_to_expiry,
            volatility=params.volatility,
            risk_free_rate=params.risk_free_rate,
            dividend_yield=params.dividend_yield
        )
        
        # Up parameters
        params_up = OptionParameters(
            current_value=params.current_value + h,
            exercise_price=params.exercise_price,
            time_to_expiry=params.time_to_expiry,
            volatility=params.volatility,
            risk_free_rate=params.risk_free_rate,
            dividend_yield=params.dividend_yield
        )
        
        # Down parameters
        params_down = OptionParameters(
            current_value=params.current_value - h,
            exercise_price=params.exercise_price,
            time_to_expiry=params.time_to_expiry,
            volatility=params.volatility,
            risk_free_rate=params.risk_free_rate,
            dividend_yield=params.dividend_yield
        )
        
        # Calculate option values
        value_orig = self._simulate_option_value(params_orig, option_type)
        value_up = self._simulate_option_value(params_up, option_type)
        value_down = self._simulate_option_value(params_down, option_type)
        
        # Calculate delta using central difference
        delta = (value_up - value_down) / (2 * h)
        return delta
    
    def _calculate_gamma(self, params: OptionParameters, option_type: str) -> float:
        """Calculate gamma using finite differences"""
        h = params.current_value * 0.01  # 1% change
        
        # Original parameters
        params_orig = OptionParameters(
            current_value=params.current_value,
            exercise_price=params.exercise_price,
            time_to_expiry=params.time_to_expiry,
            volatility=params.volatility,
            risk_free_rate=params.risk_free_rate,
            dividend_yield=params.dividend_yield
        )
        
        # Up parameters
        params_up = OptionParameters(
            current_value=params.current_value + h,
            exercise_price=params.exercise_price,
            time_to_expiry=params.time_to_expiry,
            volatility=params.volatility,
            risk_free_rate=params.risk_free_rate,
            dividend_yield=params.dividend_yield
        )
        
        # Down parameters
        params_down = OptionParameters(
            current_value=params.current_value - h,
            exercise_price=params.exercise_price,
            time_to_expiry=params.time_to_expiry,
            volatility=params.volatility,
            risk_free_rate=params.risk_free_rate,
            dividend_yield=params.dividend_yield
        )
        
        # Calculate option values
        value_orig = self._simulate_option_value(params_orig, option_type)
        value_up = self._simulate_option_value(params_up, option_type)
        value_down = self._simulate_option_value(params_down, option_type)
        
        # Calculate gamma using central difference
        gamma = (value_up - 2 * value_orig + value_down) / (h**2)
        return gamma
    
    def _simulate_option_value(self, params: OptionParameters, option_type: str) -> float:
        """Helper method to simulate option value"""
        S = params.current_value
        K = params.exercise_price
        T = params.time_to_expiry
        sigma = params.volatility
        r = params.risk_free_rate
        q = params.dividend_yield
        
        np.random.seed(42)
        Z = np.random.standard_normal(self.simulations)
        S_T = S * np.exp((r - q - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)
        
        if option_type == 'call':
            payoffs = np.maximum(S_T - K, 0)
        else:
            payoffs = np.maximum(K - S_T, 0)
        
        return np.exp(-r * T) * np.mean(payoffs)

class CompoundOptionsModel:
    """Compound options model for options on options"""
    
    def __init__(self):
        self.name = "Compound Options"
    
    def calculate_compound_option(self, params: OptionParameters, 
                                compound_params: OptionParameters,
                                option_type: str = 'call') -> Dict:
        """Calculate compound option value"""
        # This is a simplified implementation
        # In practice, compound options require more complex calculations
        
        # Calculate the underlying option value
        underlying_option = BlackScholesModel().calculate_call_option(params)
        
        # Calculate the compound option value
        compound_option = BlackScholesModel().calculate_call_option(compound_params)
        
        return {
            'underlying_option_value': underlying_option.option_value,
            'compound_option_value': compound_option.option_value,
            'total_value': underlying_option.option_value + compound_option.option_value
        }

class RealOptionsValuation:
    """Main real options valuation engine"""
    
    def __init__(self):
        self.models = {
            'black_scholes': BlackScholesModel(),
            'binomial': BinomialTreeModel(),
            'monte_carlo': MonteCarloOptionsModel(),
            'compound': CompoundOptionsModel()
        }
        logger.info("Real Options Valuation Engine initialized")
    
    def calculate_expansion_option(self, current_value: float, expansion_cost: float,
                                 time_to_expiry: float, volatility: float, 
                                 risk_free_rate: float, expansion_multiplier: float = 2.0) -> Dict:
        """Calculate expansion option value"""
        # Expansion option is a call option on the expanded project
        expanded_value = current_value * expansion_multiplier
        
        params = OptionParameters(
            current_value=expanded_value,
            exercise_price=expansion_cost,
            time_to_expiry=time_to_expiry,
            volatility=volatility,
            risk_free_rate=risk_free_rate
        )
        
        results = self.models['black_scholes'].calculate_call_option(params)
        
        return {
            'option_type': 'expansion',
            'current_value': current_value,
            'expanded_value': expanded_value,
            'expansion_cost': expansion_cost,
            'option_value': results.option_value,
            'delta': results.delta,
            'gamma': results.gamma,
            'theta': results.theta,
            'vega': results.vega,
            'rho': results.rho,
            'intrinsic_value': results.intrinsic_value,
            'time_value': results.time_value,
            'model_used': 'black_scholes'
        }
    
    def calculate_abandonment_option(self, current_value: float, salvage_value: float,
                                   time_to_expiry: float, volatility: float, 
                                   risk_free_rate: float) -> Dict:
        """Calculate abandonment option value"""
        # Abandonment option is a put option
        params = OptionParameters(
            current_value=current_value,
            exercise_price=salvage_value,
            time_to_expiry=time_to_expiry,
            volatility=volatility,
            risk_free_rate=risk_free_rate
        )
        
        results = self.models['black_scholes'].calculate_put_option(params)
        
        return {
            'option_type': 'abandonment',
            'current_value': current_value,
            'salvage_value': salvage_value,
            'option_value': results.option_value,
            'delta': results.delta,
            'gamma': results.gamma,
            'theta': results.theta,
            'vega': results.vega,
            'rho': results.rho,
            'intrinsic_value': results.intrinsic_value,
            'time_value': results.time_value,
            'model_used': 'black_scholes'
        }
    
    def calculate_timing_option(self, project_value: float, investment_cost: float,
                              time_horizon: float, volatility: float, 
                              risk_free_rate: float) -> Dict:
        """Calculate optimal investment timing option"""
        # Timing option is a call option with optimal exercise
        params = OptionParameters(
            current_value=project_value,
            exercise_price=investment_cost,
            time_to_expiry=time_horizon,
            volatility=volatility,
            risk_free_rate=risk_free_rate
        )
        
        results = self.models['black_scholes'].calculate_call_option(params)
        
        # Calculate optimal exercise threshold
        optimal_threshold = investment_cost * np.exp(risk_free_rate * time_horizon)
        
        return {
            'option_type': 'timing',
            'project_value': project_value,
            'investment_cost': investment_cost,
            'option_value': results.option_value,
            'optimal_exercise_threshold': optimal_threshold,
            'should_exercise_now': project_value >= optimal_threshold,
            'delta': results.delta,
            'gamma': results.gamma,
            'theta': results.theta,
            'vega': results.vega,
            'rho': results.rho,
            'model_used': 'black_scholes'
        }
    
    def calculate_compound_option(self, underlying_value: float, exercise_prices: List[float],
                                time_periods: List[float], volatility: float, 
                                risk_free_rate: float) -> Dict:
        """Calculate compound option value"""
        if len(exercise_prices) != 2 or len(time_periods) != 2:
            raise ValueError("Compound options require exactly 2 exercise prices and 2 time periods")
        
        # First option (underlying)
        params1 = OptionParameters(
            current_value=underlying_value,
            exercise_price=exercise_prices[0],
            time_to_expiry=time_periods[0],
            volatility=volatility,
            risk_free_rate=risk_free_rate
        )
        
        # Second option (compound)
        params2 = OptionParameters(
            current_value=underlying_value,
            exercise_price=exercise_prices[1],
            time_to_expiry=time_periods[1],
            volatility=volatility,
            risk_free_rate=risk_free_rate
        )
        
        results = self.models['compound'].calculate_compound_option(params1, params2)
        
        return {
            'option_type': 'compound',
            'underlying_value': underlying_value,
            'first_exercise_price': exercise_prices[0],
            'second_exercise_price': exercise_prices[1],
            'first_time_period': time_periods[0],
            'second_time_period': time_periods[1],
            'underlying_option_value': results['underlying_option_value'],
            'compound_option_value': results['compound_option_value'],
            'total_value': results['total_value'],
            'model_used': 'compound'
        }
    
    def calculate_greeks(self, option_value: float, underlying_price: float, 
                        volatility: float, time_to_expiry: float, 
                        risk_free_rate: float, option_type: str = 'call') -> Dict:
        """Calculate option Greeks"""
        params = OptionParameters(
            current_value=underlying_price,
            exercise_price=underlying_price,  # At-the-money for Greeks calculation
            time_to_expiry=time_to_expiry,
            volatility=volatility,
            risk_free_rate=risk_free_rate
        )
        
        if option_type == 'call':
            results = self.models['black_scholes'].calculate_call_option(params)
        else:
            results = self.models['black_scholes'].calculate_put_option(params)
        
        return {
            'delta': results.delta,
            'gamma': results.gamma,
            'theta': results.theta,
            'vega': results.vega,
            'rho': results.rho,
            'option_type': option_type
        }
    
    def estimate_volatility(self, historical_data: List[float], method: str = 'historical') -> float:
        """Estimate volatility from historical data"""
        if method == 'historical':
            returns = np.diff(np.log(historical_data))
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            return volatility
        elif method == 'implied':
            # Simplified implied volatility calculation
            # In practice, this would use numerical methods to solve for volatility
            return 0.3  # Default value
        else:
            raise ValueError(f"Unknown volatility estimation method: {method}")
    
    def run_sensitivity_analysis(self, base_params: Dict, parameter: str, 
                               range_values: List[float]) -> Dict:
        """Run sensitivity analysis for a parameter"""
        results = []
        
        for value in range_values:
            # Create new parameters with modified value
            test_params = base_params.copy()
            test_params[parameter] = value
            
            # Calculate option value
            if test_params.get('option_type') == 'expansion':
                option_result = self.calculate_expansion_option(
                    test_params['current_value'],
                    test_params['expansion_cost'],
                    test_params['time_to_expiry'],
                    test_params['volatility'],
                    test_params['risk_free_rate']
                )
            elif test_params.get('option_type') == 'abandonment':
                option_result = self.calculate_abandonment_option(
                    test_params['current_value'],
                    test_params['salvage_value'],
                    test_params['time_to_expiry'],
                    test_params['volatility'],
                    test_params['risk_free_rate']
                )
            else:
                continue
            
            results.append({
                'parameter_value': value,
                'option_value': option_result['option_value'],
                'delta': option_result['delta'],
                'gamma': option_result['gamma'],
                'theta': option_result['theta'],
                'vega': option_result['vega']
            })
        
        return {
            'parameter': parameter,
            'range_values': range_values,
            'results': results
        }
    
    def get_available_models(self) -> List[str]:
        """Get list of available pricing models"""
        return list(self.models.keys())
    
    def get_model_info(self, model_name: str) -> Dict:
        """Get information about a specific model"""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")
        
        model = self.models[model_name]
        return {
            'name': model.name,
            'description': f"{model.name} option pricing model",
            'parameters': self._get_model_parameters(model_name)
        }
    
    def _get_model_parameters(self, model_name: str) -> List[str]:
        """Get required parameters for a model"""
        base_params = ['current_value', 'exercise_price', 'time_to_expiry', 
                      'volatility', 'risk_free_rate']
        
        if model_name == 'monte_carlo':
            base_params.append('simulations')
        elif model_name == 'binomial':
            base_params.append('steps')
        
        return base_params 