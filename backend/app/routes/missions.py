from fastapi import APIRouter

router = APIRouter()

@router.get("/missions")
async def get_missions():
    return {
        "missions": [
            {
                "title": "Join Telegram",
                "reward": 500,
                "completed": False
            },
            {
                "title": "Follow on X",
                "reward": 500,
                "completed": False
            },
            {
                "title": "Invite Friends",
                "reward": 1000,
                "completed": False
            }
        ]
    }