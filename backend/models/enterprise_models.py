"""
Enterprise models for Valor IVX platform
Separate from legacy models to enable clean migration path
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
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
    tenant_plans = relationship("TenantPlan", back_populates="tenant")
    
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


class PlanDefinition(EnterpriseBase):
    __tablename__ = "plan_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_key = Column(String(64), nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    features = Column(JSON, nullable=True)  # feature flags / limits per plan
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant_plans = relationship("TenantPlan", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<PlanDefinition plan_key={self.plan_key!r} name={self.name!r}>"


class TenantPlan(EnterpriseBase):
    __tablename__ = "tenant_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_plans_tenant_once"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plan_definitions.id", ondelete="RESTRICT"), nullable=False, index=True)
    effective_from = Column(DateTime, nullable=False, default=datetime.utcnow)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    overrides = Column(JSON, nullable=True)  # per-tenant overrides for quotas/limits
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    tenant = relationship("Tenant", back_populates="tenant_plans")
    plan = relationship("PlanDefinition", back_populates="tenant_plans")

    def __repr__(self) -> str:
        return f"<TenantPlan tenant_id={self.tenant_id!r} plan_id={self.plan_id} active={self.is_active}>"


class QuotaUsage(EnterpriseBase):
    """Quota tracking for billing and limits"""
    __tablename__ = 'quota_usage'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    user_id = Column(String(64), nullable=True, index=True)
    quota_type = Column(String(100), nullable=False)  # e.g., 'api_calls', 'storage_mb'
    metric_key = Column(String(64), nullable=False, index=True)  # e.g., 'requests', 'tokens', 'jobs'
    usage_count = Column(Integer, default=0, nullable=False)
    usage_amount = Column(Float, default=0.0, nullable=False)  # For storage, etc.
    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=True)
    period_start = Column(DateTime, nullable=False)  # Start of billing period
    period_end = Column(DateTime, nullable=False)  # End of billing period
    used = Column(BigInteger, nullable=False, default=0)
    limit = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_quota_tenant_type', 'tenant_id', 'quota_type'),
        Index('idx_quota_period', 'period_start', 'period_end'),
        UniqueConstraint('tenant_id', 'quota_type', 'period_start', name='uq_quota_tenant_type_period'),
        UniqueConstraint("tenant_id", "user_id", "window_start", "metric_key", name="uq_quota_window_metric"),
        CheckConstraint("window_end IS NULL OR window_end >= window_start", name="ck_quota_window_bounds"),
    )

    def __repr__(self) -> str:
        return f"<QuotaUsage tenant={self.tenant_id!r} metric={self.metric_key!r} used={self.used}/{self.limit}>"


class RateLimit(EnterpriseBase):
    """Rate limiting configuration per tenant"""
    __tablename__ = 'rate_limits'
    
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False)
    user_id = Column(String(64), nullable=True, index=True)
    endpoint = Column(String(255), nullable=False)  # e.g., '/api/v1/analytics'
    method = Column(String(10), nullable=False)  # GET, POST, etc.
    bucket_key = Column(String(128), nullable=False, index=True)  # scope of limit (route or feature)
    requests_per_minute = Column(Integer, default=60, nullable=False)
    burst_limit = Column(Integer, default=100, nullable=False)
    capacity = Column(Integer, nullable=False)  # tokens
    refill_per_min = Column(Integer, nullable=False)  # tokens per minute
    tokens = Column(Integer, nullable=False)  # current tokens remaining
    last_refill_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    burst = Column(Integer, nullable=True)  # optional burst capacity
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="rate_limits")
    
    __table_args__ = (
        Index('idx_rate_limit_tenant_endpoint', 'tenant_id', 'endpoint'),
        UniqueConstraint('tenant_id', 'endpoint', 'method', name='uq_rate_limit_tenant_endpoint_method'),
        UniqueConstraint("tenant_id", "user_id", "bucket_key", name="uq_ratelimit_bucket"),
    )

    def __repr__(self) -> str:
        return f"<RateLimit tenant={self.tenant_id!r} bucket={self.bucket_key!r} tokens={self.tokens}>"


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


class BillingEvent(EnterpriseBase):
    __tablename__ = "billing_events"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_billing_idempotency"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # e.g., 'usage.report', 'invoice.paid'
    idempotency_key = Column(String(128), nullable=False, index=True)
    payload = Column(JSON, nullable=True)
    processed = Column(Boolean, nullable=False, default=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<BillingEvent tenant={self.tenant_id!r} type={self.event_type!r} processed={self.processed}>"


class ProviderStatus(EnterpriseBase):
    __tablename__ = "provider_status"
    __table_args__ = (
        UniqueConstraint("provider_key", name="uq_provider_key"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_key = Column(String(64), nullable=False, index=True)  # e.g., 'alpha_vantage', 'polygon'
    status = Column(String(16), nullable=False, default="unknown")  # healthy|degraded|unavailable|unknown
    last_checked_at = Column(DateTime, nullable=True)
    metrics = Column(JSON, nullable=True)  # SLA metrics (latency, error_rate, etc.)
    details = Column(Text, nullable=True)  # optional human-readable details
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<ProviderStatus provider={self.provider_key!r} status={self.status!r}>"
