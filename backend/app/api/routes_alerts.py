"""
GET  /api/alerts        — list all alerts
POST /api/alerts/{id}/resolve — mark an alert as resolved
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.database import get_db
from app.models.db_models import AlertRecord
from app.utils.seed import ensure_seeded

router = APIRouter()


@router.get("/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    ensure_seeded(db)

    all_alerts = (
        db.query(AlertRecord)
        .order_by(AlertRecord.timestamp.desc())
        .limit(100)
        .all()
    )

    active = [a for a in all_alerts if not a.resolved]
    resolved = [a for a in all_alerts if a.resolved]

    def serialize(a: AlertRecord) -> dict:
        return {
            "id": a.id,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "resolved": a.resolved,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        }

    return {
        "active_count": len(active),
        "resolved_count": len(resolved),
        "total": len(all_alerts),
        "alerts": [serialize(a) for a in all_alerts],
    }


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(AlertRecord).filter(AlertRecord.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    alert.resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)

    return {
        "success": True,
        "message": f"Alert {alert_id} marked as resolved",
        "alert_id": alert_id,
    }