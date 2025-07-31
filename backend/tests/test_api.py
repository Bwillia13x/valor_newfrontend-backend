"""
API Tests for Valor IVX Backend
"""

import json
import pytest
from datetime import datetime
from app import app, db, User, Run, Scenario, Note

@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def sample_run_data():
    """Sample run data for testing"""
    return {
        'inputs': {
            'ticker': 'AAPL',
            'revenue': 500,
            'growthY1': 12.0,
            'growthDecay': 1.5,
            'years': 7,
            'termGrowth': 2.5,
            'ebitMargin': 22.0,
            'taxRate': 23.0,
            'salesToCap': 2.5,
            'wacc': 9.0,
            'shares': 150,
            'netDebt': 300
        },
        'mc_settings': {
            'trials': 1000,
            'volPP': 2.0,
            'seed': 'test-seed'
        },
        'timestamp': datetime.utcnow().isoformat()
    }

@pytest.fixture
def sample_scenario_data():
    """Sample scenario data for testing"""
    return {
        'name': 'Test Scenario',
        'ticker': 'AAPL',
        'inputs': {
            'revenue': 500,
            'growthY1': 12.0,
            'wacc': 9.0
        },
        'mc_settings': {
            'trials': 1000,
            'volPP': 2.0
        }
    }

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['version'] == '1.0.0'

class TestRunEndpoints:
    """Test run management endpoints"""
    
    def test_save_run(self, client, sample_run_data):
        """Test saving a run"""
        response = client.post('/api/runs', 
                             data=json.dumps(sample_run_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'run_id' in data
        assert data['message'] == 'Run saved successfully'
    
    def test_save_run_invalid_data(self, client):
        """Test saving run with invalid data"""
        response = client.post('/api/runs',
                             data=json.dumps({'invalid': 'data'}),
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_last_run(self, client, sample_run_data):
        """Test getting the last run"""
        # First save a run
        client.post('/api/runs',
                   data=json.dumps(sample_run_data),
                   content_type='application/json')
        
        # Then get the last run
        response = client.get('/api/runs/last')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['ticker'] == 'AAPL'
    
    def test_get_last_run_no_runs(self, client):
        """Test getting last run when no runs exist"""
        response = client.get('/api/runs/last')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_list_runs(self, client, sample_run_data):
        """Test listing runs"""
        # Save multiple runs
        for i in range(3):
            run_data = sample_run_data.copy()
            run_data['inputs']['ticker'] = f'AAPL{i}'
            client.post('/api/runs',
                       data=json.dumps(run_data),
                       content_type='application/json')
        
        # List runs
        response = client.get('/api/runs')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['runs']) == 3

class TestScenarioEndpoints:
    """Test scenario management endpoints"""
    
    def test_save_scenarios(self, client, sample_scenario_data):
        """Test saving scenarios"""
        scenarios = [sample_scenario_data]
        
        response = client.post('/api/scenarios',
                             data=json.dumps(scenarios),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['saved_count'] == 1
    
    def test_save_scenarios_invalid_data(self, client):
        """Test saving scenarios with invalid data"""
        response = client.post('/api/scenarios',
                             data=json.dumps({'invalid': 'data'}),
                             content_type='application/json')
        
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_scenarios(self, client, sample_scenario_data):
        """Test getting scenarios"""
        # Save scenarios first
        scenarios = [sample_scenario_data]
        client.post('/api/scenarios',
                   data=json.dumps(scenarios),
                   content_type='application/json')
        
        # Get scenarios
        response = client.get('/api/scenarios')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['scenarios']) == 1
        assert data['scenarios'][0]['name'] == 'Test Scenario'
    
    def test_delete_scenario(self, client, sample_scenario_data):
        """Test deleting a scenario"""
        # Save scenario first
        scenarios = [sample_scenario_data]
        response = client.post('/api/scenarios',
                             data=json.dumps(scenarios),
                             content_type='application/json')
        
        # Get the scenario ID
        scenarios_response = client.get('/api/scenarios')
        scenario_id = json.loads(scenarios_response.data)['scenarios'][0]['scenario_id']
        
        # Delete the scenario
        response = client.delete(f'/api/scenarios/{scenario_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_delete_nonexistent_scenario(self, client):
        """Test deleting a scenario that doesn't exist"""
        response = client.delete('/api/scenarios/nonexistent-id')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data

class TestNotesEndpoints:
    """Test notes management endpoints"""
    
    def test_save_notes(self, client):
        """Test saving notes"""
        notes_data = {'content': 'Test notes for AAPL'}
        
        response = client.post('/api/notes/AAPL',
                             data=json.dumps(notes_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Notes saved successfully'
    
    def test_get_notes(self, client):
        """Test getting notes"""
        # Save notes first
        notes_data = {'content': 'Test notes for AAPL'}
        client.post('/api/notes/AAPL',
                   data=json.dumps(notes_data),
                   content_type='application/json')
        
        # Get notes
        response = client.get('/api/notes/AAPL')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['content'] == 'Test notes for AAPL'
    
    def test_get_notes_nonexistent(self, client):
        """Test getting notes for a ticker that doesn't have notes"""
        response = client.get('/api/notes/NONEXISTENT')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['content'] == ''

class TestErrorHandling:
    """Test error handling"""
    
    def test_404_error(self, client):
        """Test 404 error handling"""
        response = client.get('/api/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_invalid_json(self, client):
        """Test handling of invalid JSON"""
        response = client.post('/api/runs',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400

if __name__ == '__main__':
    pytest.main([__file__]) 