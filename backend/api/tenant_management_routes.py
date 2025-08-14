"""
Tenant Management API Routes
Phase 8: Enterprise Features
"""

from flask import Blueprint, jsonify, request, g
from typing import Dict, Any, List, Optional
import logging
import json

from ..models.rbac import (
    Tenant, Organization, User, Role, Permission, 
    TenantConfiguration, Subscription, RBACManager
)
from ..auth import auth_required
from ..rate_limiter import rate_limit
from ..middleware.tenant import tenant_required
from ..tenant_manager import TenantManager

# Initialize managers
rbac_manager = RBACManager()
tenant_manager = TenantManager()

tenant_management_bp = Blueprint('tenant_management', __name__, url_prefix='/api/tenant-management')


@tenant_management_bp.route('/tenants', methods=['POST'])
@auth_required
@rate_limit("api")
def create_tenant():
    """Create a new tenant"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'domain', 'subscription_plan']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Create tenant
        tenant_data = {
            'name': data['name'],
            'domain': data['domain'],
            'subscription_plan': data['subscription_plan'],
            'max_users': data.get('max_users', 10),
            'max_storage_gb': data.get('max_storage_gb', 1),
            'features_enabled': data.get('features_enabled', []),
            'branding_config': data.get('branding_config', {})
        }
        
        tenant = tenant_manager.create_tenant(tenant_data)
        
        # Create default organization
        org_data = {
            'name': f"{data['name']} Organization",
            'tenant_id': tenant.id
        }
        organization = tenant_manager.create_organization(org_data)
        
        # Create admin user
        admin_user_data = {
            'email': data.get('admin_email', f"admin@{data['domain']}"),
            'username': data.get('admin_username', 'admin'),
            'password': data.get('admin_password', 'changeme123'),
            'first_name': data.get('admin_first_name', 'Admin'),
            'last_name': data.get('admin_last_name', 'User'),
            'organization_id': organization.id,
            'tenant_id': tenant.id
        }
        admin_user = tenant_manager.create_tenant_user(tenant.id, admin_user_data, 'Admin')
        
        return jsonify({
            "success": True,
            "message": "Tenant created successfully",
            "data": {
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "domain": tenant.domain,
                    "subscription_plan": tenant.subscription_plan
                },
                "organization": {
                    "id": organization.id,
                    "name": organization.name
                },
                "admin_user": {
                    "id": admin_user.id,
                    "email": admin_user.email,
                    "username": admin_user.username
                }
            }
        }), 201
        
    except Exception as e:
        logging.error(f"Error creating tenant: {str(e)}")
        return jsonify({"error": "Failed to create tenant"}), 500


@tenant_management_bp.route('/tenants', methods=['GET'])
@auth_required
@rate_limit("api")
def list_tenants():
    """List all tenants (admin only)"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Query tenants with pagination
        tenants = Tenant.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        tenant_list = []
        for tenant in tenants.items:
            tenant_list.append({
                "id": tenant.id,
                "name": tenant.name,
                "domain": tenant.domain,
                "subscription_plan": tenant.subscription_plan,
                "subscription_status": tenant.subscription_status,
                "max_users": tenant.max_users,
                "max_storage_gb": tenant.max_storage_gb,
                "is_active": tenant.is_active,
                "created_at": tenant.created_at.isoformat() if tenant.created_at else None
            })
        
        return jsonify({
            "success": True,
            "data": {
                "tenants": tenant_list,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": tenants.total,
                    "pages": tenants.pages,
                    "has_next": tenants.has_next,
                    "has_prev": tenants.has_prev
                }
            }
        })
        
    except Exception as e:
        logging.error(f"Error listing tenants: {str(e)}")
        return jsonify({"error": "Failed to list tenants"}), 500


