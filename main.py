import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from datetime import datetime, timedelta
from discord.ext import tasks
from datetime import time, timezone
import random
from datetime import datetime
import pytz
from discord.ext import tasks
from tinydb import Query
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
db = TinyDB("db.json")
User = Query()
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
User = Query()

from datetime import time, timezone
from discord.ext import tasks

@tasks.loop(time=time(hour=13, minute=15, tzinfo=timezone.utc))  # 9:15 AM ET
async def send_reflection_prompt():
    print("🔁 Task started: attempting to send reflection prompts.")
    for guild in bot.guilds:
        print(f"📡 Checking guild: {guild.name} ({guild.id})")
        for member in guild.members:
            print(f"👤 Found member: {member.name} ({member.id}) | Bot: {member.bot}")
            if not member.bot:
                try:
                    dm = await member.create_dm()
                    print(f"📬 DM created for {member.name}")
                    await dm.send("🧠 What setups are you focusing on today?")
                    await dm.send("💵 What is your max dollar risk for the day?")
                    await dm.send("📝 What is the max number of trades you'll take?")
                    await dm.send("🎯 What is your discipline focus today (e.g., no revenge trades)?")
                    print(f"✅ Sent prompts to {member.name}")
                except Exception as e:
                    print(f"❌ Failed to DM {member.name}: {e}")


@bot.event
async def on_ready():
    send_reflection_prompt.start()
    print(f"✅ Bot connected as {bot.user}")


@bot.command(name="checkin")
async def checkin(ctx):
    user_id = str(ctx.author.id)
    today = datetime.utcnow().date()

    user_data = db.get(User.id == user_id)

    if user_data:
        last_checkin = datetime.strptime(user_data.get("last_checkin"), "%Y-%m-%d").date()
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
    run_pairings.start()
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
    sorted_users = sorted(top_users, key=lambda x: x.get("streak", 0), reverse=True)[:5]

    leaderboard_text = "**🏆 Top 5 Streaks 🏆**\n"
    for i, user in enumerate(sorted_users, start=1):
        try:
            member = await ctx.guild.fetch_member(int(user["id"]))
            name = member.mention
        except:
            name = f"User ID {user['id']}"
        streak = user.get("streak", 0)
        leaderboard_text += f"{i}. {name} – {streak} days\n"


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
                from datetime import datetime
    
                dm = await user.create_dm()

                await dm.send("📋 Let’s reflect on your day. Starting with your morning trade plan...")

                await dm.send("1️⃣ Did you stick to the setups you planned to focus on?")
                q1 = await bot.wait_for('message', check=lambda m: m.author.id == user.id and isinstance(m.channel, discord.DMChannel), timeout=300)

                await dm.send("2️⃣ Did you stay within your max dollar risk for the day?")
                q2 = await bot.wait_for('message', check=lambda m: m.author.id == user.id and isinstance(m.channel, discord.DMChannel), timeout=300)

                await dm.send("3️⃣ Did you follow your max number of trades?")
                q3 = await bot.wait_for('message', check=lambda m: m.author.id == user.id and isinstance(m.channel, discord.DMChannel), timeout=300)

                await dm.send("4️⃣ Did you stick to your discipline focus (e.g., no revenge trades, no FOMO)?")
                q4 = await bot.wait_for('message', check=lambda m: m.author.id == user.id and isinstance(m.channel, discord.DMChannel), timeout=300)


                await dm.send("🔁 What’s one thing you’ll improve tomorrow?")
                q5 = await bot.wait_for('message', check=lambda m: m.author.id == user.id and isinstance(m.channel, discord.DMChannel), timeout=300)

                await dm.send("✅ Thanks for completing your end-of-day reflection. Your discipline is your edge.")

                db.insert({
                        "type": "reflection",
                        "user_id": str(user.id),
                        "date": datetime.utcnow().strftime("%Y-%m-%d"),
                        "answers": {
                        "followed_setups": q1.content,
                        "stayed_in_risk": q2.content,
                        "respected_trade_limit": q3.content,
                        "stayed_disciplined": q4.content,
                        "improvement_goal": q5.content
                    }
                })
                print(f"✅ Reflection saved for {user.name}")  # ✅ NOW it's inside the try block

            except Exception as e:
                print(f"❌ Failed reflection for {user.name}: {e}")



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



@bot.command()
async def reflectionpm(ctx):
    user = ctx.author
    now = datetime.utcnow()
    today = now.strftime("%Y-%m-%d")

    try:
        dm = await user.create_dm()
        await dm.send("📅 Let’s reflect on your day. Starting with your morning trade plan...")

        await dm.send("🧠1 Did you stick to the setups you planned to focus on?")
        q1 = await bot.wait_for('message', check=lambda m: m.author.id == user.id and isinstance(m.channel, discord.DMChannel), timeout=300)

        await dm.send("💵2 Did you stay within your max dollar risk for the day?")
        q2 = await bot.wait_for('message', check=lambda m: m.author.id == user.id and isinstance(m.channel, discord.DMChannel), timeout=300)

        await dm.send("📊3 Did you follow your max number of trades?")
        q3 = await bot.wait_for('message', check=lambda m: m.author.id == user.id and isinstance(m.channel, discord.DMChannel), timeout=300)

        await dm.send("🎯4 Did you stick to your discipline focus (e.g., no revenge trades, no FOMO)?")
        q4 = await bot.wait_for('message', check=lambda m: m.author.id == user.id and isinstance(m.channel, discord.DMChannel), timeout=300)

        await dm.send("🔁5 What’s one thing you’ll improve tomorrow?")
        q5 = await bot.wait_for('message', check=lambda m: m.author.id == user.id and isinstance(m.channel, discord.DMChannel), timeout=300)

        await dm.send("✅ Thanks for completing your end-of-day reflection. Your discipline is your edge.")

        db.insert({
            "type": "reflection",
            "user_id": str(user.id),
            "date": today,
            "answers": {
                "followed_setups": q1.content,
                "stayed_in_risk": q2.content,
                "respected_trade_limit": q3.content,
                "stayed_disciplined": q4.content,
                "improvement_goal": q5.content
            }
        })

        print(f"✅ Reflection saved for {user.name}")

    except Exception as e:
        print(f"❌ Failed reflection for {user.name}: {e}")

