import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
from discord.ext import tasks
from datetime import time, timezone
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
db = TinyDB("db.json")
User = Query()
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@tasks.loop(time=time(hour=13, minute=15, tzinfo=timezone.utc))  # 9:15 AM ET
async def send_reflection_prompt():
    for guild in bot.guilds:
        for member in guild.members:
            if not member.bot:
                try:
                    dm = await member.create_dm()
                    await dm.send("🧠 What setups are you focusing on today?")
                    await dm.send("💵 What is your max dollar risk for the day?")
                    await dm.send("📝 What is the max number of trades you'll take?")
                    await dm.send("🎯 What is your discipline focus today (e.g., no revenge trades)?")
                except Exception as e:
                    print(f"Failed to DM {member}: {e}")




@bot.event
async def on_ready():
    send_reflection_prompt.start()
    print(f"📗 Bot connected as {bot.user}")


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

@bot.command(name="myplan")
async def myplan(ctx):
    user_id = str(ctx.author.id)
    today = datetime.now().strftime("%Y-%m-%d")

    # Find the most recent plan for today
    plans = db.search((User.id == user_id) & (User.date == today))
    
    if not plans:
        await ctx.send(f"{ctx.author.mention}, you haven’t submitted a trade plan today. Use `!tradeplan` to start.")
        return

    plan = plans[-1]["plan"]  # Get the most recent one if multiples

    summary = "\n".join([
        f"**{key}:** {value}"
        for key, value in plan.items()
    ])
    await ctx.send(f"📋 **Your Trading Plan for Today:**\n{summary}")

@tasks.loop(seconds=60)  # For testing — runs every 60 seconds
async def send_reflection_prompt():
    now = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")

    # Skip weekends
    if now.weekday() >= 5:
        return

    # Only send at a specific minute (adjust as needed)
    if now.minute % 2 == 0:  # Sends every 2 minutes (for testing)
        sent = 0
        plans_today = db.search(User.date == today)
        for record in plans_today:
            user = await bot.fetch_user(int(record["id"]))
            try:
                await user.send(
                    "🕓 Market's closed!\nDid you follow your plan today?\n"
                    "What did you do well, and what could you improve?"
                )
                sent += 1
            except:
                pass

        print(f"✅ Sent {sent} reflection prompts.")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        user_id = str(message.author.id)
        today = datetime.now().strftime("%Y-%m-%d")

        # Check if user submitted a plan today
        matches = db.search((User.id == user_id) & (User.date == today))
        if matches and "reflection" not in matches[-1]:
            # Save the reflection
            updated = matches[-1]
            updated["reflection"] = message.content

            db.remove((User.id == user_id) & (User.date == today))
            db.insert(updated)

            await message.channel.send("✅ Reflection saved. Good job staying accountable.")

@bot.command(name="testreflection")
async def test_reflection(ctx):
    await send_reflection_prompt()
    await ctx.send("🧠 Reflection questions sent to all members.")


bot.run(TOKEN)