@tenant_management_bp.route('/tenants/<int:tenant_id>', methods=['GET'])
@auth_required
@rate_limit("api")
def get_tenant(tenant_id: int):
    """Get tenant details"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 404
        
        # Get tenant usage stats
        usage_stats = tenant_manager.get_tenant_usage_stats(tenant_id)
        
        return jsonify({
            "success": True,
            "data": {
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "domain": tenant.domain,
                    "subscription_plan": tenant.subscription_plan,
                    "subscription_status": tenant.subscription_status,
                    "subscription_expires": tenant.subscription_expires.isoformat() if tenant.subscription_expires else None,
                    "max_users": tenant.max_users,
                    "max_storage_gb": tenant.max_storage_gb,
                    "features_enabled": tenant.features_enabled,
                    "branding_config": tenant.branding_config,
                    "is_active": tenant.is_active,
                    "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
                    "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None
                },
                "usage_stats": usage_stats
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting tenant: {str(e)}")
        return jsonify({"error": "Failed to get tenant"}), 500


@tenant_management_bp.route('/tenants/<int:tenant_id>', methods=['PUT'])
@auth_required
@rate_limit("api")
def update_tenant(tenant_id: int):
    """Update tenant configuration"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = ['name', 'subscription_plan', 'max_users', 'max_storage_gb', 
                         'features_enabled', 'branding_config', 'is_active']
        
        for field in allowed_fields:
            if field in data:
                setattr(tenant, field, data[field])
        
        # Save changes
        tenant_manager.db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Tenant updated successfully",
            "data": {
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "domain": tenant.domain,
                    "subscription_plan": tenant.subscription_plan,
                    "max_users": tenant.max_users,
                    "max_storage_gb": tenant.max_storage_gb,
                    "features_enabled": tenant.features_enabled,
                    "branding_config": tenant.branding_config,
                    "is_active": tenant.is_active
                }
            }
        })
        
    except Exception as e:
        logging.error(f"Error updating tenant: {str(e)}")
        return jsonify({"error": "Failed to update tenant"}), 500


@tenant_management_bp.route('/tenants/<int:tenant_id>/subscription', methods=['PUT'])
@auth_required
@rate_limit("api")
def update_tenant_subscription(tenant_id: int):
    """Update tenant subscription"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if 'plan_name' not in data:
            return jsonify({"error": "Missing required field: plan_name"}), 400
        
        plan_name = data['plan_name']
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        # Update subscription
        success = tenant_manager.update_subscription(tenant_id, plan_name, billing_cycle)
        
        if not success:
            return jsonify({"error": "Failed to update subscription"}), 500
        
        return jsonify({
            "success": True,
            "message": "Subscription updated successfully",
            "data": {
                "tenant_id": tenant_id,
                "plan_name": plan_name,
                "billing_cycle": billing_cycle
            }
        })
        
    except Exception as e:
        logging.error(f"Error updating subscription: {str(e)}")
        return jsonify({"error": "Failed to update subscription"}), 500


@tenant_management_bp.route('/tenants/<int:tenant_id>/branding', methods=['PUT'])
@auth_required
@rate_limit("api")
def update_tenant_branding(tenant_id: int):
    """Update tenant branding configuration"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 404
        
        data = request.get_json()
        
        # Update branding configuration
        branding_config = tenant.branding_config or {}
        branding_config.update(data)
        
        tenant.branding_config = branding_config
        tenant_manager.db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Branding configuration updated successfully",
            "data": {
                "tenant_id": tenant_id,
                "branding_config": branding_config
            }
        })
        
    except Exception as e:
        logging.error(f"Error updating branding: {str(e)}")
        return jsonify({"error": "Failed to update branding configuration"}), 500


@tenant_management_bp.route('/tenants/<int:tenant_id>/features', methods=['PUT'])
@auth_required
@rate_limit("api")
def update_tenant_features(tenant_id: int):
    """Update tenant feature access"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        tenant = Tenant.query.get(tenant_id)
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 404
        
        data = request.get_json()
        
        if 'features_enabled' not in data:
            return jsonify({"error": "Missing required field: features_enabled"}), 400
        
        # Update features
        tenant.features_enabled = data['features_enabled']
        tenant_manager.db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Features updated successfully",
            "data": {
                "tenant_id": tenant_id,
                "features_enabled": tenant.features_enabled
            }
        })
        
    except Exception as e:
        logging.error(f"Error updating features: {str(e)}")
        return jsonify({"error": "Failed to update features"}), 500


@tenant_management_bp.route('/tenants/<int:tenant_id>/deactivate', methods=['POST'])
@auth_required
@rate_limit("api")
def deactivate_tenant(tenant_id: int):
    """Deactivate a tenant"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.MANAGE_TENANT):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        success = tenant_manager.deactivate_tenant(tenant_id)
        
        if not success:
            return jsonify({"error": "Failed to deactivate tenant"}), 500
        
        return jsonify({
            "success": True,
            "message": "Tenant deactivated successfully",
            "data": {
                "tenant_id": tenant_id
            }
        })
        
    except Exception as e:
        logging.error(f"Error deactivating tenant: {str(e)}")
        return jsonify({"error": "Failed to deactivate tenant"}), 500


