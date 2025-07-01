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
intents.members = True
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

@bot.command(name="leaderboard")
async def leaderboard(ctx):
    top_users = db.all()
    if not top_users:
        await ctx.send("📭 No check-ins yet! Use `!checkin` to start the leaderboard.")
        return

    # Sort by streak descending
    sorted_users = sorted(top_users, key=lambda x: x["streak"], reverse=True)[:5]

    leaderboard_text = "**🏆 Top 5 Streaks 🏆**\n"
    for i, user in enumerate(sorted_users, start=1):
        try:
            member = await ctx.guild.fetch_member(int(user["id"]))
            name = member.mention
        except:
            name = f"User ID {user['id']}"
        leaderboard_text += f"{i}. {name} — {user['streak']} days\n"

    await ctx.send(leaderboard_text)

@bot.command(name="tradeplan")
async def tradeplan(ctx):
    user_id = str(ctx.author.id)

    # Step 1: Start DM Session
    try:
        dm_channel = await ctx.author.create_dm()
        await dm_channel.send("📝 Let's set your trading plan for today. I'll ask you 4 questions.")
    except:
        await ctx.send(f"❌ {ctx.author.mention}, I couldn't DM you. Please check your DM settings.")
        return

    # Step 2: Ask Questions in Sequence
    questions = [
        "What setup(s) are you focused on today?",
        "What’s your max $ risk for the day?",
        "What’s your max number of trades?",
        "What’s your discipline focus for the day? (e.g., no revenge trades, no FOMO)"
    ]

    responses = {}

    # Function to handle replies
    def check_reply(message):
        return message.author == ctx.author and isinstance(message.channel, discord.DMChannel)

    for i, question in enumerate(questions, start=1):
        await dm_channel.send(f"Q{i}: {question}")
        try:
            reply = await bot.wait_for("message", check=check_reply, timeout=120)
            responses[f"Q{i}"] = reply.content
        except asyncio.TimeoutError:
            await dm_channel.send("❌ You took too long to reply. Please type `!tradeplan` to start again.")
            return

    # Step 3: Confirm and Save Responses
    await dm_channel.send("✅ Got it! Here's your plan for today:")
    summary = "\n".join([f"**{key}:** {value}" for key, value in responses.items()])
    await dm_channel.send(summary)

    # Save to the database
    db.insert({
        "id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "plan": responses
    })
    await dm_channel.send("Your plan has been saved. Stay disciplined! 🔥")
bot.run(TOKEN)
