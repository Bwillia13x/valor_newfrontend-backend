"""
Enterprise models for Valor IVX platform
Separate from legacy models to enable clean migration path
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, 
    ForeignKey, Index, UniqueConstraint, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Separate base for enterprise models
EnterpriseBase = declarative_base()


class Tenant(EnterpriseBase):
    """Tenant/Organization model"""
    __tablename__ = 'tenants'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    api_keys = relationship("ApiKey", back_populates="tenant")
    rate_limits = relationship("RateLimit", back_populates="tenant")
    
    __table_args__ = (
        Index('idx_tenant_slug', 'slug'),
        Index('idx_tenant_domain', 'domain'),
    )


class User(EnterpriseBase):
    """User model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    email = Column(String(255), nullable=False)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    api_keys = relationship("ApiKey", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_tenant', 'tenant_id'),
        UniqueConstraint('tenant_id', 'email', name='uq_user_tenant_email'),
    )


class ApiKey(EnterpriseBase):
    """API Key model for authentication"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Optional user-specific key
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    permissions = Column(Text, nullable=True)  # JSON array of permissions as text
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    user = relationship("User", back_populates="api_keys")
    
    __table_args__ = (
        Index('idx_api_key_hash', 'key_hash'),
        Index('idx_api_key_tenant', 'tenant_id'),
    )


class RateLimit(EnterpriseBase):
    """Rate limiting configuration per tenant"""
    __tablename__ = 'rate_limits'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    endpoint = Column(String(255), nullable=False)  # e.g., '/api/v1/analytics'
    method = Column(String(10), nullable=False)  # GET, POST, etc.
    requests_per_minute = Column(Integer, default=60, nullable=False)
    burst_limit = Column(Integer, default=100, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="rate_limits")
    
    __table_args__ = (
        Index('idx_rate_limit_tenant_endpoint', 'tenant_id', 'endpoint'),
        UniqueConstraint('tenant_id', 'endpoint', 'method', name='uq_rate_limit_tenant_endpoint_method'),
    )


class AuditLog(EnterpriseBase):
    """Audit logging for compliance and debugging"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(100), nullable=False)  # e.g., 'api_call', 'login', 'data_access'
    resource_type = Column(String(100), nullable=True)  # e.g., 'analytics', 'portfolio'
    resource_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    context_data = Column(Text, nullable=True)  # Additional context as text
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_tenant_action', 'tenant_id', 'action'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_user', 'user_id'),
    )


class QuotaUsage(EnterpriseBase):
    """Quota tracking for billing and limits"""
    __tablename__ = 'quota_usage'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    quota_type = Column(String(100), nullable=False)  # e.g., 'api_calls', 'storage_mb'
    usage_count = Column(Integer, default=0, nullable=False)
    usage_amount = Column(Float, default=0.0, nullable=False)  # For storage, etc.
    period_start = Column(DateTime, nullable=False)  # Start of billing period
    period_end = Column(DateTime, nullable=False)  # End of billing period
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_quota_tenant_type', 'tenant_id', 'quota_type'),
        Index('idx_quota_period', 'period_start', 'period_end'),
        UniqueConstraint('tenant_id', 'quota_type', 'period_start', name='uq_quota_tenant_type_period'),
    )