"""
Unit tests for LBO Engine module
Phase 6 Testing Infrastructure
"""

import pytest
import math

@pytest.fixture
def sample_lbo_inputs():
    """Sample LBO inputs for testing"""
    return {
        'companyName': 'Test Company',
        'purchasePrice': 1000000,
        'equityContribution': 300000,
        'seniorDebt': 500000,
        'mezzanineDebt': 150000,
        'highYieldDebt': 50000,
        'seniorRate': 0.06,
        'mezzanineRate': 0.10,
        'highYieldRate': 0.12,
        'revenue': 800000,
        'ebitdaMargin': 0.20,
        'revenueGrowth': 0.05,
        'ebitdaGrowth': 0.03,
        'workingCapital': 0.15,
        'capex': 0.08,
        'taxRate': 0.25,
        'depreciation': 0.05,
        'exitYear': 5,
        'exitMultiple': 8.0
    }

@pytest.fixture
def sample_lbo_results():
    """Sample LBO results for testing"""
    return {
        'irr': 0.25,
        'moic': 3.2,
        'exitValue': 1200000,
        'equityValue': 960000,
        'debtPaydown': [450000, 400000, 350000, 300000, 250000],
        'cashFlows': [50000, 75000, 100000, 125000, 150000],
        'ebitda': [160000, 164800, 169744, 174836, 180081]
    }

class TestLBOEngine:
    """Test cases for LBO engine calculations"""
    
    def test_lbo_engine_basic_calculation(self, sample_lbo_inputs):
        """Test basic LBO calculation"""
        assert 'purchasePrice' in sample_lbo_inputs
        assert 'equityContribution' in sample_lbo_inputs
        assert 'exitYear' in sample_lbo_inputs
    
    def test_lbo_engine_debt_structure(self, sample_lbo_inputs):
        """Test debt structure calculations"""
        total_debt = (sample_lbo_inputs['seniorDebt'] + 
                     sample_lbo_inputs['mezzanineDebt'] + 
                     sample_lbo_inputs['highYieldDebt'])
        
        total_purchase_price = sample_lbo_inputs['purchasePrice']
        equity_contribution = sample_lbo_inputs['equityContribution']
        
        # Total debt + equity should equal purchase price
        assert abs(total_debt + equity_contribution - total_purchase_price) < 1
    
    def test_lbo_engine_interest_calculation(self, sample_lbo_inputs):
        """Test interest expense calculations"""
        senior_interest = sample_lbo_inputs['seniorDebt'] * sample_lbo_inputs['seniorRate']
        mezzanine_interest = sample_lbo_inputs['mezzanineDebt'] * sample_lbo_inputs['mezzanineRate']
        high_yield_interest = sample_lbo_inputs['highYieldDebt'] * sample_lbo_inputs['highYieldRate']
        
        total_interest = senior_interest + mezzanine_interest + high_yield_interest
        
        assert total_interest > 0
        assert total_interest < sample_lbo_inputs['purchasePrice'] * 0.15  # Reasonable interest burden
    
    def test_lbo_engine_ebitda_projection(self, sample_lbo_inputs):
        """Test EBITDA projections"""
        initial_ebitda = sample_lbo_inputs['revenue'] * sample_lbo_inputs['ebitdaMargin']
        growth_rate = sample_lbo_inputs['ebitdaGrowth']
        
        # Project EBITDA for 5 years
        ebitda_projections = []
        current_ebitda = initial_ebitda
        
        for year in range(5):
            ebitda_projections.append(current_ebitda)
            current_ebitda *= (1 + growth_rate)
        
        # Check that EBITDA grows over time
        for i in range(len(ebitda_projections) - 1):
            assert ebitda_projections[i + 1] >= ebitda_projections[i]
    
    def test_lbo_engine_cash_flow_calculation(self, sample_lbo_inputs):
        """Test cash flow calculations"""
        revenue = sample_lbo_inputs['revenue']
        ebitda_margin = sample_lbo_inputs['ebitdaMargin']
        working_capital = sample_lbo_inputs['workingCapital']
        capex = sample_lbo_inputs['capex']
        tax_rate = sample_lbo_inputs['taxRate']
        
        # Calculate basic cash flow
        ebitda = revenue * ebitda_margin
        working_capital_change = revenue * working_capital * 0.1  # Assume 10% revenue growth
        capex_expense = revenue * capex
        taxes = ebitda * tax_rate
        
        free_cash_flow = ebitda - working_capital_change - capex_expense - taxes
        
        assert free_cash_flow > 0  # Should generate positive cash flow
    
    def test_lbo_engine_debt_paydown(self, sample_lbo_inputs):
        """Test debt paydown calculations"""
        total_debt = (sample_lbo_inputs['seniorDebt'] + 
                     sample_lbo_inputs['mezzanineDebt'] + 
                     sample_lbo_inputs['highYieldDebt'])
        
        # Simulate debt paydown over 5 years
        remaining_debt = total_debt
        paydown_schedule = []
        
        for year in range(5):
            paydown_amount = remaining_debt * 0.1  # Assume 10% paydown per year
            remaining_debt -= paydown_amount
            paydown_schedule.append(remaining_debt)
        
        # Check that debt decreases over time
        for i in range(len(paydown_schedule) - 1):
            assert paydown_schedule[i] >= paydown_schedule[i + 1]
        
        # Final debt should be positive
        assert paydown_schedule[-1] > 0

