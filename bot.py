import os
import discord
from discord.ext import commands
import aiosqlite

# -----------------------------
# Configuration
# -----------------------------
# Put your bot token in an environment variable called DISCORD_TOKEN
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = "!"
DB_FILE = "database.db"

# Minimal intents: add message_content so the bot can read commands
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)


# -----------------------------
# Database setup
# -----------------------------
async def init_db():
    """Create the builds table if it doesn't exist."""
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS builds (
                champion TEXT,
                build TEXT,
                author TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


# -----------------------------
# Events
# -----------------------------
@bot.event
async def on_ready():
    await init_db()
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


# -----------------------------
# Commands
# -----------------------------
@bot.command(name="add")
async def add_build(ctx, champion: str, *, build: str):
    """
    Store a build for a champion.
    Usage: !add ashe Kraken Slayer -> Runaan's -> IE
    """
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "INSERT INTO builds (champion, build, author) VALUES (?, ?, ?)",
            (champion.lower(), build, str(ctx.author))
        )
        await db.commit()

    await ctx.send(f"✅ Build for **{champion.title()}** saved!")


@bot.command(name="get")
async def get_build(ctx, champion: str):
    """
    Retrieve builds for a champion.
    Usage: !get ashe
    """
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute(
            "SELECT build, author FROM builds WHERE champion = ?",
            (champion.lower(),)
        ) as cursor:
            rows = await cursor.fetchall()

    if not rows:
        await ctx.send(f"❄️ No builds found for **{champion.title()}** yet.")
        return

    # Format the response nicely
    response = "\n".join([f"- {build} *(by {author})*" for build, author in rows])
    await ctx.send(f"**Builds for {champion.title()}**:\n{response}")


@bot.command(name="delete")
async def delete_build(ctx, champion: str):
    """
    Delete all builds for a champion that you submitted.
    Usage: !delete ashe
    """
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute(
            "DELETE FROM builds WHERE champion = ? AND author = ?",
            (champion.lower(), str(ctx.author))
        )
        await db.commit()

    await ctx.send(f"🗑️ Deleted your builds for **{champion.title()}** (if any).")


# -----------------------------
# Run the bot
# -----------------------------
if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("Missing DISCORD_TOKEN environment variable.")
    bot.run(TOKEN)
