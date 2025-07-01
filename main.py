import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
db = TinyDB("db.json")
User = Query()
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.command(name="checkin")
async def checkin(ctx):
    user_id = str(ctx.author.id)
    today = datetime.utcnow().date()

    user_data = db.get(User.id == user_id)

    if user_data:
        last_checkin = datetime.strptime(user_data["last_checkin"], "%Y-%m-%d").date()
        streak = user_data["streak"]

        if today == last_checkin:
            await ctx.send(f"✅ You already checked in today, {ctx.author.mention}! Your current streak is {streak} 🔥")
            return
        elif today == last_checkin + timedelta(days=1):
            streak += 1
        else:
            streak = 1  # Reset streak if not consecutive

        db.update({"last_checkin": str(today), "streak": streak}, User.id == user_id)
    else:
        db.insert({"id": user_id, "last_checkin": str(today), "streak": 1})
        streak = 1

    await ctx.send(f"🧠 Check-in recorded for {ctx.author.mention}! You're on a **{streak}-day streak**! 💪")
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz

scheduler = AsyncIOScheduler()

@bot.event
async def on_ready():
    print(f"✅ Bot connected as {bot.user}")

    channel_id = YOUR_CHANNEL_ID  # 1389469819472056345
    eastern = pytz.timezone('US/Eastern')

    # Schedule check-in post every weekday at 9:15 AM ET
    scheduler.add_job(
        send_checkin_reminder,
        'cron',
        day_of_week='mon-fri',
        hour=9,
        minute=15,
        timezone=eastern,
        args=[channel_id]
    )

    scheduler.start()

async def send_checkin_reminder(channel_id):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send("🛎️ Pre-market check-in time! Reply with your plan. Stay disciplined!")
        
@bot.command(name="streak")
async def streak(ctx):
    user_id = str(ctx.author.id)
    user_data = db.get(User.id == user_id)

    if user_data:
        current_streak = user_data["streak"]
        await ctx.send(f"📊 {ctx.author.mention}, your current streak is **{current_streak}** days! 🔥")
    else:
        await ctx.send(f"{ctx.author.mention}, you haven't started a streak yet. Use `!checkin` to begin!")        
bot.run(TOKEN)
