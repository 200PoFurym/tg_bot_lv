from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from models import User
from search import recommend_users

async def recommend_users_periodically():
    try:
        users = await User.all()
        for user in users:
            await recommend_users(user)
    except Exception as e:
        print(f"Error: {e}")

async def reset_daily_views():
    now = datetime.now(timezone.utc)
    await User.all().update(daily_profile_views=100, last_view_reset=now)

async def start_scheduler():
    scheduler = AsyncIOScheduler()
    reset_trigger = CronTrigger(hour=0, minute=0, second=0)
    recommend_trigger = CronTrigger(hour='*/4')
    scheduler.add_job(reset_daily_views, reset_trigger)
    scheduler.add_job(recommend_users_periodically, recommend_trigger)
    scheduler.start()
