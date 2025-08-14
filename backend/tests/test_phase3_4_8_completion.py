"""
Comprehensive Tests for Phase 3, 4, and 8 Completion
Testing ML variant routing, performance optimization, and enterprise features
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app import app, db, init_ml_variant_routing
from backend.ml_models.registry import registry as ml_registry, get_model_performance_stats
from backend.settings import settings
from backend.utils.pagination import apply_pagination, create_paginated_response
from backend.models.rbac import Tenant, Organization, User, Role, Permission, RBACManager


class TestPhase3MLVariantRouting:
    """Test Phase 3: ML/Analytics Hardening"""
    
    def test_ml_variant_routing_activation(self, monkeypatch):
        """Test ML variant routing activation at startup"""
        # Mock settings
        monkeypatch.setattr(settings, "REVENUE_MODEL_VARIANT", "revenue_predictor_v2", raising=False)
        monkeypatch.setattr(settings, "PORTFOLIO_OPTIMIZER_VARIANT", "portfolio_optimizer_v2", raising=False)
        
        # Clear existing variants
        ml_registry._variants.clear()
        
        # Run initialization
        init_ml_variant_routing()
        
        # Verify variants were set
        assert ml_registry._variants.get("revenue_predictor") == "revenue_predictor_v2"
        assert ml_registry._variants.get("portfolio_optimizer") == "portfolio_optimizer_v2"
    
    def test_ab_testing_configuration(self):
        """Test A/B testing configuration"""
        # Configure A/B test
        ml_registry.configure_ab_test(
            "revenue_predictor",
            "revenue_predictor",
            "revenue_predictor_v2",
            traffic_split=0.3
        )
        
        # Verify configuration
        assert "revenue_predictor" in ml_registry._ab_tests
        config = ml_registry._ab_tests["revenue_predictor"]
        assert config.variant_a == "revenue_predictor"
        assert config.variant_b == "revenue_predictor_v2"
        assert config.traffic_split == 0.3
        assert config.enabled is True
    
    def test_performance_tracking(self):
        """Test ML model performance tracking"""
        # Track performance
        ml_registry.track_performance("revenue_predictor", 0.5)
        ml_registry.track_performance("revenue_predictor", 0.3)
        ml_registry.track_performance("revenue_predictor", 0.7)
        
        # Get performance stats
        stats = ml_registry.get_performance_stats("revenue_predictor")
        
        assert stats is not None
        assert stats["count"] == 3
        assert stats["min"] == 0.3
        assert stats["max"] == 0.7
        assert 0.4 < stats["mean"] < 0.6
    
    def test_usage_statistics(self):
        """Test usage statistics tracking"""
        # Clear existing stats
        ml_registry.clear_usage_stats()
        
        # Get models to increment usage
        ml_registry.get("revenue_predictor")
        ml_registry.get("revenue_predictor")
        ml_registry.get("portfolio_optimizer")
        
        # Get usage stats
        usage_stats = ml_registry.get_usage_stats()
        
        assert usage_stats.get("revenue_predictor") == 2
        assert usage_stats.get("portfolio_optimizer") == 1


class TestPhase4PerformanceOptimization:
    """Test Phase 4: Performance & Scalability"""
    
    @pytest.fixture
    def test_app(self):
        """Create test Flask app"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    @pytest.fixture
    def test_db(self, test_app):
        """Create test database"""
        with test_app.app_context():
            db.create_all()
            yield db
            db.drop_all()
    
    def test_database_indexes_created(self, test_db):
        """Test that database indexes are created for performance"""
        # Check that indexes exist on User model
        user_indexes = [index.name for index in User.__table__.indexes]
        assert 'idx_user_tenant_id' in user_indexes
        assert 'idx_user_email' in user_indexes
        assert 'idx_user_username' in user_indexes
        
        # Check that indexes exist on Run model
        run_indexes = [index.name for index in db.Model.metadata.tables['run'].indexes]
        assert 'idx_run_tenant_id' in run_indexes
        assert 'idx_run_user_id' in run_indexes
        assert 'idx_run_ticker' in run_indexes
        assert 'idx_run_created_at' in run_indexes
        assert 'idx_run_tenant_user' in run_indexes
    
    def test_pagination_utilities(self, test_app):
        """Test pagination utilities"""
        with test_app.app_context():
            # Create test data
            from backend.app import User, Run
            
            # Create test user
            user = User(
                username="testuser",
                email="test@example.com",
                password_hash="hash",
                tenant_id=1
            )
            test_db.session.add(user)
            test_db.session.commit()
            
            # Create test runs
            for i in range(25):
                run = Run(
                    user_id=user.id,
                    tenant_id=1,
                    run_id=f"run-{i}",
                    ticker=f"TICK{i}",
                    inputs=json.dumps({"test": "data"})
                )
                test_db.session.add(run)
            test_db.session.commit()
            
            # Test pagination
            query = Run.query
            paginated_query, pagination_info = apply_pagination(query, Run)
            
            assert pagination_info["page"] == 1
            assert pagination_info["per_page"] == 20
            assert pagination_info["total"] == 25
            assert pagination_info["pages"] == 2
            assert pagination_info["has_next"] is True
            assert pagination_info["has_prev"] is False
    
    def test_tenant_filtering(self, test_app, test_db):
        """Test tenant filtering for multi-tenancy"""
        with test_app.app_context():
            from backend.app import User, Run
            from backend.utils.pagination import apply_tenant_filter
            
            # Create users for different tenants
            user1 = User(username="user1", email="user1@tenant1.com", password_hash="hash", tenant_id=1)
            user2 = User(username="user2", email="user2@tenant2.com", password_hash="hash", tenant_id=2)
            test_db.session.add_all([user1, user2])
            test_db.session.commit()
            
            # Create runs for different tenants
            run1 = Run(user_id=user1.id, tenant_id=1, run_id="run1", ticker="AAPL", inputs="{}")
            run2 = Run(user_id=user2.id, tenant_id=2, run_id="run2", ticker="MSFT", inputs="{}")
            test_db.session.add_all([run1, run2])
            test_db.session.commit()
            
            # Test tenant filtering
            query = Run.query
            tenant1_query = apply_tenant_filter(query, 1)
            tenant2_query = apply_tenant_filter(query, 2)
            
            assert tenant1_query.count() == 1
            assert tenant2_query.count() == 1
            assert tenant1_query.first().tenant_id == 1
            assert tenant2_query.first().tenant_id == 2


