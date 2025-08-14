"""
Tenant Management Service for Valor IVX
Phase 8 Implementation - Multi-Tenant Architecture

This module provides comprehensive tenant management capabilities:
- Tenant creation and management
- Subscription handling
- Tenant-specific configurations
- Branding and theming
- Feature access control
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from models.rbac import Tenant, Organization, User, Role, TenantConfiguration, Subscription, RBACManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TenantConfig:
    """Tenant configuration data"""
    name: str
    domain: str
    subscription_plan: str = 'basic'
    max_users: int = 10
    max_storage_gb: int = 1
    features_enabled: List[str] = None
    branding_config: Dict[str, Any] = None

@dataclass
class SubscriptionPlan:
    """Subscription plan configuration"""
    name: str
    price_monthly: int  # Price in cents
    price_yearly: int   # Price in cents
    max_users: int
    max_storage_gb: int
    features: List[str]
    description: str

class TenantManager:
    """Comprehensive tenant management service"""
    
    def __init__(self, db_session):
        self.db = db_session
        self.rbac_manager = RBACManager()
        
        # Define available subscription plans
        self.subscription_plans = {
            'basic': SubscriptionPlan(
                name='Basic',
                price_monthly=2900,  # $29/month
                price_yearly=29000,  # $290/year
                max_users=10,
                max_storage_gb=1,
                features=['dcf_analysis', 'basic_analytics', 'data_export'],
                description='Perfect for small teams and individual analysts'
            ),
            'professional': SubscriptionPlan(
                name='Professional',
                price_monthly=9900,  # $99/month
                price_yearly=99000,  # $990/year
                max_users=50,
                max_storage_gb=10,
                features=['dcf_analysis', 'lbo_analysis', 'ma_analysis', 'advanced_analytics', 
                         'real_options', 'portfolio_optimization', 'risk_assessment', 'api_access'],
                description='Ideal for growing financial teams and consultancies'
            ),
            'enterprise': SubscriptionPlan(
                name='Enterprise',
                price_monthly=29900,  # $299/month
                price_yearly=299000,  # $2990/year
                max_users=200,
                max_storage_gb=100,
                features=['dcf_analysis', 'lbo_analysis', 'ma_analysis', 'advanced_analytics',
                         'real_options', 'portfolio_optimization', 'risk_assessment', 'api_access',
                         'custom_integrations', 'dedicated_support', 'white_label', 'audit_logs'],
                description='For large organizations requiring advanced features and support'
            )
        }
    
    def create_tenant(self, config: TenantConfig) -> Tenant:
        """Create a new tenant with default organization and admin user"""
        try:
            # Create tenant
            tenant = Tenant(
                name=config.name,
                domain=config.domain,
                subscription_plan=config.subscription_plan,
                max_users=config.max_users,
                max_storage_gb=config.max_storage_gb,
                features_enabled=config.features_enabled or self.subscription_plans[config.subscription_plan].features,
                branding_config=config.branding_config or self._get_default_branding(),
                is_active=True
            )
            
            self.db.session.add(tenant)
            self.db.session.flush()  # Get the tenant ID
            
            # Create default organization
            organization = Organization(
                name=f"{config.name} Organization",
                tenant_id=tenant.id,
                is_active=True
            )
            
            self.db.session.add(organization)
            self.db.session.flush()  # Get the organization ID
            
            # Create default roles for the organization
            self.rbac_manager.create_default_roles(organization.id, tenant.id)
            
            # Create subscription record
            subscription = Subscription(
                tenant_id=tenant.id,
                plan_name=config.subscription_plan,
                status='active',
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30),  # 30-day trial
                billing_cycle='monthly',
                amount=self.subscription_plans[config.subscription_plan].price_monthly,
                currency='USD',
                features=self.subscription_plans[config.subscription_plan].features
            )
            
            self.db.session.add(subscription)
            self.db.session.commit()
            
            logger.info(f"Created tenant: {tenant.name} (ID: {tenant.id})")
            return tenant
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Failed to create tenant: {str(e)}")
            raise
    
    def create_tenant_user(self, tenant_id: int, user_data: Dict[str, Any], 
                          role_name: str = 'Admin') -> User:
        """Create a user within a tenant"""
        try:
            # Verify tenant exists and is active
            tenant = Tenant.query.get(tenant_id)
            if not tenant or not tenant.is_active:
                raise ValueError("Invalid or inactive tenant")
            
            # Check user limit
            current_users = User.query.filter_by(tenant_id=tenant_id, is_active=True).count()
            if current_users >= tenant.max_users:
                raise ValueError(f"User limit reached for tenant. Max: {tenant.max_users}")
            
            # Create user
            user = User(
                email=user_data['email'],
                username=user_data['username'],
                password_hash=user_data['password_hash'],
                first_name=user_data.get('first_name'),
                last_name=user_data.get('last_name'),
                organization_id=user_data.get('organization_id'),
                tenant_id=tenant_id,
                is_active=True
            )
            
            self.db.session.add(user)
            self.db.session.flush()
            
            # Assign role
            role = Role.query.filter_by(
                name=role_name,
                organization_id=user.organization_id,
                tenant_id=tenant_id,
                is_active=True
            ).first()
            
            if role:
                self.rbac_manager.assign_role_to_user(user, role)
            
            self.db.session.commit()
            logger.info(f"Created user: {user.email} in tenant: {tenant_id}")
            return user
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Failed to create tenant user: {str(e)}")
            raise
    
    def update_tenant_configuration(self, tenant_id: int, config_key: str, 
                                   config_value: Any, config_type: str = 'string') -> bool:
        """Update tenant-specific configuration"""
        try:
            # Check if configuration exists
            existing_config = TenantConfiguration.query.filter_by(
                tenant_id=tenant_id,
                config_key=config_key
            ).first()
            
            if existing_config:
                existing_config.config_value = str(config_value)
                existing_config.config_type = config_type
                existing_config.updated_at = datetime.utcnow()
            else:
                new_config = TenantConfiguration(
                    tenant_id=tenant_id,
                    config_key=config_key,
                    config_value=str(config_value),
                    config_type=config_type
                )
                self.db.session.add(new_config)
            
            self.db.session.commit()
            logger.info(f"Updated tenant configuration: {config_key} for tenant: {tenant_id}")
            return True
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Failed to update tenant configuration: {str(e)}")
            return False
    
    def get_tenant_configuration(self, tenant_id: int, config_key: str = None) -> Dict[str, Any]:
        """Get tenant configuration(s)"""
        try:
            query = TenantConfiguration.query.filter_by(tenant_id=tenant_id)
            
            if config_key:
                config = query.filter_by(config_key=config_key).first()
                if config:
                    return {config.config_key: self._parse_config_value(config)}
                return {}
            
            configs = query.all()
            return {config.config_key: self._parse_config_value(config) for config in configs}
            
        except Exception as e:
            logger.error(f"Failed to get tenant configuration: {str(e)}")
            return {}
    
    def update_subscription(self, tenant_id: int, plan_name: str, 
                           billing_cycle: str = 'monthly') -> bool:
        """Update tenant subscription"""
        try:
            tenant = Tenant.query.get(tenant_id)
            if not tenant:
                raise ValueError("Tenant not found")
            
            plan = self.subscription_plans.get(plan_name)
            if not plan:
                raise ValueError("Invalid subscription plan")
            
            # Update tenant
            tenant.subscription_plan = plan_name
            tenant.max_users = plan.max_users
            tenant.max_storage_gb = plan.max_storage_gb
            tenant.features_enabled = plan.features
            tenant.updated_at = datetime.utcnow()
            
            # Create new subscription record
            subscription = Subscription(
                tenant_id=tenant_id,
                plan_name=plan_name,
                status='active',
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=30 if billing_cycle == 'monthly' else 365),
                billing_cycle=billing_cycle,
                amount=plan.price_monthly if billing_cycle == 'monthly' else plan.price_yearly,
                currency='USD',
                features=plan.features
            )
            
            self.db.session.add(subscription)
            self.db.session.commit()
            
            logger.info(f"Updated subscription for tenant: {tenant_id} to {plan_name}")
            return True
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Failed to update subscription: {str(e)}")
            return False
    
    def get_tenant_usage_stats(self, tenant_id: int) -> Dict[str, Any]:
        """Get tenant usage statistics"""
        try:
            tenant = Tenant.query.get(tenant_id)
            if not tenant:
                return {}
            
            # Count users
            user_count = User.query.filter_by(tenant_id=tenant_id, is_active=True).count()
            
            # Count organizations
            org_count = Organization.query.filter_by(tenant_id=tenant_id, is_active=True).count()
            
            # Get subscription info
            subscription = Subscription.query.filter_by(
                tenant_id=tenant_id,
                status='active'
            ).order_by(Subscription.created_at.desc()).first()
            
            return {
                'tenant_id': tenant_id,
                'tenant_name': tenant.name,
                'subscription_plan': tenant.subscription_plan,
                'max_users': tenant.max_users,
                'current_users': user_count,
                'user_usage_percent': (user_count / tenant.max_users) * 100 if tenant.max_users > 0 else 0,
                'max_storage_gb': tenant.max_storage_gb,
                'organizations': org_count,
                'features_enabled': tenant.features_enabled,
                'subscription_status': subscription.status if subscription else 'none',
                'subscription_expires': subscription.end_date.isoformat() if subscription else None,
                'created_at': tenant.created_at.isoformat(),
                'is_active': tenant.is_active
            }
            
        except Exception as e:
            logger.error(f"Failed to get tenant usage stats: {str(e)}")
            return {}
    
    def deactivate_tenant(self, tenant_id: int) -> bool:
        """Deactivate a tenant and all associated resources"""
        try:
            tenant = Tenant.query.get(tenant_id)
            if not tenant:
                return False
            
            # Deactivate tenant
            tenant.is_active = False
            tenant.updated_at = datetime.utcnow()
            
            # Deactivate all users
            users = User.query.filter_by(tenant_id=tenant_id).all()
            for user in users:
                user.is_active = False
                user.updated_at = datetime.utcnow()
            
            # Deactivate all organizations
            organizations = Organization.query.filter_by(tenant_id=tenant_id).all()
            for org in organizations:
                org.is_active = False
                org.updated_at = datetime.utcnow()
            
            # Cancel active subscription
            subscription = Subscription.query.filter_by(
                tenant_id=tenant_id,
                status='active'
            ).first()
            
            if subscription:
                subscription.status = 'cancelled'
                subscription.updated_at = datetime.utcnow()
            
            self.db.session.commit()
            logger.info(f"Deactivated tenant: {tenant_id}")
            return True
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Failed to deactivate tenant: {str(e)}")
            return False
    
    def _get_default_branding(self) -> Dict[str, Any]:
        """Get default branding configuration"""
        return {
            'primary_color': '#2563eb',
            'secondary_color': '#64748b',
            'logo_url': None,
            'company_name': 'Valor IVX',
            'custom_css': None,
            'theme': 'light'
        }
    
    def _parse_config_value(self, config: TenantConfiguration) -> Any:
        """Parse configuration value based on type"""
        try:
            if config.config_type == 'json':
                return json.loads(config.config_value)
            elif config.config_type == 'boolean':
                return config.config_value.lower() == 'true'
            elif config.config_type == 'number':
                return float(config.config_value)
            else:
                return config.config_value
        except:
            return config.config_value 