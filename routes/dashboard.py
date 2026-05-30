from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models
from datetime import date

router = APIRouter()

@router.get("/")
def get_dashboard(db: Session = Depends(get_db)):
    today    = date.today()
    invoices = db.query(models.Invoice).filter(
        models.Invoice.status.in_(["open", "partial"])
    ).all()

    buckets       = {"0_30": 0, "31_60": 0, "61_90": 0, "90_plus": 0}
    bucket_counts = {"0_30": 0, "31_60": 0, "61_90": 0, "90_plus": 0}
    total = 0

    for inv in invoices:
        outstanding = inv.amount - inv.amount_paid
        dpd = max(0, (today - inv.due_date).days)
        total += outstanding
        if dpd <= 30:
            buckets["0_30"] += outstanding;       bucket_counts["0_30"] += 1
        elif dpd <= 60:
            buckets["31_60"] += outstanding;      bucket_counts["31_60"] += 1
        elif dpd <= 90:
            buckets["61_90"] += outstanding;      bucket_counts["61_90"] += 1
        else:
            buckets["90_plus"] += outstanding;    bucket_counts["90_plus"] += 1

    return {
        "total_outstanding": total,
        "total_invoices":    len(invoices),
        "buckets":           buckets,
        "bucket_counts":     bucket_counts,
    }
