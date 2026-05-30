from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from datetime import date, datetime
import csv, io

router = APIRouter()

@router.get("/")
def get_invoices(db: Session = Depends(get_db)):
    today = date.today()
    invs  = db.query(models.Invoice).filter(
        models.Invoice.status.in_(["open", "partial"])
    ).all()
    result = []
    for i in invs:
        result.append({
            "id": i.id, "invoice_no": i.invoice_no,
            "buyer_id": i.buyer_id,
            "buyer_name":  i.buyer.name  if i.buyer else "Unknown",
            "buyer_phone": i.buyer.phone if i.buyer else None,
            "due_date": str(i.due_date), "amount": i.amount,
            "outstanding": i.amount - i.amount_paid,
            "status": i.status, "dpd": max(0, (today - i.due_date).days),
        })
    return sorted(result, key=lambda x: x["dpd"], reverse=True)


@router.post("/mark-paid/{invoice_id}")
def mark_paid(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(models.Invoice).filter(models.Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Not found")
    inv.status = "paid"; inv.amount_paid = inv.amount
    db.commit()
    return {"message": f"{inv.invoice_no} marked as paid ✓"}


@router.post("/log-message")
def log_message(data: dict, db: Session = Depends(get_db)):
    c = models.Communication(
        invoice_id=data.get("invoice_id"),
        buyer_id=data.get("buyer_id"),
        channel=data.get("channel", "whatsapp"),
        message=data.get("message"),
    )
    db.add(c); db.commit()
    return {"message": "Logged ✓"}


@router.get("/communications/{buyer_id}")
def get_communications(buyer_id: int, db: Session = Depends(get_db)):
    comms = db.query(models.Communication).filter(
        models.Communication.buyer_id == buyer_id
    ).order_by(models.Communication.sent_at.desc()).all()
    return [{"id": c.id, "channel": c.channel, "message": c.message,
             "sent_at": str(c.sent_at), "status": c.status} for c in comms]


@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except Exception:
        text = content.decode("latin-1")

    reader  = csv.DictReader(io.StringIO(text))
    created = skipped = 0
    errors  = []

    for row_num, row in enumerate(reader, start=2):
        try:
            r = {k.strip().lower().replace(" ", "_"): str(v).strip()
                 for k, v in row.items() if k}

            buyer_name   = _pick(r, ["buyer_name","party_name","name","customer_name"])
            invoice_no   = _pick(r, ["invoice_no","invoice_number","voucher_no","bill_no"])
            invoice_date = _pick(r, ["invoice_date","date","bill_date"])
            due_date     = _pick(r, ["due_date","payment_due","due"])
            amount       = _pick(r, ["amount","total_amount","invoice_amount"])
            phone        = _pick(r, ["phone","mobile","contact","whatsapp"])

            if not all([buyer_name, invoice_no, invoice_date, due_date, amount]):
                errors.append(f"Row {row_num}: missing fields — found: {list(r.keys())[:6]}")
                continue

            inv_date = _parse_date(invoice_date)
            d_date   = _parse_date(due_date)
            if not inv_date or not d_date:
                errors.append(f"Row {row_num}: bad date format '{invoice_date}' — use DD/MM/YYYY")
                continue

            amt = float(str(amount).replace(",","").replace("₹","").replace("Rs.","").strip())

            buyer = db.query(models.Buyer).filter(models.Buyer.name == buyer_name).first()
            if not buyer:
                buyer = models.Buyer(name=buyer_name, phone=phone or None)
                db.add(buyer); db.flush()

            if db.query(models.Invoice).filter(models.Invoice.invoice_no == invoice_no).first():
                skipped += 1; continue

            db.add(models.Invoice(
                buyer_id=buyer.id, invoice_no=invoice_no,
                invoice_date=inv_date, due_date=d_date, amount=amt,
            ))
            created += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    db.commit()
    return {
        "success": True,
        "message": f"{created} invoices imported, {skipped} duplicates skipped.",
        "created": created, "skipped": skipped, "errors": errors[:10],
    }


def _pick(d, keys):
    for k in keys:
        if d.get(k): return d[k]
    return None

def _parse_date(s):
    for fmt in ["%d/%m/%Y","%d-%m-%Y","%Y-%m-%d","%d/%m/%y","%m/%d/%Y","%d %b %Y"]:
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    return None
