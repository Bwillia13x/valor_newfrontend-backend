"""
Financial Data API Integration Module
Handles fetching financial data from external APIs like Alpha Vantage
"""

import os
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinancialDataAPI:
    """Financial data API client for fetching market data"""
    
    def __init__(self):
        self.alpha_vantage_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
        
    def get_company_overview(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get company overview data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
            
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': ticker.upper(),
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
                
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note: {data['Note']}")
                return None
            
            # Return None if no data found
            if not data or len(data) <= 1:
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching company overview: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching company overview: {e}")
            return None
    
    def get_income_statement(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get income statement data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
            
        try:
            params = {
                'function': 'INCOME_STATEMENT',
                'symbol': ticker.upper(),
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
                
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note: {data['Note']}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching income statement: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching income statement: {e}")
            return None
    
    def get_balance_sheet(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get balance sheet data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
            
        try:
            params = {
                'function': 'BALANCE_SHEET',
                'symbol': ticker.upper(),
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
                
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note: {data['Note']}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching balance sheet: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching balance sheet: {e}")
            return None
    
    def get_cash_flow(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cash flow statement data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
            
        try:
            params = {
                'function': 'CASH_FLOW',
                'symbol': ticker.upper(),
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
                
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note: {data['Note']}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching cash flow: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching cash flow: {e}")
            return None
    
    def get_historical_prices(self, ticker: str, interval: str = 'daily') -> Optional[Dict[str, Any]]:
        """Get historical price data from Alpha Vantage"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
            
        try:
            params = {
                'function': 'TIME_SERIES_' + interval.upper(),
                'symbol': ticker.upper(),
                'apikey': self.alpha_vantage_key,
                'outputsize': 'compact'  # Last 100 data points
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                return None
                
            if 'Note' in data:
                logger.warning(f"Alpha Vantage API note: {data['Note']}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching historical prices: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching historical prices: {e}")
            return None

def parse_financial_data(overview_data: Dict[str, Any], income_data: Dict[str, Any], 
                        balance_data: Dict[str, Any], cash_flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and structure financial data for DCF analysis"""
    
    parsed_data = {
        'ticker': overview_data.get('Symbol', ''),
        'company_name': overview_data.get('Name', ''),
        'sector': overview_data.get('Sector', ''),
        'industry': overview_data.get('Industry', ''),
        'market_cap': _parse_number(overview_data.get('MarketCapitalization', '0')),
        'revenue': _parse_number(overview_data.get('RevenueTTM', '0')),
        'ebit': _parse_number(overview_data.get('EBITTTM', '0')),
        'net_income': _parse_number(overview_data.get('NetIncomeTTM', '0')),
        'total_debt': _parse_number(overview_data.get('TotalDebt', '0')),
        'cash': _parse_number(overview_data.get('CashAndCashEquivalents', '0')),
        'shares_outstanding': _parse_number(overview_data.get('SharesOutstanding', '0')),
        'beta': _parse_number(overview_data.get('Beta', '1.0')),
        'pe_ratio': _parse_number(overview_data.get('PERatio', '0')),
        'pb_ratio': _parse_number(overview_data.get('PriceToBookRatio', '0')),
        'debt_to_equity': _parse_number(overview_data.get('DebtToEquityRatio', '0')),
        'return_on_equity': _parse_number(overview_data.get('ReturnOnEquityTTM', '0')),
        'return_on_assets': _parse_number(overview_data.get('ReturnOnAssetsTTM', '0')),
        'profit_margin': _parse_number(overview_data.get('ProfitMargin', '0')),
        'operating_margin': _parse_number(overview_data.get('OperatingMarginTTM', '0')),
        'revenue_growth': _parse_number(overview_data.get('RevenueGrowthTTM', '0')),
        'earnings_growth': _parse_number(overview_data.get('EarningsGrowthTTM', '0')),
        'free_cash_flow': _parse_number(overview_data.get('FreeCashFlowTTM', '0')),
        'current_ratio': _parse_number(overview_data.get('CurrentRatio', '0')),
        'quick_ratio': _parse_number(overview_data.get('QuickRatio', '0')),
        'inventory_turnover': _parse_number(overview_data.get('InventoryTurnoverTTM', '0')),
        'asset_turnover': _parse_number(overview_data.get('AssetTurnoverTTM', '0')),
        'income_statements': [],
        'balance_sheets': [],
        'cash_flows': []
    }
    
    # Parse income statements
    if income_data and 'annualReports' in income_data:
        for report in income_data['annualReports'][:5]:  # Last 5 years
            parsed_data['income_statements'].append({
                'fiscal_date': report.get('fiscalDateEnding', ''),
                'total_revenue': _parse_number(report.get('totalRevenue', '0')),
                'gross_profit': _parse_number(report.get('grossProfit', '0')),
                'operating_income': _parse_number(report.get('operatingIncome', '0')),
                'net_income': _parse_number(report.get('netIncome', '0')),
                'ebitda': _parse_number(report.get('ebitda', '0')),
                'ebit': _parse_number(report.get('ebit', '0'))
            })
    
    # Parse balance sheets
    if balance_data and 'annualReports' in balance_data:
        for report in balance_data['annualReports'][:5]:  # Last 5 years
            parsed_data['balance_sheets'].append({
                'fiscal_date': report.get('fiscalDateEnding', ''),
                'total_assets': _parse_number(report.get('totalAssets', '0')),
                'total_current_assets': _parse_number(report.get('totalCurrentAssets', '0')),
                'total_liabilities': _parse_number(report.get('totalLiabilities', '0')),
                'total_current_liabilities': _parse_number(report.get('totalCurrentLiabilities', '0')),
                'total_equity': _parse_number(report.get('totalShareholderEquity', '0')),
                'total_debt': _parse_number(report.get('totalDebt', '0')),
                'cash_and_equivalents': _parse_number(report.get('cashAndCashEquivalentsAtCarryingValue', '0')),
                'inventory': _parse_number(report.get('inventory', '0')),
                'accounts_receivable': _parse_number(report.get('netReceivables', '0')),
                'accounts_payable': _parse_number(report.get('accountPayables', '0'))
            })
    
    # Parse cash flows
    if cash_flow_data and 'annualReports' in cash_flow_data:
        for report in cash_flow_data['annualReports'][:5]:  # Last 5 years
            parsed_data['cash_flows'].append({
                'fiscal_date': report.get('fiscalDateEnding', ''),
                'operating_cash_flow': _parse_number(report.get('operatingCashflow', '0')),
                'investing_cash_flow': _parse_number(report.get('cashflowFromInvestment', '0')),
                'financing_cash_flow': _parse_number(report.get('cashflowFromFinancing', '0')),
                'capital_expenditures': _parse_number(report.get('capitalExpenditures', '0')),
                'free_cash_flow': _parse_number(report.get('operatingCashflow', '0')) - _parse_number(report.get('capitalExpenditures', '0'))
            })
    
    return parsed_data

def _parse_number(value: str) -> float:
    """Parse string number to float, handling various formats"""
    if not value or value == 'None' or value == '':
        return 0.0
    
    try:
        # Remove any non-numeric characters except decimal point and minus
        cleaned = ''.join(c for c in str(value) if c.isdigit() or c in '.-')
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0

def calculate_dcf_inputs(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate DCF model inputs from financial data"""
    
    if not financial_data:
        return {}
    
    # Get most recent data
    latest_income = financial_data.get('income_statements', [{}])[0] if financial_data.get('income_statements') else {}
    latest_balance = financial_data.get('balance_sheets', [{}])[0] if financial_data.get('balance_sheets') else {}
    latest_cash_flow = financial_data.get('cash_flows', [{}])[0] if financial_data.get('cash_flows') else {}
    
    # Calculate key metrics
    revenue = financial_data.get('revenue', 0) or latest_income.get('total_revenue', 0)
    ebit = financial_data.get('ebit', 0) or latest_income.get('operating_income', 0)
    net_income = financial_data.get('net_income', 0) or latest_income.get('net_income', 0)
    total_debt = financial_data.get('total_debt', 0) or latest_balance.get('total_debt', 0)
    cash = financial_data.get('cash', 0) or latest_balance.get('cash_and_equivalents', 0)
    shares_outstanding = financial_data.get('shares_outstanding', 0)
    
    # Calculate derived metrics
    net_debt = total_debt - cash
    ebit_margin = (ebit / revenue * 100) if revenue > 0 else 0
    tax_rate = 0.25  # Default corporate tax rate, could be calculated from actual data
    
    # Calculate working capital metrics
    current_assets = latest_balance.get('total_current_assets', 0)
    current_liabilities = latest_balance.get('total_current_liabilities', 0)
    working_capital = current_assets - current_liabilities
    nwc_ratio = (working_capital / revenue * 100) if revenue > 0 else 0
    
    # Calculate capital efficiency
    total_assets = latest_balance.get('total_assets', 0)
    sales_to_capital = (revenue / total_assets) if total_assets > 0 else 2.5
    
    # Calculate growth rates (simplified)
    revenue_growth = financial_data.get('revenue_growth', 0) * 100  # Convert to percentage
    
    return {
        'ticker': financial_data.get('ticker', ''),
        'revenue': revenue,
        'growthY1': revenue_growth / 100,  # Convert to decimal
        'growthDecay': 0.015,  # Default decay rate
        'ebitMargin': ebit_margin / 100,  # Convert to decimal
        'taxRate': tax_rate,
        'salesToCap': sales_to_capital,
        'shares': shares_outstanding,
        'netDebt': net_debt,
        's1NWC': nwc_ratio / 100,  # Convert to decimal
        's2NWC': nwc_ratio / 100,
        's3NWC': nwc_ratio / 100,
        'wacc': 0.09,  # Default WACC, could be calculated from beta
        'termGrowth': 0.025,  # Default terminal growth
        'years': 7,  # Default projection years
        'stage1End': 3,
        'stage2End': 6
    }

# Global instance
financial_api = FinancialDataAPI() 