"""
GET /api/policies         — list all policies
PUT /api/policies/{name}  — update a policy value at runtime
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel
from app.db.database import get_db
from app.models.db_models import PolicyConfig
from app.utils.seed import ensure_seeded

router = APIRouter()


class PolicyUpdateRequest(BaseModel):
    value: str


@router.get("/policies")
async def get_policies(db: Session = Depends(get_db)):
    ensure_seeded(db)

    policies = db.query(PolicyConfig).order_by(PolicyConfig.policy_name).all()

    return {
        "total": len(policies),
        "policies": [
            {
                "name": p.policy_name,
                "value": p.policy_value,
                "description": p.description or "",
                "last_updated": p.last_updated.isoformat() if p.last_updated else None,
            }
            for p in policies
        ],
    }


@router.put("/policies/{policy_name}")
async def update_policy(
    policy_name: str,
    body: PolicyUpdateRequest,
    db: Session = Depends(get_db),
):
    policy = (
        db.query(PolicyConfig)
        .filter(PolicyConfig.policy_name == policy_name)
        .first()
    )
    if not policy:
        raise HTTPException(
            status_code=404,
            detail=f"Policy '{policy_name}' not found. Valid names: max_tokens_per_request, daily_budget_cap_usd, rate_limit_rpm, routing_strategy, allowed_models",
        )

    policy.policy_value = body.value
    policy.last_updated = datetime.now(timezone.utc)
    db.commit()
    db.refresh(policy)

    return {
        "success": True,
        "message": f"Policy '{policy_name}' updated to '{body.value}'",
        "policy": {
            "name": policy.policy_name,
            "value": policy.policy_value,
            "last_updated": policy.last_updated.isoformat(),
        },
    }