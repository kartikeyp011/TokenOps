"""
SQLAlchemy ORM models.
Three tables: RequestLog, AlertRecord, PolicyConfig.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.database import Base


class RequestLog(Base):
    """
    Every proxy request is stored here.
    This is the source of truth for all analytics.
    """
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Request info
    prompt = Column(Text, nullable=False)
    prompt_preview = Column(String(300), nullable=True)   # first 300 chars
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)

    # Model tracking
    model_requested = Column(String(100), nullable=True)  # what client asked for
    model_used = Column(String(100), nullable=False)       # what we actually used
    provider = Column(String(50), nullable=False)          # google / groq / mock

    # Router decision
    routing_decision = Column(String(50), nullable=False)  # pass_through / cheapest / quality / policy_override
    routing_reason = Column(String(500), nullable=True)

    # Cost tracking
    estimated_cost_usd = Column(Float, default=0.0)
    cost_saved_usd = Column(Float, default=0.0)

    # Status
    status = Column(String(20), default="success")         # success / error / blocked / cached
    error_message = Column(String(500), nullable=True)
    latency_ms = Column(Integer, default=0)
    is_cached = Column(Boolean, default=False)
    is_mock = Column(Boolean, default=False)

    # Response preview
    response_preview = Column(String(300), nullable=True)

    def __repr__(self):
        return f"<RequestLog id={self.id} model={self.model_used} cost={self.estimated_cost_usd}>"


class AlertRecord(Base):
    """
    Triggered alerts — budget exceeded, spikes, rate surges, errors.
    """
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    alert_type = Column(String(50), nullable=False)   # budget_exceeded | cost_spike | rate_surge | high_error_rate
    severity = Column(String(20), default="warning")  # info | warning | critical
    message = Column(String(1000), nullable=False)
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Deduplication: don't fire same alert type within window
    dedup_key = Column(String(200), nullable=True, index=True)

    def __repr__(self):
        return f"<AlertRecord type={self.alert_type} severity={self.severity} resolved={self.resolved}>"


class PolicyConfig(Base):
    """
    Runtime-editable policy values.
    Seeded with defaults on first run. Can be updated via PUT /api/policies/{name}.
    """
    __tablename__ = "policy_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    policy_name = Column(String(100), unique=True, nullable=False, index=True)
    policy_value = Column(String(500), nullable=False)   # stored as string, parsed by type
    description = Column(String(500), nullable=True)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<PolicyConfig name={self.policy_name} value={self.policy_value}>"


class SeedState(Base):
    """
    Tracks whether seed data has been applied.
    Prevents re-seeding on every restart.
    """
    __tablename__ = "seed_state"

    id = Column(Integer, primary_key=True, default=1)
    seeded = Column(Boolean, default=False)
    seeded_at = Column(DateTime(timezone=True), nullable=True)