from tinydb import Query

@bot.command(name="myreflections")
async def myreflections(ctx):
    user_id = str(ctx.author.id)
    Reflection = Query()  # Define the query object here

    reflections = db.search(
        (Reflection.type == "reflection") & (Reflection.user_id == user_id)
    )

    if not reflections:
        await ctx.send("🪞 You have no reflections saved yet.")
        return

    response = "**📜 Your Reflections:**\n\n"
    for reflection in reflections[-5:]:  # Show only the last 5 reflections
        date = reflection["date"]
        answers = reflection["answers"]
        response += f"🗓️ **{date}**\n"
        response += f"• Followed setups: {answers['followed_setups']}\n"
        response += f"• Stayed in risk: {answers['stayed_in_risk']}\n"
        response += f"• Trade limit: {answers['respected_trade_limit']}\n"
        response += f"• Disciplined: {answers['stayed_disciplined']}\n"
        response += f"• Goal: {answers['improvement_goal']}\n\n"

    await ctx.send(response)

@bot.command(name="pairme")
async def pairme(ctx):
    user_id = str(ctx.author.id)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    existing = db.search((User.type == "pairing_optin") & (User.user_id == user_id) & (User.date == today))
    if existing:
        await ctx.send(f"🟡 You’re already on today’s list, {ctx.author.mention}.")
        return

    db.insert({
        "type": "pairing_optin",
        "user_id": user_id,
        "date": today
    })
    await ctx.send(f"✅ You’ve been added to today’s pairing list, {ctx.author.mention}.")

@bot.command(name="testpairing")
async def testpairing(ctx):
    await pair_traders()
    await ctx.send("🔁 Test pairing triggered.")

@tasks.loop(minutes=1)
async def run_pairings():
    now = datetime.now(pytz.timezone("US/Eastern"))
    if now.hour == 9 and now.minute == 15 and now.weekday() < 5:
        await pair_traders()

async def pair_traders():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    optins = db.search((User.type == "pairing_optin") & (User.date == today))
    
    if len(optins) < 2:
        return

    random.shuffle(optins)
    pairs = [optins[i:i+2] for i in range(0, len(optins), 2)]

    for pair in pairs:
        if len(pair) == 2:
            user1 = await bot.fetch_user(int(pair[0]["user_id"]))
            user2 = await bot.fetch_user(int(pair[1]["user_id"]))

            msg = (
                f"👥 You’ve been paired for accountability today!\n"
                f"Check in and help each other stick to your trading plans. 💪"
            )
            await user1.send(f"{msg}\nYour partner: {user2.mention}")
            await user2.send(f"{msg}\nYour partner: {user1.mention}")
        else:
            user = await bot.fetch_user(int(pair[0]["user_id"]))
            await user.send("👤 No partner today (odd number of traders). Try again tomorrow!")

@bot.command(name="unpairme")
async def unpairme(ctx):
    user_id = str(ctx.author.id)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    removed = db.remove((User.type == "pairing_optin") & (User.user_id == user_id) & (User.date == today))
    
    if removed:
        await ctx.send(f"❌ You’ve been removed from today’s pairing list, {ctx.author.mention}.")
    else:
        await ctx.send(f"ℹ️ You weren’t on the pairing list for today, {ctx.author.mention}.")

@bot.command(name='mylog')
async def mylog(ctx):
    user_id = str(ctx.author.id)
    today = datetime.datetime.today().date().isoformat()

    if user_id not in user_data or today not in user_data[user_id]:
        await ctx.author.send("You haven't submitted a trade plan or reflection today.")
        return

    data = user_data[user_id][today]

    embed = discord.Embed(
        title=f"📊 Your Daily Trading Log — {today}",
        color=discord.Color.blue()
    )

    # ✅ Streak
    streak = user_data[user_id].get("streak", 0)
    embed.add_field(name="✅ Streak", value=f"{streak} days", inline=False)

    # 📝 Trade Plan
    plan = data.get("trade_plan", {})
    if plan:
        trade_plan_text = (
            f"**Setups:** {plan.get('setups', 'N/A')}\n"
            f"**Max $ Risk:** {plan.get('max_risk', 'N/A')}\n"
            f"**Max Trades:** {plan.get('max_trades', 'N/A')}\n"
            f"**Discipline Focus:** {plan.get('discipline_focus', 'N/A')}"
        )
        embed.add_field(name="📋 Trade Plan", value=trade_plan_text, inline=False)
    else:
        embed.add_field(name="📋 Trade Plan", value="Not submitted.", inline=False)

    # 🧠 Reflection
    reflection = data.get("reflection", {})
    if reflection:
        reflection_text = (
            f"**Followed Plan?** {reflection.get('followed_plan', 'N/A')}\n"
            f"**Lesson Learned:** {reflection.get('lesson', 'N/A')}"
        )
        embed.add_field(name="🧠 Reflection", value=reflection_text, inline=False)
    else:
        embed.add_field(name="🧠 Reflection", value="Not submitted.", inline=False)

    await ctx.author.send(embed=embed)
    await ctx.send("📬 Your log has been sent via DM.")


bot.run(TOKEN)
