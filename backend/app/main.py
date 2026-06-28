from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USERS_FILE = "users.json"
PAYMENTS_FILE = "payments.json"
REFERRALS_FILE = "referrals.json"
ALERTS_FILE = "alerts.json"
MISSIONS_FILE = "missions.json"
FRONTEND_DIR = os.path.abspath("frontend")

for file in [USERS_FILE, PAYMENTS_FILE, ALERTS_FILE, REFERRALS_FILE, MISSIONS_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)


class UserData(BaseModel):
    user_id: str
    username: str = "Sardine"
    balance: float
    tap_points: int
    level: int
    streak: int
    referrer_id: str = ""

class AlertData(BaseModel):
    user_id: str
    asset: str
    alert_type: str

class ReferralData(BaseModel):
    user_id: str
    username: str = "Sardine"
    first_name: str = "Sardine"
    referral_code: str
    inviter_id: str = ""

class MissionData(BaseModel):
    user_id: str
    mission_type: str
    reward: float

class PaymentData(BaseModel):
    user_id: str
    plan_key: str
    plan_name: str
    amount: float
    reward_per_24h: float
    network: str
    address: str

@app.post("/save-user")
def save_user(data: UserData):

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    existing_user = users.get(data.user_id, {})

    users[data.user_id] = {
        "user_id": data.user_id,
        "username": data.username,
        "balance": data.balance,
        "tap_points": data.tap_points,
        "level": data.level,
        "streak": data.streak,
        "active_vip_plan": existing_user.get("active_vip_plan", "free"),
        "pending_vip_plan": existing_user.get("pending_vip_plan", ""),
        "vip_expires_at": existing_user.get("vip_expires_at", ""),
        "vip_reward_per_24h": existing_user.get("vip_reward_per_24h", 1),
        "referral_count": existing_user.get("referral_count", 0),
        "referrals": existing_user.get("referrals", []),
        "invited_by": existing_user.get("invited_by", ""),
        "rank": existing_user.get("rank", "Bronze"),
        "rank_bonus": existing_user.get("rank_bonus", 1),
        "daily_bonus": existing_user.get("daily_bonus", 1),
        "reputation": existing_user.get("reputation", "Trusted Sardine")

    }

    users[data.user_id]["rank"] = calculate_rank(users[data.user_id])

    users[data.user_id]["rank_bonus"] = get_rank_bonus(
        users[data.user_id]["rank"]
    )

    streak = users[data.user_id].get("streak", 1)

    daily_bonus = 1 + min(streak * 0.02, 1)

    users[data.user_id]["daily_bonus"] = round(daily_bonus, 2)
    users[data.user_id]["reputation"] = calculate_reputation(users[data.user_id])

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    return {
        "success": True,
        "message": "User saved"
    }

@app.get("/get-user/{user_id}")
def get_user(user_id: str):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    if user_id not in users:
        return {"exists": False}

    return {
        "exists": True,
        "data": users[user_id],
        "referral_count": len(users[user_id].get("referrals", []))
    }

@app.post("/create-payment")
def create_payment(data: PaymentData):
    with open(PAYMENTS_FILE, "r") as f:
        payments = json.load(f)

    payment_id = f"{data.user_id}_{data.plan_key}_{int(datetime.now().timestamp())}"

    payments[payment_id] = {
        "payment_id": payment_id,
        "user_id": data.user_id,
        "plan_key": data.plan_key,
        "plan_name": data.plan_name,
        "amount": data.amount,
        "reward_per_24h": data.reward_per_24h,
        "network": data.network,
        "address": data.address,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }

    with open(PAYMENTS_FILE, "w") as f:
        json.dump(payments, f, indent=4)

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    user = users.get(data.user_id, {})
    user["pending_vip_plan"] = data.plan_key
    user["active_vip_plan"] = user.get("active_vip_plan", "free")
    users[data.user_id] = user

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    return {"success": True, "payment_id": payment_id}

