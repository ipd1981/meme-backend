from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MSME Collections API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes import dashboard, buyers, invoices
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(buyers.router,    prefix="/api/buyers",    tags=["Buyers"])
app.include_router(invoices.router,  prefix="/api/invoices",  tags=["Invoices"])

@app.get("/")
def root():
    return {"status": "running", "message": "MSME Collections API is live ✓"}
