from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship


# New declarative base for enterprise features to avoid collision with legacy models
EnterpriseBase = declarative_base(name="EnterpriseBase")


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
    tenant_id = Column(String(64), nullable=False, index=True)  # string id to avoid cross-model FK
    plan_id = Column(Integer, ForeignKey("plan_definitions.id", ondelete="RESTRICT"), nullable=False, index=True)
    effective_from = Column(DateTime, nullable=False, default=datetime.utcnow)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    overrides = Column(JSON, nullable=True)  # per-tenant overrides for quotas/limits
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    plan = relationship("PlanDefinition", back_populates="tenant_plans")

    def __repr__(self) -> str:
        return f"<TenantPlan tenant_id={self.tenant_id!r} plan_id={self.plan_id} active={self.is_active}>"


class QuotaUsage(EnterpriseBase):
    __tablename__ = "quota_usage"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "window_start", "metric_key", name="uq_quota_window_metric"),
        CheckConstraint("window_end IS NULL OR window_end >= window_start", name="ck_quota_window_bounds"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    metric_key = Column(String(64), nullable=False, index=True)  # e.g., 'requests', 'tokens', 'jobs'
    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=True)
    used = Column(BigInteger, nullable=False, default=0)
    limit = Column(BigInteger, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<QuotaUsage tenant={self.tenant_id!r} metric={self.metric_key!r} used={self.used}/{self.limit}>"


class RateLimit(EnterpriseBase):
    __tablename__ = "rate_limits"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "bucket_key", name="uq_ratelimit_bucket"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=True, index=True)
    bucket_key = Column(String(128), nullable=False, index=True)  # scope of limit (route or feature)
    capacity = Column(Integer, nullable=False)  # tokens
    refill_per_min = Column(Integer, nullable=False)  # tokens per minute
    tokens = Column(Integer, nullable=False)  # current tokens remaining
    last_refill_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    burst = Column(Integer, nullable=True)  # optional burst capacity
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<RateLimit tenant={self.tenant_id!r} bucket={self.bucket_key!r} tokens={self.tokens}>"


class BillingEvent(EnterpriseBase):
    __tablename__ = "billing_events"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_billing_idempotency"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(64), nullable=False, index=True)
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