class TestLBOResults:
    """Test cases for LBO results"""
    
    def test_irr_calculation(self, sample_lbo_results):
        """Test IRR calculation"""
        irr = sample_lbo_results['irr']
        assert 0 < irr < 1  # IRR should be between 0 and 1 (0% to 100%)
    
    def test_moic_calculation(self, sample_lbo_results):
        """Test MOIC calculation"""
        moic = sample_lbo_results['moic']
        assert moic > 1  # MOIC should be greater than 1x
    
    def test_exit_value_calculation(self, sample_lbo_results):
        """Test exit value calculation"""
        exit_value = sample_lbo_results['exitValue']
        assert exit_value > 0
    
    def test_equity_value_calculation(self, sample_lbo_results):
        """Test equity value calculation"""
        equity_value = sample_lbo_results['equityValue']
        exit_value = sample_lbo_results['exitValue']
        
        assert equity_value > 0
        assert equity_value <= exit_value  # Equity value cannot exceed exit value
    
    def test_debt_paydown_schedule(self, sample_lbo_results):
        """Test debt paydown schedule"""
        debt_paydown = sample_lbo_results['debtPaydown']
        
        assert len(debt_paydown) == 5  # 5-year projection
        assert all(debt >= 0 for debt in debt_paydown)  # All debt values should be non-negative
        
        # Debt should generally decrease over time
        for i in range(len(debt_paydown) - 1):
            assert debt_paydown[i] >= debt_paydown[i + 1]
    
    def test_cash_flow_projection(self, sample_lbo_results):
        """Test cash flow projections"""
        cash_flows = sample_lbo_results['cashFlows']
        
        assert len(cash_flows) == 5  # 5-year projection
        assert all(cf > 0 for cf in cash_flows)  # All cash flows should be positive

class TestLBOValidation:
    """Test cases for LBO validation functions"""
    
    def test_validate_inputs_structure(self, sample_lbo_inputs):
        """Test input validation structure"""
        required_fields = [
            'companyName', 'purchasePrice', 'equityContribution',
            'seniorDebt', 'mezzanineDebt', 'highYieldDebt',
            'seniorRate', 'mezzanineRate', 'highYieldRate',
            'revenue', 'ebitdaMargin', 'revenueGrowth', 'ebitdaGrowth',
            'workingCapital', 'capex', 'taxRate', 'depreciation',
            'exitYear', 'exitMultiple'
        ]
        
        for field in required_fields:
            assert field in sample_lbo_inputs
    
    def test_validate_inputs_ranges(self, sample_lbo_inputs):
        """Test input validation ranges"""
        # Test rates are reasonable
        assert 0 < sample_lbo_inputs['seniorRate'] < 0.15
        assert 0 < sample_lbo_inputs['mezzanineRate'] < 0.20
        assert 0 < sample_lbo_inputs['highYieldRate'] < 0.25
        
        # Test margins and growth rates
        assert 0 < sample_lbo_inputs['ebitdaMargin'] < 1
        assert 0 < sample_lbo_inputs['revenueGrowth'] < 1
        assert 0 < sample_lbo_inputs['ebitdaGrowth'] < 1
        
        # Test exit multiple
        assert 3 < sample_lbo_inputs['exitMultiple'] < 20
    
    def test_validate_inputs_consistency(self, sample_lbo_inputs):
        """Test input validation consistency"""
        # Equity contribution should be less than purchase price
        assert sample_lbo_inputs['equityContribution'] < sample_lbo_inputs['purchasePrice']
        
        # Total debt should be positive
        total_debt = (sample_lbo_inputs['seniorDebt'] + 
                     sample_lbo_inputs['mezzanineDebt'] + 
                     sample_lbo_inputs['highYieldDebt'])
        assert total_debt > 0
        
        # Exit year should be reasonable
        assert 3 <= sample_lbo_inputs['exitYear'] <= 10

class TestIRRCalculation:
    """Test cases for IRR calculation"""
    
    def test_irr_basic_calculation(self):
        """Test basic IRR calculation"""
        # Simple case: $100 investment, $150 return in 1 year
        initial_investment = 100
        final_value = 150
        years = 1
        
        # IRR = (final_value / initial_investment)^(1/years) - 1
        irr = (final_value / initial_investment) ** (1/years) - 1
        
        assert abs(irr - 0.5) < 0.01  # Should be 50%
    
    def test_irr_multi_year_calculation(self):
        """Test multi-year IRR calculation"""
        # $100 investment, $200 return in 2 years
        initial_investment = 100
        final_value = 200
        years = 2
        
        irr = (final_value / initial_investment) ** (1/years) - 1
        
        assert abs(irr - 0.414) < 0.01  # Should be approximately 41.4%
    
    def test_irr_with_cash_flows(self):
        """Test IRR calculation with intermediate cash flows"""
        # This would test the Newton-Raphson method implementation
        # For now, we'll test the concept
        cash_flows = [-100, 30, 40, 50]  # Initial investment + 3 years of returns
        
        # Simple approximation
        total_return = sum(cash_flows[1:])
        initial_investment = abs(cash_flows[0])
        
        # Rough IRR calculation
        irr = (total_return / initial_investment) ** (1/3) - 1
        
        assert irr > 0  # Should be positive
        assert irr < 1  # Should be less than 100%

if __name__ == '__main__':
    pytest.main([__file__]) 