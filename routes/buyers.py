from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from datetime import date

router = APIRouter()

@router.get("/")
def get_buyers(db: Session = Depends(get_db)):
    today   = date.today()
    buyers  = db.query(models.Buyer).all()
    result  = []
    for b in buyers:
        open_inv = [i for i in b.invoices if i.status in ["open", "partial"]]
        outstanding = sum(i.amount - i.amount_paid for i in open_inv)
        max_dpd = max((max(0, (today - i.due_date).days) for i in open_inv), default=0)
        result.append({
            "id": b.id, "name": b.name, "phone": b.phone,
            "city": b.city, "total_outstanding": outstanding,
            "open_invoice_count": len(open_inv), "max_dpd": max_dpd,
        })
    return sorted(result, key=lambda x: x["total_outstanding"], reverse=True)


@router.get("/{buyer_id}")
def get_buyer(buyer_id: int, db: Session = Depends(get_db)):
    b = db.query(models.Buyer).filter(models.Buyer.id == buyer_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Buyer not found")
    today = date.today()
    invoices = [{
        "id": i.id, "invoice_no": i.invoice_no,
        "invoice_date": str(i.invoice_date), "due_date": str(i.due_date),
        "amount": i.amount, "amount_paid": i.amount_paid,
        "outstanding": i.amount - i.amount_paid,
        "status": i.status, "dpd": max(0, (today - i.due_date).days),
    } for i in b.invoices]
    invoices.sort(key=lambda x: x["dpd"], reverse=True)
    return {
        "id": b.id, "name": b.name, "phone": b.phone,
        "email": b.email, "city": b.city, "gstin": b.gstin,
        "invoices": invoices,
        "total_outstanding": sum(i["outstanding"] for i in invoices if i["status"] != "paid"),
        "total_paid": sum(i["amount_paid"] for i in invoices),
    }


@router.post("/")
def create_buyer(data: dict, db: Session = Depends(get_db)):
    b = models.Buyer(**{k: v for k, v in data.items() if k in ["name","phone","email","city","gstin"]})
    db.add(b); db.commit(); db.refresh(b)
    return {"id": b.id, "name": b.name}