@tenant_management_bp.route('/tenants/<int:tenant_id>/usage', methods=['GET'])
@auth_required
@rate_limit("api")
def get_tenant_usage(tenant_id: int):
    """Get detailed tenant usage statistics"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.VIEW_TENANT_ANALYTICS):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        usage_stats = tenant_manager.get_tenant_usage_stats(tenant_id)
        
        return jsonify({
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "usage_stats": usage_stats
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting tenant usage: {str(e)}")
        return jsonify({"error": "Failed to get tenant usage"}), 500


@tenant_management_bp.route('/tenants/<int:tenant_id>/organizations', methods=['GET'])
@auth_required
@rate_limit("api")
def list_tenant_organizations(tenant_id: int):
    """List organizations for a tenant"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.validate_tenant_access(current_user, tenant_id):
            return jsonify({"error": "Access denied"}), 403
        
        organizations = tenant_manager.get_tenant_organizations(tenant_id)
        
        org_list = []
        for org in organizations:
            org_list.append({
                "id": org.id,
                "name": org.name,
                "created_at": org.created_at.isoformat() if org.created_at else None,
                "is_active": org.is_active
            })
        
        return jsonify({
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "organizations": org_list
            }
        })
        
    except Exception as e:
        logging.error(f"Error listing organizations: {str(e)}")
        return jsonify({"error": "Failed to list organizations"}), 500


@tenant_management_bp.route('/tenants/<int:tenant_id>/users', methods=['GET'])
@auth_required
@rate_limit("api")
def list_tenant_users(tenant_id: int):
    """List users for a tenant"""
    try:
        # Check permissions
        current_user = g.current_user
        if not rbac_manager.has_permission(current_user, Permission.ADMIN_USERS, tenant_id):
            return jsonify({"error": "Insufficient permissions"}), 403
        
        users = tenant_manager.get_tenant_users(tenant_id)
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "organization_id": user.organization_id,
                "is_active": user.is_active,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })
        
        return jsonify({
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "users": user_list
            }
        })
        
    except Exception as e:
        logging.error(f"Error listing users: {str(e)}")
        return jsonify({"error": "Failed to list users"}), 500


@tenant_management_bp.route('/subscription-plans', methods=['GET'])
@auth_required
@rate_limit("api")
def get_subscription_plans():
    """Get available subscription plans"""
    try:
        # Define available subscription plans
        plans = {
            "basic": {
                "name": "Basic",
                "price": 99,
                "billing_cycle": "monthly",
                "max_users": 10,
                "max_storage_gb": 1,
                "features": [
                    "basic_analytics",
                    "standard_reports",
                    "email_support"
                ]
            },
            "professional": {
                "name": "Professional",
                "price": 299,
                "billing_cycle": "monthly",
                "max_users": 50,
                "max_storage_gb": 10,
                "features": [
                    "advanced_analytics",
                    "custom_reports",
                    "priority_support",
                    "api_access",
                    "ml_models"
                ]
            },
            "enterprise": {
                "name": "Enterprise",
                "price": 999,
                "billing_cycle": "monthly",
                "max_users": 500,
                "max_storage_gb": 100,
                "features": [
                    "all_professional_features",
                    "custom_branding",
                    "dedicated_support",
                    "sla_guarantee",
                    "advanced_security",
                    "audit_logs"
                ]
            }
        }
        
        return jsonify({
            "success": True,
            "data": {
                "plans": plans
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting subscription plans: {str(e)}")
        return jsonify({"error": "Failed to get subscription plans"}), 500 