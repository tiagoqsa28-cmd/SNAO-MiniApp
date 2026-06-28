def get_user_level(points: int):
    if points >= 5000:
        return "Diamond"
    elif points >= 2000:
        return "Gold"
    elif points >= 500:
        return "Silver"
    else:
        return "Bronze"


def get_multiplier_by_vip_level(vip_level: str | None):
    if not vip_level:
        return 1.00

    level = vip_level.lower()

    if level == "diamond":
        return 1.50
    elif level == "gold":
        return 1.25
    elif level == "silver":
        return 1.10
    else:
        return 1.00


def get_vip_status(points: int):
    level = get_user_level(points)

    if level == "Diamond":
        return {"vip": True, "vip_name": "VIP Diamond", "multiplier": 1.50}

    if level == "Gold":
        return {"vip": True, "vip_name": "VIP Gold", "multiplier": 1.25}

    if level == "Silver":
        return {"vip": True, "vip_name": "VIP Silver", "multiplier": 1.10}

    return {"vip": False, "vip_name": "Standard", "multiplier": 1.00}