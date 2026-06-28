from fastapi import APIRouter
from datetime import datetime
from decimal import Decimal
from typing import Optional
import requests

from backend.app.database import SessionLocal
from backend.app.models.payment import Payment
from backend.app.models.vip import VIP
from backend.app.config import BSCSCAN_API_KEY, BSC_CHAIN_ID, BSC_WALLET, USDT_BSC_CONTRACT

router = APIRouter()

VIP_PRICES = {
    "silver": Decimal("2.0"),
    "gold": Decimal("5.0"),
    "diamond": Decimal("10.0")
}

ETHERSCAN_V2_URL = "https://api.etherscan.io/v2/api"


def normalize(address: str):
    return address.lower()


def activate_vip_from_payment(payment: Payment, db):
    payment.status = "confirmed"
    payment.confirmed_at = datetime.utcnow()

    vip = db.query(VIP).filter(VIP.telegram_id == payment.telegram_id).first()

    if vip:
        vip.level = payment.plan
        vip.is_active = True
    else:
        vip = VIP(
            telegram_id=payment.telegram_id,
            level=payment.plan,
            is_active=True
        )
        db.add(vip)


def find_matching_usdt_payment(payment: Payment, db):
    try:
        params = {
            "chainid": BSC_CHAIN_ID,
            "module": "account",
            "action": "tokentx",
            "contractaddress": USDT_BSC_CONTRACT,
            "address": BSC_WALLET,
            "page": 1,
            "offset": 100,
            "sort": "desc",
            "apikey": BSCSCAN_API_KEY
        }

        response = requests.get(ETHERSCAN_V2_URL, params=params, timeout=20)
        data = response.json()

        if data.get("status") != "1":
            return None, data.get("message", "API error")

        expected_amount = Decimal(str(payment.amount_usdt))
        wallet = normalize(payment.wallet_address)

        for tx in data.get("result", []):
            tx_hash = tx.get("hash")

            already_used = db.query(Payment).filter(
                Payment.tx_hash == tx_hash,
                Payment.status == "confirmed"
            ).first()

            if already_used:
                continue

            to_address = normalize(tx.get("to", ""))

            if to_address != wallet:
                continue

            decimals = int(tx.get("tokenDecimal", 18))
            amount = Decimal(tx.get("value", "0")) / (Decimal(10) ** decimals)

            tx_time = int(tx.get("timeStamp", "0"))
            payment_time = int(payment.created_at.timestamp())

            if tx_time < payment_time - 600:
                continue

            if amount == expected_amount:
                return tx, None

        return None, "No matching payment found"

    except Exception as e:
        return None, str(e)


def auto_confirm_pending_payments():
    db = SessionLocal()
    try:
        pending_payments = db.query(Payment).filter(Payment.status == "pending").all()

        confirmed = []

        for payment in pending_payments:
            tx, error = find_matching_usdt_payment(payment, db)

            if tx:
                payment.tx_hash = tx.get("hash")
                activate_vip_from_payment(payment, db)

                confirmed.append({
                    "payment_id": payment.id,
                    "telegram_id": payment.telegram_id,
                    "plan": payment.plan,
                    "tx_hash": payment.tx_hash
                })

        db.commit()

        return confirmed

    finally:
        db.close()


@router.post("/payments/create")
def create_payment(telegram_id: str, plan: str):
    plan = plan.lower()

    if plan not in VIP_PRICES:
        return {"error": "Invalid VIP plan"}

    db = SessionLocal()
    try:
        payment = Payment(
            telegram_id=telegram_id,
            plan=plan,
            amount_usdt=float(VIP_PRICES[plan]),
            network="BEP20",
            wallet_address=BSC_WALLET,
            status="pending"
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        unique_amount = VIP_PRICES[plan] + (Decimal(payment.id) / Decimal("1000"))
        payment.amount_usdt = float(unique_amount)

        db.commit()
        db.refresh(payment)

        return {
            "message": "Payment created",
            "payment_id": payment.id,
            "telegram_id": telegram_id,
            "plan": plan,
            "amount_usdt": payment.amount_usdt,
            "network": "BEP20 / BSC",
            "wallet_address": BSC_WALLET,
            "status": payment.status,
            "instruction": f"Send exactly {payment.amount_usdt} USDT via BEP20/BSC. The system will detect it automatically."
        }

    finally:
        db.close()


@router.post("/payments/auto-confirm")
def auto_confirm_payment(payment_id: int):
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment:
            return {"error": "Payment not found"}

        if payment.status != "pending":
            return {"error": "Payment is not pending", "status": payment.status}

        tx, error = find_matching_usdt_payment(payment, db)

        if not tx:
            return {
                "message": "Payment not confirmed yet",
                "reason": error,
                "payment_id": payment.id,
                "expected_amount": payment.amount_usdt,
                "wallet_address": payment.wallet_address
            }

        payment.tx_hash = tx.get("hash")
        activate_vip_from_payment(payment, db)

        db.commit()

        return {
            "message": "Payment detected automatically and VIP activated",
            "payment_id": payment.id,
            "telegram_id": payment.telegram_id,
            "vip_level": payment.plan,
            "tx_hash": payment.tx_hash,
            "status": payment.status
        }

    finally:
        db.close()


@router.post("/payments/auto-confirm-all")
def auto_confirm_all_pending():
    confirmed = auto_confirm_pending_payments()

    return {
        "message": "Auto-confirm all completed",
        "confirmed_count": len(confirmed),
        "confirmed": confirmed
    }


@router.get("/payments/status/{payment_id}")
def payment_status(payment_id: int):
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment:
            return {"error": "Payment not found"}

        return {
            "payment_id": payment.id,
            "telegram_id": payment.telegram_id,
            "plan": payment.plan,
            "amount_usdt": payment.amount_usdt,
            "network": payment.network,
            "wallet_address": payment.wallet_address,
            "tx_hash": payment.tx_hash,
            "status": payment.status,
            "created_at": payment.created_at,
            "confirmed_at": payment.confirmed_at
        }

    finally:
        db.close()


@router.get("/payments/user/{telegram_id}")
def user_payments(telegram_id: str):
    db = SessionLocal()
    try:
        payments = (
            db.query(Payment)
            .filter(Payment.telegram_id == telegram_id)
            .order_by(Payment.created_at.desc())
            .all()
        )

        return payments

    finally:
        db.close()


@router.get("/payments/admin/list")
def list_payments(status: Optional[str] = None):
    db = SessionLocal()
    try:
        query = db.query(Payment)

        if status:
            query = query.filter(Payment.status == status)

        payments = query.order_by(Payment.created_at.desc()).all()

        return payments

    finally:
        db.close()


@router.post("/payments/submit-tx")
def submit_tx(payment_id: int, tx_hash: str):
    return {
        "message": "Manual TX submission disabled. Use automatic detection.",
        "payment_id": payment_id
    }