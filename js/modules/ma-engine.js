/**
 * M&A (Merger & Acquisition) Analysis Engine
 * Provides comprehensive M&A modeling capabilities including:
 * - Accretion/Dilution Analysis
 * - Synergy Modeling
 * - Deal Structuring
 * - Pro Forma Financials
 */

import { $, fmt, clamp } from './utils.js';

class MAAnalysisEngine {
    constructor() {
        this.results = null;
        this.isCalculating = false;
        this.cancellationToken = null;
    }

    /**
     * Run M&A analysis with given parameters
     */
    async runAnalysis(params) {
        if (this.isCalculating) {
            throw new Error('Analysis already in progress');
        }

        this.isCalculating = true;
        this.cancellationToken = { cancelled: false };

        try {
            // Validate inputs
            this.validateInputs(params);

            // Calculate pro forma financials
            const proForma = this.calculateProFormaFinancials(params);

            // Calculate accretion/dilution
            const accretionDilution = this.calculateAccretionDilution(params, proForma);

            // Calculate synergies
            const synergies = this.calculateSynergies(params);

            // Calculate deal metrics
            const dealMetrics = this.calculateDealMetrics(params, proForma);

            this.results = {
                proForma,
                accretionDilution,
                synergies,
                dealMetrics,
                timestamp: new Date().toISOString()
            };

            return this.results;

        } catch (error) {
            if (this.cancellationToken.cancelled) {
                throw new Error('Analysis cancelled');
            }
            throw error;
        } finally {
            this.isCalculating = false;
            this.cancellationToken = null;
        }
    }

    /**
     * Validate M&A analysis inputs
     */
    validateInputs(params) {
        const required = [
            'acquirerRevenue', 'acquirerEBITDA', 'acquirerShares',
            'targetRevenue', 'targetEBITDA', 'targetShares',
            'purchasePrice', 'dealStructure', 'synergies'
        ];

        for (const field of required) {
            if (params[field] === undefined || params[field] === null) {
                throw new Error(`Missing required field: ${field}`);
            }
        }

        // Validate deal structure
        if (params.dealStructure.cash + params.dealStructure.stock !== 100) {
            throw new Error('Deal structure must equal 100%');
        }

        // Validate purchase price
        if (params.purchasePrice <= 0) {
            throw new Error('Purchase price must be positive');
        }

        return true;
    }

    /**
     * Calculate pro forma financial statements
     */
    calculateProFormaFinancials(params) {
        const {
            acquirerRevenue, acquirerEBITDA, acquirerShares, acquirerNetDebt,
            targetRevenue, targetEBITDA, targetShares, targetNetDebt,
            purchasePrice, dealStructure, synergies
        } = params;

        // Pro forma revenue
        const proFormaRevenue = acquirerRevenue + targetRevenue;

        // Pro forma EBITDA (including synergies)
        const proFormaEBITDA = acquirerEBITDA + targetEBITDA + synergies.annual;

        // Calculate new shares issued
        const newSharesIssued = (purchasePrice * dealStructure.stock / 100) / 
                               (acquirerRevenue / acquirerShares); // Using revenue per share as proxy

        // Pro forma shares outstanding
        const proFormaShares = acquirerShares + newSharesIssued;

        // Pro forma net debt
        const cashPaid = purchasePrice * dealStructure.cash / 100;
        const proFormaNetDebt = acquirerNetDebt + targetNetDebt + cashPaid;

        // Pro forma EPS
        const proFormaNetIncome = proFormaEBITDA * 0.65; // Assuming 35% tax rate
        const proFormaEPS = proFormaNetIncome / proFormaShares;

        return {
            revenue: proFormaRevenue,
            ebitda: proFormaEBITDA,
            netIncome: proFormaNetIncome,
            shares: proFormaShares,
            eps: proFormaEPS,
            netDebt: proFormaNetDebt,
            newSharesIssued
        };
    }

