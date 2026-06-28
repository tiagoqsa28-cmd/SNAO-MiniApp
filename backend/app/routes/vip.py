from fastapi import APIRouter
from backend.app.database import SessionLocal
from backend.app.models.vip import VIP

router = APIRouter()

# 🔐 CONFIGURAÇÃO FIXA
BSC_WALLET = "0xed6ff9d9a17fd0d87e93bc4240e38b748f936d6e"

VIP_PRICES = {
    "silver": 2,
    "gold": 5,
    "diamond": 10
}


# 🚀 GERAR PAGAMENTO
@router.get("/vip/pay")
def get_vip_payment(level: str):
    level = level.lower()

    if level not in VIP_PRICES:
        return {"error": "Invalid VIP level"}

    return {
        "plan": level,
        "amount_usdt": VIP_PRICES[level],
        "network": "BEP20 (BSC)",
        "wallet_address": BSC_WALLET,
        "instruction": f"Send {VIP_PRICES[level]} USDT via BSC network to activate {level} VIP"
    }


# ✅ ATIVAR VIP (MANUAL CONFIRMAÇÃO)
@router.post("/vip/activate")
def activate_vip(telegram_id: str, level: str):
    db = SessionLocal()
    try:
        vip = db.query(VIP).filter(VIP.telegram_id == telegram_id).first()

        if vip:
            vip.level = level
            vip.is_active = True
        else:
            vip = VIP(
                telegram_id=telegram_id,
                level=level,
                is_active=True
            )
            db.add(vip)

        db.commit()

        return {
            "message": "VIP activated successfully",
            "telegram_id": telegram_id,
            "vip_level": level,
            "is_active": True
        }

    finally:
        db.close()


# 🔍 STATUS VIP
@router.get("/vip/status/{telegram_id}")
def vip_status(telegram_id: str):
    db = SessionLocal()
    try:
        vip = db.query(VIP).filter(
            VIP.telegram_id == telegram_id,
            VIP.is_active == True
        ).first()

        if not vip:
            return {
                "telegram_id": telegram_id,
                "vip": False,
                "vip_level": None
            }

        return {
            "telegram_id": telegram_id,
            "vip": True,
            "vip_level": vip.level
        }

    finally:
        db.close()