@app.post("/claim-mission")
def claim_mission(data: MissionData):

    today = datetime.now().strftime("%Y-%m-%d")
    mission_id = f"{data.user_id}_{data.mission_type}_{today}"

    with open(MISSIONS_FILE, "r") as f:
        missions = json.load(f)

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    if mission_id in missions:
        return {
            "success": False,
            "message": "Mission already claimed today"
        }

    missions[mission_id] = {
        "user_id": data.user_id,
        "mission_type": data.mission_type,
        "reward": data.reward,
        "date": today,
        "claimed_at": datetime.now().isoformat()
    }

    if data.user_id in users:
        users[data.user_id]["balance"] = users[data.user_id].get("balance", 0) + data.reward
        users[data.user_id]["tap_points"] = users[data.user_id].get("tap_points", 0) + int(data.reward)

    with open(MISSIONS_FILE, "w") as f:
        json.dump(missions, f, indent=4)

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    return {
        "success": True,
        "message": "Mission claimed",
        "reward": data.reward
    }

@app.post("/save-alert")
def save_alert(data: AlertData):

    with open(ALERTS_FILE, "r") as f:
        alerts = json.load(f)

    alert_id = f"{data.user_id}_{data.asset}_{data.alert_type}"

    alerts[alert_id] = {
        "user_id": data.user_id,
        "asset": data.asset,
        "alert_type": data.alert_type
    }

    with open(ALERTS_FILE, "w") as f:
        json.dump(alerts, f, indent=4)

    return {
        "success": True,
        "message": "Alert saved"
    }

@app.post("/save-referral")
def save_referral(data: ReferralData):

    with open(REFERRALS_FILE, "r") as f:
        referrals = json.load(f)

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    if data.user_id in referrals:
        return {
            "success": False,
            "message": "Referral already registered"
        }

    referrals[data.user_id] = {
        "user_id": data.user_id,
        "username": data.username,
        "first_name": data.first_name,
        "referral_code": data.referral_code,
        "inviter_id": data.inviter_id,
        "reward": 1200,
        "created_at": datetime.now().isoformat()
    }

    if data.inviter_id and data.inviter_id in users:
        users[data.inviter_id]["balance"] = users[data.inviter_id].get("balance", 0) + 1200
        users[data.inviter_id]["referral_count"] = users[data.inviter_id].get("referral_count", 0) + 1

        if "referrals" not in users[data.inviter_id]:
            users[data.inviter_id]["referrals"] = []

        users[data.inviter_id]["referrals"].append({
            "user_id": data.user_id,
            "username": data.username
        })

    with open(REFERRALS_FILE, "w") as f:
        json.dump(referrals, f, indent=4)

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    return {
        "success": True,
        "message": "Referral saved and reward applied"
    }

@app.get("/referrals")
def list_referrals():

    with open(REFERRALS_FILE, "r") as f:
        referrals = json.load(f)

    return referrals

@app.get("/payments")
def list_payments():
    with open(PAYMENTS_FILE, "r") as f:
        payments = json.load(f)
    return payments

class ApprovePaymentData(BaseModel):
    user_id: str
    plan_key: str

@app.post("/approve-payment")
def approve_payment(data: ApprovePaymentData):
    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    with open(PAYMENTS_FILE, "r") as f:
        payments = json.load(f)

    if data.user_id not in users:
        users[data.user_id] = {
            "user_id": data.user_id,
            "username": "Sardine",
            "balance": 0,
            "tap_points": 0,
            "level": 1,
            "streak": 1,
            "active_vip_plan": "free",
            "pending_vip_plan": "",
            "vip_expires_at": ""
        }

    users[data.user_id]["active_vip_plan"] = data.plan_key
    users[data.user_id]["pending_vip_plan"] = ""
    users[data.user_id]["vip_expires_at"] = (
        datetime.now() + timedelta(days=30)
    ).isoformat()
    users[data.user_id]["vip_reward_per_24h"] = 1

    for payment_id, payment in payments.items():
        if payment.get("user_id") == data.user_id and payment.get("plan_key") == data.plan_key:
            payments[payment_id]["status"] = "approved"
            payments[payment_id]["approved_at"] = datetime.now().isoformat()

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    with open(PAYMENTS_FILE, "w") as f:
        json.dump(payments, f, indent=4)

    return {
        "success": True,
        "message": "Payment approved and VIP activated",
        "user_id": data.user_id,
        "plan_key": data.plan_key,
        "vip_expires_at": users[data.user_id]["vip_expires_at"]
    }