    /**
     * Calculate accretion/dilution analysis
     */
    calculateAccretionDilution(params, proForma) {
        const {
            acquirerRevenue, acquirerEBITDA, acquirerShares,
            targetRevenue, targetEBITDA, targetShares
        } = params;

        // Pre-deal metrics
        const acquirerEPS = (acquirerEBITDA * 0.65) / acquirerShares;
        const targetEPS = (targetEBITDA * 0.65) / targetShares;

        // Post-deal metrics
        const postDealEPS = proForma.eps;

        // Calculate accretion/dilution
        const accretionDilution = ((postDealEPS - acquirerEPS) / acquirerEPS) * 100;

        // Calculate contribution analysis
        const targetContribution = (targetEBITDA * 0.65) / proForma.shares;
        const synergyContribution = (params.synergies.annual * 0.65) / proForma.shares;

        return {
            preDealEPS: acquirerEPS,
            postDealEPS: postDealEPS,
            accretionDilution: accretionDilution,
            targetContribution: targetContribution,
            synergyContribution: synergyContribution,
            isAccretive: accretionDilution > 0
        };
    }

    /**
     * Calculate synergy impacts
     */
    calculateSynergies(params) {
        const { synergies } = params;

        // Calculate present value of synergies
        const pvSynergies = this.calculatePV(synergies.annual, synergies.duration, 0.10);

        // Calculate synergy per share
        const synergyPerShare = pvSynergies / params.acquirerShares;

        return {
            annual: synergies.annual,
            duration: synergies.duration,
            presentValue: pvSynergies,
            perShare: synergyPerShare
        };
    }

    /**
     * Calculate key deal metrics
     */
    calculateDealMetrics(params, proForma) {
        const { purchasePrice, targetEBITDA, targetRevenue } = params;

        // Purchase multiples
        const evEbitda = purchasePrice / targetEBITDA;
        const evRevenue = purchasePrice / targetRevenue;

        // Pro forma metrics
        const proFormaEvEbitda = (purchasePrice + proForma.netDebt) / proForma.ebitda;

        // Return metrics
        const roic = (proForma.ebitda * 0.65) / purchasePrice;

        return {
            evEbitda: evEbitda,
            evRevenue: evRevenue,
            proFormaEvEbitda: proFormaEvEbitda,
            roic: roic,
            purchasePrice: purchasePrice
        };
    }

    /**
     * Calculate present value
     */
    calculatePV(cashFlow, periods, rate) {
        let pv = 0;
        for (let i = 1; i <= periods; i++) {
            pv += cashFlow / Math.pow(1 + rate, i);
        }
        return pv;
    }

    /**
     * Cancel ongoing analysis
     */
    cancelAnalysis() {
        if (this.cancellationToken) {
            this.cancellationToken.cancelled = true;
        }
    }

    /**
     * Get analysis results
     */
    getResults() {
        return this.results;
    }

    /**
     * Export results to JSON
     */
    exportResults() {
        if (!this.results) {
            throw new Error('No analysis results to export');
        }
        return JSON.stringify(this.results, null, 2);
    }

    /**
     * Update UI with results
     */
    updateUI() {
        if (!this.results) return;

        const { proForma, accretionDilution, synergies, dealMetrics } = this.results;

        // Update pro forma metrics
        $('#ma-proforma-revenue').text(fmt(proForma.revenue, 'currency'));
        $('#ma-proforma-ebitda').text(fmt(proForma.ebitda, 'currency'));
        $('#ma-proforma-eps').text(fmt(proForma.eps, 'currency'));
        $('#ma-proforma-shares').text(fmt(proForma.shares, 'number'));

        // Update accretion/dilution
        $('#ma-accretion-dilution').text(fmt(accretionDilution.accretionDilution, 'percent'));
        $('#ma-accretion-dilution').className = accretionDilution.isAccretive ? 'positive' : 'negative';

        // Update deal metrics
        $('#ma-ev-ebitda').text(fmt(dealMetrics.evEbitda, 'number'));
        $('#ma-ev-revenue').text(fmt(dealMetrics.evRevenue, 'number'));
        $('#ma-roic').text(fmt(dealMetrics.roic, 'percent'));

        // Update synergies
        $('#ma-synergies-pv').text(fmt(synergies.presentValue, 'currency'));
        $('#ma-synergies-per-share').text(fmt(synergies.perShare, 'currency'));
    }
}

// Export the M&A engine
export const maEngine = new MAAnalysisEngine();