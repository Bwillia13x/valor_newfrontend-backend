// Valor IVX - Financial Data Module
// Handles fetching financial data from backend API

import { logLine } from './ui-handlers.js';
import { applyInputs } from './dcf-engine.js';

// Financial data cache
const dataCache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

class FinancialDataManager {
    constructor() {
        this.baseUrl = '/api/financial-data';
        this.isLoading = false;
    }
    
    /**
     * Fetch comprehensive financial data for a ticker
     */
    async fetchFinancialData(ticker) {
        if (!ticker) {
            throw new Error('Ticker is required');
        }
        
        // Check cache first
        const cacheKey = `financial_${ticker.toUpperCase()}`;
        const cached = this.getCachedData(cacheKey);
        if (cached) {
            return cached;
        }
        
        this.isLoading = true;
        logLine(`Fetching financial data for ${ticker.toUpperCase()}...`);
        
        try {
            const response = await fetch(`${this.baseUrl}/${ticker.toUpperCase()}`);
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to fetch financial data');
            }
            
            // Cache the result
            this.cacheData(cacheKey, result.data);
            
            logLine(`Financial data loaded for ${ticker.toUpperCase()}`);
            return result.data;
            
        } catch (error) {
            logLine(`Error fetching financial data: ${error.message}`, 'err');
            throw error;
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * Fetch DCF inputs calculated from financial data
     */
    async fetchDCFInputs(ticker) {
        if (!ticker) {
            throw new Error('Ticker is required');
        }
        
        // Check cache first
        const cacheKey = `dcf_inputs_${ticker.toUpperCase()}`;
        const cached = this.getCachedData(cacheKey);
        if (cached) {
            return cached;
        }
        
        this.isLoading = true;
        logLine(`Calculating DCF inputs for ${ticker.toUpperCase()}...`);
        
        try {
            const response = await fetch(`${this.baseUrl}/${ticker.toUpperCase()}/dcf-inputs`);
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to fetch DCF inputs');
            }
            
            // Cache the result
            this.cacheData(cacheKey, result.data);
            
            logLine(`DCF inputs calculated for ${ticker.toUpperCase()}`);
            return result.data;
            
        } catch (error) {
            logLine(`Error fetching DCF inputs: ${error.message}`, 'err');
            throw error;
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * Fetch historical price data
     */
    async fetchHistoricalPrices(ticker, interval = 'daily') {
        if (!ticker) {
            throw new Error('Ticker is required');
        }
        
        // Check cache first
        const cacheKey = `prices_${ticker.toUpperCase()}_${interval}`;
        const cached = this.getCachedData(cacheKey);
        if (cached) {
            return cached;
        }
        
        this.isLoading = true;
        logLine(`Fetching historical prices for ${ticker.toUpperCase()}...`);
        
        try {
            const response = await fetch(`${this.baseUrl}/${ticker.toUpperCase()}/historical-prices?interval=${interval}`);
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to fetch historical prices');
            }
            
            // Cache the result
            this.cacheData(cacheKey, result.data);
            
            logLine(`Historical prices loaded for ${ticker.toUpperCase()}`);
            return result.data;
            
        } catch (error) {
            logLine(`Error fetching historical prices: ${error.message}`, 'err');
            throw error;
        } finally {
            this.isLoading = false;
        }
    }
    
    /**
     * Load financial data and populate DCF inputs
     */
    async loadAndPopulateDCF(ticker) {
        try {
            const dcfInputs = await this.fetchDCFInputs(ticker);
            
            if (dcfInputs && Object.keys(dcfInputs).length > 0) {
                // Apply the inputs to the form
                applyInputs(dcfInputs);
                logLine(`DCF inputs populated for ${ticker.toUpperCase()}`);
                return true;
            } else {
                logLine(`No DCF inputs available for ${ticker.toUpperCase()}`, 'warn');
                return false;
            }
            
        } catch (error) {
            logLine(`Failed to load DCF inputs: ${error.message}`, 'err');
            return false;
        }
    }
    
    /**
     * Display financial data summary
     */
    displayFinancialSummary(data) {
        const summaryContainer = document.getElementById('financialSummary');
        if (!summaryContainer || !data) return;
        
        const formatCurrency = (value) => {
            if (!value || value === 0) return 'N/A';
            if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
            if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
            if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
            return `$${value.toFixed(2)}`;
        };
        
        const formatPercent = (value) => {
            if (!value || value === 0) return 'N/A';
            return `${(value * 100).toFixed(2)}%`;
        };
        
        summaryContainer.innerHTML = `
            <div class="financial-summary">
                <h3>${data.company_name || data.ticker} (${data.ticker})</h3>
                <div class="summary-grid">
                    <div class="summary-item">
                        <label>Market Cap:</label>
                        <span>${formatCurrency(data.market_cap)}</span>
                    </div>
                    <div class="summary-item">
                        <label>Revenue (TTM):</label>
                        <span>${formatCurrency(data.revenue)}</span>
                    </div>
                    <div class="summary-item">
                        <label>EBIT (TTM):</label>
                        <span>${formatCurrency(data.ebit)}</span>
                    </div>
                    <div class="summary-item">
                        <label>Net Income (TTM):</label>
                        <span>${formatCurrency(data.net_income)}</span>
                    </div>
                    <div class="summary-item">
                        <label>Operating Margin:</label>
                        <span>${formatPercent(data.operating_margin)}</span>
                    </div>
                    <div class="summary-item">
                        <label>Profit Margin:</label>
                        <span>${formatPercent(data.profit_margin)}</span>
                    </div>
                    <div class="summary-item">
                        <label>ROE:</label>
                        <span>${formatPercent(data.return_on_equity)}</span>
                    </div>
                    <div class="summary-item">
                        <label>ROA:</label>
                        <span>${formatPercent(data.return_on_assets)}</span>
                    </div>
                    <div class="summary-item">
                        <label>Debt/Equity:</label>
                        <span>${data.debt_to_equity ? data.debt_to_equity.toFixed(2) : 'N/A'}</span>
                    </div>
                    <div class="summary-item">
                        <label>P/E Ratio:</label>
                        <span>${data.pe_ratio ? data.pe_ratio.toFixed(2) : 'N/A'}</span>
                    </div>
                    <div class="summary-item">
                        <label>Beta:</label>
                        <span>${data.beta ? data.beta.toFixed(2) : 'N/A'}</span>
                    </div>
                    <div class="summary-item">
                        <label>Revenue Growth:</label>
                        <span>${formatPercent(data.revenue_growth)}</span>
                    </div>
                </div>
                <div class="summary-actions">
                    <button id="loadDCFInputs" class="btn btn-primary">Load DCF Inputs</button>
                    <button id="viewFinancials" class="btn btn-secondary">View Full Financials</button>
                </div>
            </div>
        `;
        
        // Add event listeners
        document.getElementById('loadDCFInputs')?.addEventListener('click', async () => {
            await this.loadAndPopulateDCF(data.ticker);
            // Trigger DCF calculation
            const { run } = await import('./ui-handlers.js');
            run();
        });
        
        document.getElementById('viewFinancials')?.addEventListener('click', () => {
            this.displayDetailedFinancials(data);
        });
    }
    
    /**
     * Display detailed financial statements
     */
    displayDetailedFinancials(data) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>${data.company_name || data.ticker} - Financial Statements</h2>
                    <span class="close">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="financial-tabs">
                        <button class="tab-button active" data-tab="income">Income Statement</button>
                        <button class="tab-button" data-tab="balance">Balance Sheet</button>
                        <button class="tab-button" data-tab="cashflow">Cash Flow</button>
                    </div>
                    <div class="tab-content">
                        <div id="income-tab" class="tab-pane active">
                            ${this.renderIncomeStatement(data.income_statements)}
                        </div>
                        <div id="balance-tab" class="tab-pane">
                            ${this.renderBalanceSheet(data.balance_sheets)}
                        </div>
                        <div id="cashflow-tab" class="tab-pane">
                            ${this.renderCashFlow(data.cash_flows)}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add event listeners
        modal.querySelector('.close').addEventListener('click', () => {
            document.body.removeChild(modal);
        });
        
        modal.querySelectorAll('.tab-button').forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.dataset.tab;
                this.switchTab(modal, tabName);
            });
        });
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }
    
    /**
     * Render income statement table
     */
    renderIncomeStatement(statements) {
        if (!statements || statements.length === 0) {
            return '<p>No income statement data available</p>';
        }
        
        const formatCurrency = (value) => {
            if (!value || value === 0) return '-';
            if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
            if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
            return `$${value.toFixed(0)}`;
        };
        
        let html = '<table class="financial-table"><thead><tr><th>Year</th>';
        statements.forEach(stmt => {
            html += `<th>${stmt.fiscal_date}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        const metrics = [
            { key: 'total_revenue', label: 'Total Revenue' },
            { key: 'gross_profit', label: 'Gross Profit' },
            { key: 'operating_income', label: 'Operating Income' },
            { key: 'ebit', label: 'EBIT' },
            { key: 'ebitda', label: 'EBITDA' },
            { key: 'net_income', label: 'Net Income' }
        ];
        
        metrics.forEach(metric => {
            html += `<tr><td>${metric.label}</td>`;
            statements.forEach(stmt => {
                html += `<td>${formatCurrency(stmt[metric.key])}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    /**
     * Render balance sheet table
     */
    renderBalanceSheet(sheets) {
        if (!sheets || sheets.length === 0) {
            return '<p>No balance sheet data available</p>';
        }
        
        const formatCurrency = (value) => {
            if (!value || value === 0) return '-';
            if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
            if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
            return `$${value.toFixed(0)}`;
        };
        
        let html = '<table class="financial-table"><thead><tr><th>Year</th>';
        sheets.forEach(sheet => {
            html += `<th>${sheet.fiscal_date}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        const metrics = [
            { key: 'total_assets', label: 'Total Assets' },
            { key: 'total_current_assets', label: 'Current Assets' },
            { key: 'cash_and_equivalents', label: 'Cash & Equivalents' },
            { key: 'accounts_receivable', label: 'Accounts Receivable' },
            { key: 'inventory', label: 'Inventory' },
            { key: 'total_liabilities', label: 'Total Liabilities' },
            { key: 'total_current_liabilities', label: 'Current Liabilities' },
            { key: 'total_debt', label: 'Total Debt' },
            { key: 'total_equity', label: 'Total Equity' }
        ];
        
        metrics.forEach(metric => {
            html += `<tr><td>${metric.label}</td>`;
            sheets.forEach(sheet => {
                html += `<td>${formatCurrency(sheet[metric.key])}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    /**
     * Render cash flow table
     */
    renderCashFlow(flows) {
        if (!flows || flows.length === 0) {
            return '<p>No cash flow data available</p>';
        }
        
        const formatCurrency = (value) => {
            if (!value || value === 0) return '-';
            if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
            if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
            return `$${value.toFixed(0)}`;
        };
        
        let html = '<table class="financial-table"><thead><tr><th>Year</th>';
        flows.forEach(flow => {
            html += `<th>${flow.fiscal_date}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        const metrics = [
            { key: 'operating_cash_flow', label: 'Operating Cash Flow' },
            { key: 'investing_cash_flow', label: 'Investing Cash Flow' },
            { key: 'financing_cash_flow', label: 'Financing Cash Flow' },
            { key: 'capital_expenditures', label: 'Capital Expenditures' },
            { key: 'free_cash_flow', label: 'Free Cash Flow' }
        ];
        
        metrics.forEach(metric => {
            html += `<tr><td>${metric.label}</td>`;
            flows.forEach(flow => {
                html += `<td>${formatCurrency(flow[metric.key])}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        return html;
    }
    
    /**
     * Switch between tabs in the financial modal
     */
    switchTab(modal, tabName) {
        // Update tab buttons
        modal.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        modal.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Update tab content
        modal.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        modal.querySelector(`#${tabName}-tab`).classList.add('active');
    }
    
    /**
     * Cache management
     */
    cacheData(key, data) {
        dataCache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }
    
    getCachedData(key) {
        const cached = dataCache.get(key);
        if (!cached) return null;
        
        if (Date.now() - cached.timestamp > CACHE_DURATION) {
            dataCache.delete(key);
            return null;
        }
        
        return cached.data;
    }
    
    clearCache() {
        dataCache.clear();
    }
}

// Global instance
export const financialDataManager = new FinancialDataManager();

// Initialize financial data UI
export function initFinancialDataUI() {
    // Add financial data section to the UI
    const tickerSection = document.querySelector('.input-section');
    if (tickerSection) {
        const financialDataSection = document.createElement('div');
        financialDataSection.className = 'input-section';
        financialDataSection.innerHTML = `
            <h3>Financial Data</h3>
            <div class="input-group">
                <label for="fetchTicker">Fetch Financial Data:</label>
                <div class="ticker-input-group">
                    <input type="text" id="fetchTicker" placeholder="Enter ticker (e.g., AAPL)" maxlength="10">
                    <button id="fetchData" class="btn btn-primary">Fetch Data</button>
                </div>
            </div>
            <div id="financialSummary" class="financial-summary-container"></div>
        `;
        
        tickerSection.parentNode.insertBefore(financialDataSection, tickerSection.nextSibling);
        
        // Add event listeners
        document.getElementById('fetchData')?.addEventListener('click', async () => {
            const ticker = document.getElementById('fetchTicker')?.value?.trim();
            if (!ticker) {
                logLine('Please enter a ticker symbol', 'err');
                return;
            }
            
            try {
                const data = await financialDataManager.fetchFinancialData(ticker);
                financialDataManager.displayFinancialSummary(data);
            } catch (error) {
                logLine(`Failed to fetch data: ${error.message}`, 'err');
            }
        });
        
        // Allow Enter key to trigger fetch
        document.getElementById('fetchTicker')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('fetchData')?.click();
            }
        });
    }
} 