import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.command(name="checkin")
async def checkin(ctx):
    await ctx.send("✅ Please submit your pre-market trading plan here!")

bot.run(TOKEN)
