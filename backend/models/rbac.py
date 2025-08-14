from enum import Enum
from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Permission(Enum):
    READ_MODELS = "read_models"
    WRITE_MODELS = "write_models"
    DELETE_MODELS = "delete_models"
    SHARE_MODELS = "share_models"
    ADMIN_USERS = "admin_users"
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    MANAGE_ORGANIZATION = "manage_organization"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    CONFIGURE_INTEGRATIONS = "configure_integrations"
    MANAGE_TENANT = "manage_tenant"
    VIEW_TENANT_ANALYTICS = "view_tenant_analytics"

class Tenant(db.Model):
    """Multi-tenant architecture: Tenant model for complete data isolation"""
    __tablename__ = 'tenant'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    domain = Column(String(100), unique=True, nullable=False)
    subscription_plan = Column(String(50), default='basic')  # basic, professional, enterprise
    subscription_status = Column(String(20), default='active')  # active, suspended, cancelled
    subscription_expires = Column(DateTime(timezone=True))
    max_users = Column(Integer, default=10)
    max_storage_gb = Column(Integer, default=1)
    features_enabled = Column(JSON)  # JSON array of enabled features
    branding_config = Column(JSON)  # JSON object with branding settings
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    organizations = relationship("Organization", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")

class Organization(db.Model):
    __tablename__ = 'organization'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="organizations")
    users = relationship("User", back_populates="organization")
    roles = relationship("Role", back_populates="organization")
    audit_logs = relationship("AuditLog", back_populates="organization")

from sqlalchemy import UniqueConstraint


class Role(db.Model):
    __tablename__ = 'role'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    permissions = Column(Text)  # JSON array of permissions
    organization_id = Column(Integer, ForeignKey('organization.id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    organization = relationship("Organization", back_populates="roles")
    tenant = relationship("Tenant")
    users = relationship("User", secondary="user_roles", back_populates="roles")

    __table_args__ = (
        UniqueConstraint('name', 'organization_id', name='_name_organization_uc'),
    )

class User(db.Model):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    organization_id = Column(Integer, ForeignKey('organization.id'))
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    tenant = relationship("Tenant")
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user")

# Association table for many-to-many relationship between User and Role
user_roles = db.Table('user_roles',
    db.Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    db.Column('role_id', Integer, ForeignKey('role.id'), primary_key=True),
    db.Column('assigned_at', DateTime(timezone=True), server_default=func.now())
)

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    organization_id = Column(Integer, ForeignKey('organization.id'))
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    details = Column(Text)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    organization = relationship("Organization", back_populates="audit_logs")
    tenant = relationship("Tenant", back_populates="audit_logs")

class TenantConfiguration(db.Model):
    """Tenant-specific configuration settings"""
    __tablename__ = 'tenant_configuration'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=False)
    config_key = Column(String(100), nullable=False)
    config_value = Column(Text)
    config_type = Column(String(20), default='string')  # string, json, boolean, number
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'config_key', name='_tenant_config_uc'),
    )

class Subscription(db.Model):
    """Subscription management for tenants"""
    __tablename__ = 'subscription'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenant.id'), nullable=False)
    plan_name = Column(String(50), nullable=False)
    status = Column(String(20), default='active')  # active, suspended, cancelled, expired
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True))
    billing_cycle = Column(String(20), default='monthly')  # monthly, quarterly, yearly
    amount = Column(Integer)  # Amount in cents
    currency = Column(String(3), default='USD')
    features = Column(JSON)  # JSON array of features included in this plan
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tenant = relationship("Tenant")

