from __future__ import annotations

import json
from datetime import date, timedelta
from typing import List
import os

import httpx
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import select

from db import SKU, Sale, get_session
from gpt_client import call_gpt

app = FastAPI()

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

SERPER_URL = "https://google.serper.dev/search"
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"

@app.post("/predict-restock")
async def predict_restock(payload: dict, session=Depends(get_session)):
    sku_id = payload["sku_id"]
    days_history = int(payload["days_history"])
    current_stock = int(payload["current_stock"])
    lead_time_days = int(payload["lead_time_days"])
    service_level_pct = float(payload["service_level_pct"])
    budget_currency = payload["budget_currency"]

    since = date.today() - timedelta(days=days_history)
    result = await session.execute(
        select(Sale).where(Sale.sku_id == sku_id, Sale.sold_on >= since)
    )
    sales = [s.quantity for s in result.scalars().all()]

    messages = [
        {"role": "system", "content": "You are a demand forecaster."},
        {
            "role": "user",
            "content": json.dumps({
                "sales_history": sales,
                "current_stock": current_stock,
                "lead_time_days": lead_time_days,
                "service_level_pct": service_level_pct,
                "budget_currency": budget_currency,
            })
        }
    ]
    functions = [
        {
            "name": "restock_response",
            "parameters": {
                "type": "object",
                "properties": {
                    "recommended_qty": {"type": "integer"},
                    "reasoning": {"type": "string"}
                },
                "required": ["recommended_qty", "reasoning"]
            }
        }
    ]
    data = await call_gpt(messages, functions)
    return JSONResponse(content=data)

@app.post("/optimize-markdown")
async def optimize_markdown(payload: dict, session=Depends(get_session)):
    sku_id = payload["sku_id"]
    current_price = float(payload["current_price"])
    current_stock = int(payload["current_stock"])
    sku = await session.get(SKU, sku_id)
    name = sku.name if sku else sku_id

    async with httpx.AsyncClient() as client:
        r = await client.post(
            SERPER_URL,
            headers={"X-API-KEY": SERPER_API_KEY},
            json={"q": f"{name} price"}
        )
        results = r.json().get("organic", [])[:5]
        prices = []
        for item in results:
            text = item.get("snippet", "")
            for token in text.split():
                if token.startswith("$"):
                    try:
                        prices.append(float(token.strip("$")))
                    except ValueError:
                        pass

    messages = [
        {"role": "system", "content": "You optimize discounts."},
        {
            "role": "user",
            "content": json.dumps({
                "our_price": current_price,
                "competitor_prices": prices,
                "current_stock": current_stock,
            })
        }
    ]
    functions = [
        {
            "name": "markdown_response",
            "parameters": {
                "type": "object",
                "properties": {
                    "discount_pct": {"type": "number"},
                    "expected_sell_through_units": {"type": "integer"},
                    "reasoning": {"type": "string"}
                },
                "required": ["discount_pct", "expected_sell_through_units", "reasoning"]
            }
        }
    ]
    data = await call_gpt(messages, functions)
    return JSONResponse(content=data)

@app.post("/liquidate")
async def liquidate(session=Depends(get_session)):
    result = await session.execute(
        select(SKU).where((SKU.days_on_hand > 60) | (SKU.sell_through < 0.2))
    )
    skus = result.scalars().all()
    sku_list = [
        {"id": s.id, "name": s.name, "stock": s.current_stock} for s in skus
    ]
    messages = [
        {"role": "system", "content": "You draft liquidation emails."},
        {"role": "user", "content": json.dumps({"skus": sku_list})}
    ]
    functions = [
        {
            "name": "email_body",
            "parameters": {
                "type": "object",
                "properties": {"body": {"type": "string"}},
                "required": ["body"]
            }
        }
    ]
    data = await call_gpt(messages, functions)

    async with httpx.AsyncClient() as client:
        await client.post(
            SENDGRID_URL,
            headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"},
            json={
                "personalizations": [{"to": [{"email": "ops@example.com"}]}],
                "from": {"email": "noreply@example.com"},
                "subject": "Liquidation Plan",
                "content": [{"type": "text/markdown", "value": data["body"]}],
            },
        )
    return JSONResponse(content={"email_status": "sent"})
