import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

class RevenuePredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100)
        self.scaler = StandardScaler()
        self.feature_columns = [
            'revenue_growth', 'ebitda_margin', 'market_cap',
            'industry_avg_growth', 'economic_indicators'
        ]
    
    def train(self, historical_data):
        X = historical_data[self.feature_columns]
        y = historical_data['future_revenue']
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
    
    def predict(self, current_data):
        X = current_data[self.feature_columns]
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
