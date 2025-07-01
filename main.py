import os
import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = nextcord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

@bot.slash_command(name="checkin", description="Submit your pre-market trading plan")
async def checkin(interaction: nextcord.Interaction):
    await interaction.response.send_message("Thanks for checking in. Stay disciplined!")

bot.run(TOKEN)