class RBACManager:
    """Role-Based Access Control Manager with Multi-Tenant Support"""
    
    def __init__(self):
        self.permissions = Permission
    
    def has_permission(self, user, permission, tenant_id=None):
        """Check if user has specific permission within tenant context"""
        if not user or not user.is_active:
            return False
        
        # If tenant_id is provided, ensure user belongs to that tenant
        if tenant_id and user.tenant_id != tenant_id:
            return False
        
        # Check through roles
        for role in user.roles:
            if role.is_active and permission.value in self._parse_permissions(role.permissions):
                # Ensure the role belongs to the user's organization and tenant
                if (role.organization_id == user.organization_id and 
                    (not tenant_id or role.tenant_id == tenant_id)):
                    return True
        
        return False
    
    def has_role(self, user, role_name, tenant_id=None):
        """Check if user has specific role within tenant context"""
        if not user or not user.is_active:
            return False
        
        # If tenant_id is provided, ensure user belongs to that tenant
        if tenant_id and user.tenant_id != tenant_id:
            return False
        
        return any(role.name == role_name and role.is_active and 
                  (not tenant_id or role.tenant_id == tenant_id) for role in user.roles)
    
    def get_user_permissions(self, user, tenant_id=None):
        """Get all permissions for a user within tenant context"""
        if not user or not user.is_active:
            return []
        
        # If tenant_id is provided, ensure user belongs to that tenant
        if tenant_id and user.tenant_id != tenant_id:
            return []
        
        permissions = set()
        for role in user.roles:
            if role.is_active and (not tenant_id or role.tenant_id == tenant_id):
                permissions.update(self._parse_permissions(role.permissions))
        
        return list(permissions)
    
    def _parse_permissions(self, permissions_json):
        """Parse JSON permissions string"""
        import json
        try:
            return json.loads(permissions_json) if permissions_json else []
        except:
            return []
    
    def create_role(self, name, description, permissions_list, organization_id, tenant_id):
        """Create a new role within tenant context"""
        permissions_json = json.dumps([p.value for p in permissions_list])
        
        role = Role(
            name=name,
            description=description,
            permissions=permissions_json,
            organization_id=organization_id,
            tenant_id=tenant_id
        )
        
        db.session.add(role)
        db.session.commit()
        return role
    
    def assign_role_to_user(self, user, role):
        """Assign role to user"""
        if role not in user.roles:
            user.roles.append(role)
            db.session.commit()
    
    def remove_role_from_user(self, user, role):
        """Remove role from user"""
        if role in user.roles:
            user.roles.remove(role)
            db.session.commit()
    
    def log_user_action(self, user, action, resource_type=None, resource_id=None, details=None):
        """Log user action for audit purposes with tenant context"""
        log = AuditLog(
            user_id=user.id,
            organization_id=user.organization_id,
            tenant_id=user.tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if details else None
        )
        
        db.session.add(log)
        db.session.commit()
    
    def get_user_roles(self, user):
        """Get all roles for a user"""
        if not user or not user.is_active:
            return []
        
        return [role for role in user.roles if role.is_active]
    
    def get_organization_roles(self, organization_id, tenant_id=None):
        """Get all roles for an organization within tenant context"""
        query = Role.query.filter_by(organization_id=organization_id, is_active=True)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        return query.all()
    
    def get_tenant_roles(self, tenant_id):
        """Get all roles for a tenant"""
        return Role.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    def create_default_roles(self, organization_id, tenant_id):
        """Create default roles for new organization within tenant context"""
        default_roles = [
            {
                'name': 'Admin',
                'description': 'Full administrative access',
                'permissions': list(Permission)
            },
            {
                'name': 'Analyst',
                'description': 'Can create and modify models',
                'permissions': [
                    Permission.READ_MODELS,
                    Permission.WRITE_MODELS,
                    Permission.SHARE_MODELS,
                    Permission.VIEW_ANALYTICS,
                    Permission.EXPORT_DATA
                ]
            },
            {
                'name': 'Viewer',
                'description': 'Read-only access',
                'permissions': [
                    Permission.READ_MODELS,
                    Permission.VIEW_ANALYTICS
                ]
            },
            {
                'name': 'Guest',
                'description': 'Limited access',
                'permissions': [
                    Permission.READ_MODELS
                ]
            }
        ]
        
        for role_data in default_roles:
            self.create_role(
                name=role_data['name'],
                description=role_data['description'],
                permissions_list=role_data['permissions'],
                organization_id=organization_id,
                tenant_id=tenant_id
            )
    
    def get_tenant_users(self, tenant_id):
        """Get all users for a tenant"""
        return User.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    def get_tenant_organizations(self, tenant_id):
        """Get all organizations for a tenant"""
        return Organization.query.filter_by(tenant_id=tenant_id, is_active=True).all()
    
    def validate_tenant_access(self, user, tenant_id):
        """Validate that a user has access to a specific tenant"""
        if not user or not user.is_active:
            return False
        return user.tenant_id == tenant_id