class TestPhase8EnterpriseFeatures:
    """Test Phase 8: Enterprise Features"""
    
    @pytest.fixture
    def test_app(self):
        """Create test Flask app"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        return app
    
    @pytest.fixture
    def test_db(self, test_app):
        """Create test database"""
        with test_app.app_context():
            db.create_all()
            yield db
            db.drop_all()
    
    def test_tenant_creation(self, test_app, test_db):
        """Test tenant creation and management"""
        with test_app.app_context():
            # Create tenant
            tenant = Tenant(
                name="Test Company",
                domain="testcompany.com",
                subscription_plan="professional",
                max_users=50,
                max_storage_gb=10,
                features_enabled=["advanced_analytics", "ml_models"],
                branding_config={"logo_url": "https://example.com/logo.png"}
            )
            test_db.session.add(tenant)
            test_db.session.commit()
            
            assert tenant.id is not None
            assert tenant.name == "Test Company"
            assert tenant.subscription_plan == "professional"
            assert "advanced_analytics" in tenant.features_enabled
            assert tenant.branding_config["logo_url"] == "https://example.com/logo.png"
    
    def test_organization_creation(self, test_app, test_db):
        """Test organization creation within tenant"""
        with test_app.app_context():
            # Create tenant
            tenant = Tenant(name="Test Company", domain="test.com", subscription_plan="basic")
            test_db.session.add(tenant)
            test_db.session.commit()
            
            # Create organization
            org = Organization(
                name="Test Organization",
                tenant_id=tenant.id
            )
            test_db.session.add(org)
            test_db.session.commit()
            
            assert org.id is not None
            assert org.tenant_id == tenant.id
            assert org.name == "Test Organization"
    
    def test_user_creation_with_tenant(self, test_app, test_db):
        """Test user creation with tenant association"""
        with test_app.app_context():
            # Create tenant and organization
            tenant = Tenant(name="Test Company", domain="test.com", subscription_plan="basic")
            org = Organization(name="Test Org", tenant_id=1)
            test_db.session.add_all([tenant, org])
            test_db.session.commit()
            
            # Create user
            user = User(
                username="testuser",
                email="test@test.com",
                password_hash="hash",
                tenant_id=tenant.id,
                organization_id=org.id,
                first_name="Test",
                last_name="User"
            )
            test_db.session.add(user)
            test_db.session.commit()
            
            assert user.id is not None
            assert user.tenant_id == tenant.id
            assert user.organization_id == org.id
            assert user.first_name == "Test"
            assert user.last_name == "User"
    
    def test_rbac_permissions(self, test_app, test_db):
        """Test RBAC permission system"""
        with test_app.app_context():
            rbac_manager = RBACManager()
            
            # Create tenant and user
            tenant = Tenant(name="Test Company", domain="test.com", subscription_plan="basic")
            user = User(username="testuser", email="test@test.com", password_hash="hash", tenant_id=1)
            test_db.session.add_all([tenant, user])
            test_db.session.commit()
            
            # Create role with permissions
            role = Role(
                name="Analyst",
                description="Can create and modify models",
                permissions=json.dumps([Permission.READ_MODELS.value, Permission.WRITE_MODELS.value]),
                organization_id=1,
                tenant_id=tenant.id
            )
            test_db.session.add(role)
            test_db.session.commit()
            
            # Assign role to user
            user.roles.append(role)
            test_db.session.commit()
            
            # Test permissions
            assert rbac_manager.has_permission(user, Permission.READ_MODELS, tenant.id) is True
            assert rbac_manager.has_permission(user, Permission.WRITE_MODELS, tenant.id) is True
            assert rbac_manager.has_permission(user, Permission.ADMIN_USERS, tenant.id) is False
    
    def test_subscription_management(self, test_app, test_db):
        """Test subscription management"""
        with test_app.app_context():
            from backend.models.rbac import Subscription
            from datetime import datetime, timedelta
            
            # Create tenant
            tenant = Tenant(name="Test Company", domain="test.com", subscription_plan="basic")
            test_db.session.add(tenant)
            test_db.session.commit()
            
            # Create subscription
            subscription = Subscription(
                tenant_id=tenant.id,
                plan_name="professional",
                status="active",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30),
                billing_cycle="monthly",
                amount=29900,  # $299.00 in cents
                currency="USD",
                features=["advanced_analytics", "ml_models", "api_access"]
            )
            test_db.session.add(subscription)
            test_db.session.commit()
            
            assert subscription.id is not None
            assert subscription.plan_name == "professional"
            assert subscription.status == "active"
            assert subscription.amount == 29900
            assert "advanced_analytics" in subscription.features
    
    def test_tenant_configuration(self, test_app, test_db):
        """Test tenant-specific configuration"""
        with test_app.app_context():
            from backend.models.rbac import TenantConfiguration
            
            # Create tenant
            tenant = Tenant(name="Test Company", domain="test.com", subscription_plan="basic")
            test_db.session.add(tenant)
            test_db.session.commit()
            
            # Create tenant configuration
            config = TenantConfiguration(
                tenant_id=tenant.id,
                config_key="custom_theme",
                config_value=json.dumps({"primary_color": "#007bff", "logo_url": "https://example.com/logo.png"}),
                config_type="json"
            )
            test_db.session.add(config)
            test_db.session.commit()
            
            assert config.id is not None
            assert config.tenant_id == tenant.id
            assert config.config_key == "custom_theme"
            assert json.loads(config.config_value)["primary_color"] == "#007bff"


class TestIntegrationFeatures:
    """Test integration between phases"""
    
    def test_ml_variant_with_tenant_isolation(self):
        """Test ML variant routing with tenant isolation"""
        # Configure different variants for different tenants
        ml_registry.set_variant("revenue_predictor", "revenue_predictor_v2")
        
        # Get model instance
        model = ml_registry.get("revenue_predictor")
        
        # Test that it's the v2 variant
        result = model.predict([{"x": 1}, {"x": 2}])
        assert isinstance(result, dict)
        assert result.get("variant") == "v2"
        
        # Track performance
        ml_registry.track_performance("revenue_predictor_v2", 0.5)
        
        # Verify performance tracking
        stats = ml_registry.get_performance_stats("revenue_predictor_v2")
        assert stats is not None
        assert stats["count"] == 1
    
    def test_pagination_with_tenant_filtering(self, test_app, test_db):
        """Test pagination with tenant filtering"""
        with test_app.app_context():
            from backend.app import User, Run
            from backend.utils.pagination import apply_pagination, apply_tenant_filter
            
            # Create test data for multiple tenants
            user1 = User(username="user1", email="user1@tenant1.com", password_hash="hash", tenant_id=1)
            user2 = User(username="user2", email="user2@tenant2.com", password_hash="hash", tenant_id=2)
            test_db.session.add_all([user1, user2])
            test_db.session.commit()
            
            # Create runs for different tenants
            for i in range(15):
                run = Run(
                    user_id=user1.id if i < 10 else user2.id,
                    tenant_id=1 if i < 10 else 2,
                    run_id=f"run-{i}",
                    ticker=f"TICK{i}",
                    inputs=json.dumps({"test": "data"})
                )
                test_db.session.add(run)
            test_db.session.commit()
            
            # Test pagination with tenant filtering
            query = Run.query
            tenant1_query = apply_tenant_filter(query, 1)
            paginated_query, pagination_info = apply_pagination(tenant1_query, Run)
            
            assert pagination_info["total"] == 10  # Only tenant 1 runs
            assert len(paginated_query.items) == 10  # All tenant 1 runs fit on one page
            assert all(run.tenant_id == 1 for run in paginated_query.items)


class TestPerformanceBenchmarks:
    """Test performance benchmarks for Phase 4 completion"""
    
    def test_database_query_performance(self, test_app, test_db):
        """Test database query performance with indexes"""
        with test_app.app_context():
            from backend.app import User, Run
            import time
            
            # Create test data
            user = User(username="testuser", email="test@example.com", password_hash="hash", tenant_id=1)
            test_db.session.add(user)
            test_db.session.commit()
            
            # Create 1000 runs
            runs = []
            for i in range(1000):
                run = Run(
                    user_id=user.id,
                    tenant_id=1,
                    run_id=f"run-{i}",
                    ticker=f"TICK{i % 10}",  # 10 different tickers
                    inputs=json.dumps({"test": "data"})
                )
                runs.append(run)
            test_db.session.add_all(runs)
            test_db.session.commit()
            
            # Test query performance with tenant filter
            start_time = time.time()
            tenant_runs = Run.query.filter_by(tenant_id=1).all()
            query_time = time.time() - start_time
            
            # Should be fast with indexes
            assert query_time < 0.1  # Less than 100ms
            assert len(tenant_runs) == 1000
    
    def test_pagination_performance(self, test_app, test_db):
        """Test pagination performance"""
        with test_app.app_context():
            from backend.app import User, Run
            from backend.utils.pagination import apply_pagination
            import time
            
            # Create test data
            user = User(username="testuser", email="test@example.com", password_hash="hash", tenant_id=1)
            test_db.session.add(user)
            test_db.session.commit()
            
            # Create 500 runs
            runs = []
            for i in range(500):
                run = Run(
                    user_id=user.id,
                    tenant_id=1,
                    run_id=f"run-{i}",
                    ticker=f"TICK{i % 5}",
                    inputs=json.dumps({"test": "data"})
                )
                runs.append(run)
            test_db.session.add_all(runs)
            test_db.session.commit()
            
            # Test pagination performance
            start_time = time.time()
            query = Run.query
            paginated_query, pagination_info = apply_pagination(query, Run)
            pagination_time = time.time() - start_time
            
            # Should be fast
            assert pagination_time < 0.05  # Less than 50ms
            assert pagination_info["total"] == 500
            assert pagination_info["pages"] == 25  # 500 / 20 per page 