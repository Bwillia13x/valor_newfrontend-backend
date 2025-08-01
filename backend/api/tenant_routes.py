"""
Tenant Management API Routes for Valor IVX
Phase 8 Implementation - Multi-Tenant Architecture

This module provides comprehensive tenant management endpoints:
- Tenant creation and management
- Subscription handling
- Tenant-specific configurations
- Branding and theming
- Usage statistics
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Any, Optional

# Import tenant management and RBAC
from tenant_manager import TenantManager, TenantConfig
from models.rbac import RBACManager, Permission, Tenant, User, Organization
from auth import auth_required, get_current_user_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
tenant_bp = Blueprint('tenant', __name__, url_prefix='/api/tenant')

# Initialize managers
rbac_manager = RBACManager()

@tenant_bp.route('/create', methods=['POST'])
def create_tenant():
    """Create a new tenant with default organization"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'domain', 'admin_email', 'admin_username', 'admin_password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create tenant configuration
        config = TenantConfig(
            name=data['name'],
            domain=data['domain'],
            subscription_plan=data.get('subscription_plan', 'basic'),
            max_users=data.get('max_users', 10),
            max_storage_gb=data.get('max_storage_gb', 1),
            features_enabled=data.get('features_enabled'),
            branding_config=data.get('branding_config')
        )
        
        # Initialize tenant manager
        tenant_manager = TenantManager(current_app.db.session)
        
        # Create tenant
        tenant = tenant_manager.create_tenant(config)
        
        # Create admin user
        from auth import AuthManager
        auth_manager = AuthManager()
        password_hash = auth_manager.hash_password(data['admin_password'])
        
        user_data = {
            'email': data['admin_email'],
            'username': data['admin_username'],
            'password_hash': password_hash,
            'first_name': data.get('admin_first_name'),
            'last_name': data.get('admin_last_name'),
            'organization_id': tenant.organizations[0].id if tenant.organizations else None
        }
        
        admin_user = tenant_manager.create_tenant_user(tenant.id, user_data, 'Admin')
        
        return jsonify({
            'success': True,
            'tenant_id': tenant.id,
            'tenant_name': tenant.name,
            'admin_user_id': admin_user.id,
            'message': f'Tenant {tenant.name} created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create tenant: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_bp.route('/<int:tenant_id>/users', methods=['POST'])
@auth_required
def create_tenant_user(tenant_id):
    """Create a new user within a tenant"""
    try:
        current_user_id = get_current_user_id()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if not rbac_manager.has_permission(current_user, Permission.ADMIN_USERS, tenant_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['email', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Hash password
        from auth import AuthManager
        auth_manager = AuthManager()
        password_hash = auth_manager.hash_password(data['password'])
        
        user_data = {
            'email': data['email'],
            'username': data['username'],
            'password_hash': password_hash,
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'organization_id': data.get('organization_id')
        }
        
        # Initialize tenant manager
        tenant_manager = TenantManager(current_app.db.session)
        
        # Create user
        user = tenant_manager.create_tenant_user(
            tenant_id, 
            user_data, 
            data.get('role_name', 'Viewer')
        )
        
        return jsonify({
            'success': True,
            'user_id': user.id,
            'email': user.email,
            'message': f'User {user.email} created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create tenant user: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_bp.route('/<int:tenant_id>/users', methods=['GET'])
@auth_required
def list_tenant_users(tenant_id):
    """List all users within a tenant"""
    try:
        current_user_id = get_current_user_id()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if not rbac_manager.has_permission(current_user, Permission.ADMIN_USERS, tenant_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        users = rbac_manager.get_tenant_users(tenant_id)
        
        user_list = []
        for user in users:
            user_data = {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'organization_id': user.organization_id,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'roles': [role.name for role in user.roles if role.is_active]
            }
            user_list.append(user_data)
        
        return jsonify({
            'success': True,
            'users': user_list,
            'total_users': len(user_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to list tenant users: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_bp.route('/<int:tenant_id>/configuration', methods=['PUT'])
@auth_required
def update_tenant_configuration(tenant_id):
    """Update tenant-specific configuration"""
    try:
        current_user_id = get_current_user_id()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT, tenant_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        config_key = data.get('config_key')
        config_value = data.get('config_value')
        config_type = data.get('config_type', 'string')
        
        if not config_key or config_value is None:
            return jsonify({'error': 'Missing config_key or config_value'}), 400
        
        # Initialize tenant manager
        tenant_manager = TenantManager(current_app.db.session)
        
        # Update configuration
        success = tenant_manager.update_tenant_configuration(
            tenant_id, config_key, config_value, config_type
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Configuration {config_key} updated successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to update configuration'}), 500
        
    except Exception as e:
        logger.error(f"Failed to update tenant configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_bp.route('/<int:tenant_id>/configuration', methods=['GET'])
@auth_required
def get_tenant_configuration(tenant_id):
    """Get tenant-specific configuration"""
    try:
        current_user_id = get_current_user_id()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if not rbac_manager.validate_tenant_access(current_user, tenant_id):
            return jsonify({'error': 'Access denied'}), 403
        
        config_key = request.args.get('config_key')
        
        # Initialize tenant manager
        tenant_manager = TenantManager(current_app.db.session)
        
        # Get configuration
        config = tenant_manager.get_tenant_configuration(tenant_id, config_key)
        
        return jsonify({
            'success': True,
            'configuration': config
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get tenant configuration: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_bp.route('/<int:tenant_id>/subscription', methods=['PUT'])
@auth_required
def update_subscription(tenant_id):
    """Update tenant subscription"""
    try:
        current_user_id = get_current_user_id()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT, tenant_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        plan_name = data.get('plan_name')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        if not plan_name:
            return jsonify({'error': 'Missing plan_name'}), 400
        
        # Initialize tenant manager
        tenant_manager = TenantManager(current_app.db.session)
        
        # Update subscription
        success = tenant_manager.update_subscription(tenant_id, plan_name, billing_cycle)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Subscription updated to {plan_name} plan'
            }), 200
        else:
            return jsonify({'error': 'Failed to update subscription'}), 500
        
    except Exception as e:
        logger.error(f"Failed to update subscription: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_bp.route('/<int:tenant_id>/usage', methods=['GET'])
@auth_required
def get_tenant_usage(tenant_id):
    """Get tenant usage statistics"""
    try:
        current_user_id = get_current_user_id()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if not rbac_manager.has_permission(current_user, Permission.VIEW_TENANT_ANALYTICS, tenant_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        # Initialize tenant manager
        tenant_manager = TenantManager(current_app.db.session)
        
        # Get usage stats
        usage_stats = tenant_manager.get_tenant_usage_stats(tenant_id)
        
        if usage_stats:
            return jsonify({
                'success': True,
                'usage_stats': usage_stats
            }), 200
        else:
            return jsonify({'error': 'Tenant not found'}), 404
        
    except Exception as e:
        logger.error(f"Failed to get tenant usage: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_bp.route('/<int:tenant_id>/branding', methods=['PUT'])
@auth_required
def update_tenant_branding(tenant_id):
    """Update tenant branding configuration"""
    try:
        current_user_id = get_current_user_id()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT, tenant_id):
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Initialize tenant manager
        tenant_manager = TenantManager(current_app.db.session)
        
        # Update branding configuration
        branding_config = {
            'primary_color': data.get('primary_color'),
            'secondary_color': data.get('secondary_color'),
            'logo_url': data.get('logo_url'),
            'company_name': data.get('company_name'),
            'custom_css': data.get('custom_css'),
            'theme': data.get('theme', 'light')
        }
        
        # Remove None values
        branding_config = {k: v for k, v in branding_config.items() if v is not None}
        
        success = tenant_manager.update_tenant_configuration(
            tenant_id, 'branding_config', json.dumps(branding_config), 'json'
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Branding configuration updated successfully'
            }), 200
        else:
            return jsonify({'error': 'Failed to update branding configuration'}), 500
        
    except Exception as e:
        logger.error(f"Failed to update tenant branding: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_bp.route('/<int:tenant_id>/branding', methods=['GET'])
@auth_required
def get_tenant_branding(tenant_id):
    """Get tenant branding configuration"""
    try:
        current_user_id = get_current_user_id()
        current_user = User.query.get(current_user_id)
        
        # Check permissions
        if not rbac_manager.validate_tenant_access(current_user, tenant_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Initialize tenant manager
        tenant_manager = TenantManager(current_app.db.session)
        
        # Get branding configuration
        config = tenant_manager.get_tenant_configuration(tenant_id, 'branding_config')
        
        if 'branding_config' in config:
            branding = config['branding_config']
        else:
            # Return default branding
            branding = tenant_manager._get_default_branding()
        
        return jsonify({
            'success': True,
            'branding': branding
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get tenant branding: {str(e)}")
        return jsonify({'error': str(e)}), 500

@tenant_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans"""
    try:
        # Initialize tenant manager
        tenant_manager = TenantManager(current_app.db.session)
        
        plans = {}
        for plan_key, plan in tenant_manager.subscription_plans.items():
            plans[plan_key] = {
                'name': plan.name,
                'price_monthly': plan.price_monthly,
                'price_yearly': plan.price_yearly,
                'max_users': plan.max_users,
                'max_storage_gb': plan.max_storage_gb,
                'features': plan.features,
                'description': plan.description
            }
        
        return jsonify({
            'success': True,
            'plans': plans
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get subscription plans: {str(e)}")
        return jsonify({'error': str(e)}), 500 