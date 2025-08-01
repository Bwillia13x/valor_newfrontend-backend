from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import numpy as np
import pandas as pd
from typing import Dict, List, Any

class SentimentAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.classifier = LogisticRegression(C=1.0, solver='liblinear', multi_class='auto')
        self.pipeline = Pipeline([
            ('tfidf', self.vectorizer),
            ('clf', self.classifier)
        ])
        self.sentiment_labels = {
            -1: 'negative',
            0: 'neutral',
            1: 'positive'
        }
    
    def train(self, text_data: List[str], labels: List[int]):
        """Train sentiment analysis model on labeled text data"""
        if len(text_data) != len(labels):
            raise ValueError("Text data and labels must have the same length")
            
        if len(text_data) < 50:
            raise ValueError("Need at least 50 samples for training")
            
        X_train, X_test, y_train, y_test = train_test_split(
            text_data, labels, test_size=0.2, random_state=42
        )
        
        self.pipeline.fit(X_train, y_train)
        
        # Log training metrics
        predictions = self.pipeline.predict(X_test)
        print(classification_report(y_test, predictions))
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of a single text input"""
        if not text or len(text.strip()) < 10:
            raise ValueError("Text must be at least 10 characters long")
            
        # Predict sentiment
        sentiment_score = self.pipeline.predict([text])[0]
        probabilities = self.pipeline.predict_proba([text])[0]
        
        # Get most relevant features
        feature_names = self.vectorizer.get_feature_names_out()
        coefs = self.classifier.coef_[0]
        sorted_indices = np.argsort(np.abs(coefs))[::-1]
        
        return {
            'sentiment': self.sentiment_labels.get(sentiment_score, 'unknown'),
            'confidence': float(max(probabilities)),
            'key_features': [
                {
                    'word': feature_names[i],
                    'weight': float(coefs[i])
                } for i in sorted_indices[:5]
            ],
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def batch_analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze sentiment for multiple text inputs"""
        if not texts:
            raise ValueError("No texts provided for analysis")
            
        if len(texts) < 5:
            raise ValueError("Need at least 5 texts for batch analysis")
            
        sentiment_scores = self.pipeline.predict(texts)
        probabilities = self.pipeline.predict_proba(texts)
        
        return [
            {
                'sentiment': self.sentiment_labels.get(score, 'unknown'),
                'confidence': float(max(probabilities[i]))
            } for i, score in enumerate(sentiment_scores)
        ]