def calculate_rank(user):

    referrals = user.get("referral_count", 0)
    level = user.get("level", 1)

    if referrals >= 100 or level >= 50:
        return "Magnata"

    elif referrals >= 50 or level >= 30:
        return "Diamond"

    elif referrals >= 20 or level >= 20:
        return "Gold"

    elif referrals >= 5 or level >= 10:
        return "Silver"

    return "Bronze"

def get_rank_bonus(rank):

    bonuses = {
        "Bronze": 1,
        "Silver": 1.2,
        "Gold": 1.5,
        "Diamond": 2,
        "Magnata": 3
    }

    return bonuses.get(rank, 1)

def calculate_reputation(user):

    referrals = user.get("referral_count", 0)
    streak = user.get("streak", 1)
    level = user.get("level", 1)
    tap_points = user.get("tap_points", 0)

    score = 0
    score += referrals * 50
    score += streak * 10
    score += level * 20
    score += tap_points // 10000

    if score >= 5000:
        return "Ocean Legend"

    if score >= 2500:
        return "Ocean Guardian"

    if score >= 1000:
        return "Whale Hunter"

    if score >= 400:
        return "Ocean Explorer"

    return "Trusted Sardine"

@app.get("/leaderboard")
def leaderboard():

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    ranking = []

    for user_id, data in users.items():
        ranking.append({
            "user_id": user_id,
            "username": data.get("username", "Sardine"),
            "balance": data.get("balance", 0),
            "tap_points": data.get("tap_points", 0),
            "level": data.get("level", 1),
            "streak": data.get("streak", 1),
            "active_vip_plan": data.get("active_vip_plan", "free"),
            "referral_count": data.get("referral_count", 0),
            "rank_bonus": data.get("rank_bonus", 1),
            "rank": data.get("rank", "Bronze"),
            "reputation": data.get("reputation", "Trusted Sardine"),
        })

    ranking.sort(
        key=lambda x: (
            x["referral_count"],
            x["level"],
            x["tap_points"],
            x["balance"]
        ),
        reverse=True
    )

    return {
        "success": True,
        "leaderboard": ranking[:50]
    }

@app.get("/admin-summary")
def admin_summary():
    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    with open(PAYMENTS_FILE, "r") as f:
        payments = json.load(f)

    return {"users": users, "payments": payments}


@app.post("/approve-payment/{payment_id}")
def approve_payment_by_id(payment_id: str):
    with open(PAYMENTS_FILE, "r") as f:
        payments = json.load(f)

    if payment_id not in payments:
        return {"success": False, "message": "Payment not found"}

    payment = payments[payment_id]
    payment["status"] = "approved"
    payment["approved_at"] = datetime.now().isoformat()
    payments[payment_id] = payment

    with open(PAYMENTS_FILE, "w") as f:
        json.dump(payments, f, indent=4)

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    user_id = payment["user_id"]
    user = users.get(user_id, {})

    user["active_vip_plan"] = payment["plan_key"]
    user["pending_vip_plan"] = ""
    user["vip_expires_at"] = (
    datetime.now() + timedelta(days=30)
    ).isoformat()

    users[user_id] = user

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    return {
        "success": True,
        "message": "Payment approved and VIP activated",
        "user_id": user_id,
        "active_vip_plan": payment["plan_key"]
    }


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")