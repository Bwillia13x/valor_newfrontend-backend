import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class RiskAssessor:
    def __init__(self):
        self.credit_model = RandomForestClassifier(n_estimators=50)
        self.market_model = RandomForestClassifier(n_estimators=50)
        self.operational_model = RandomForestClassifier(n_estimators=50)
        self.scaler = StandardScaler()
        
    def train_credit_model(self, credit_data):
        X = credit_data[['debt_to_equity', 'interest_coverage', 'leverage_ratio']]
        y = credit_data['credit_risk']
        X_scaled = self.scaler.fit_transform(X)
        self.credit_model.fit(X_scaled, y)
    
    def train_market_model(self, market_data):
        X = market_data[['volatility', 'liquidity_ratio', 'market_cap']]
        y = market_data['market_risk']
        X_scaled = self.scaler.fit_transform(X)
        self.market_model.fit(X_scaled, y)
    
    def train_operational_model(self, operational_data):
        X = operational_data[['process_efficiency', 'compliance_score', 'internal_controls']]
        y = operational_data['operational_risk']
        X_scaled = self.scaler.fit_transform(X)
        self.operational_model.fit(X_scaled, y)
    
    def assess_credit_risk(self, financial_data):
        X = financial_data[['debt_to_equity', 'interest_coverage', 'leverage_ratio']]
        X_scaled = self.scaler.transform(X)
        return self.credit_model.predict_proba(X_scaled)
    
    def assess_market_risk(self, market_data):
        X = market_data[['volatility', 'liquidity_ratio', 'market_cap']]
        X_scaled = self.scaler.transform(X)
        return self.market_model.predict(X_scaled)
    
    def assess_operational_risk(self, operational_data):
        X = operational_data[['process_efficiency', 'compliance_score', 'internal_controls']]
        X_scaled = self.scaler.transform(X)
        return self.operational_model.predict_proba(X_scaled)
