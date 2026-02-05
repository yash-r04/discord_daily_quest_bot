import discord
import json
import random
import os
from discord.ext import commands, tasks
from datetime import datetime, date

# ---------- LOAD QUESTIONS ----------
with open("questions.json") as f:
    QUESTIONS = json.load(f)

# ---------- DISCORD SETUP ----------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- GLOBAL STATE ----------
current_question = None
current_answer = None
today = None

# user_id -> data
user_progress = {}
# example:
# {
#   "123": {
#     "attempted": True,
#     "solved": False,
#     "streak": 2
#   }
# }

# ---------- HELPERS ----------
def get_general_channel():
    return discord.utils.get(bot.get_all_channels(), name="general")

# ---------- BOT READY ----------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    daily_question.start()
    evening_reminder.start()
    weekly_report.start()

# ---------- DAILY QUESTION ----------
@tasks.loop(hours=24)
async def daily_question():
    global current_question, current_answer, today, user_progress

    q = random.choice(QUESTIONS)
    current_question = q
    current_answer = q["answer"]
    today = str(date.today())

    # Reset daily progress (keep streaks)
    for user in user_progress.values():
        user["attempted"] = False
        user["solved"] = False

    channel = get_general_channel()
    if channel:
        await channel.send(
            f"""📘 **Daily questttt – {q['topic']} ({q['year']})**

📝 {q['question']}

💬 **Send your answer as a DM to me**
🔁 Unlimited attempts allowed
"""
        )


# ---------- DM ANSWER HANDLER ----------
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Only accept DMs
    if not isinstance(message.channel, discord.DMChannel):
        return

    if not current_answer:
        await message.channel.send("❗ No active question right now.")
        return

    user_id = str(message.author.id)

    if user_id not in user_progress:
        user_progress[user_id] = {
            "attempted": False,
            "solved": False,
            "streak": 0
        }

    user = user_progress[user_id]
    user["attempted"] = True

    if user["solved"]:
        await message.channel.send(
            "✅Aryyyeee over achiever come tommoroww!"
        )
        return

    user_input = message.content.strip()

    if user_input == current_answer:
        user["solved"] = True
        user["streak"] += 1

        await message.channel.send(
            f"🎉 **Correct!**\n🔥 Current streak: {user['streak']} days"
        )
    else:
        await message.channel.send(
            "❌ Not correct. Try again!"
        )

# ---------- EVENING REMINDER ----------
@tasks.loop(hours=24)
async def evening_reminder():
    await bot.wait_until_ready()

    # Run at ~8 PM IST (adjust hosting start time)
    for user_id, data in user_progress.items():
        if not data["attempted"]:
            try:
                user = await bot.fetch_user(int(user_id))
                await user.send(
                    "⏰ **Reminder:** You haven’t attempted today’s side quest yet!"
                )
            except:
                pass

# ---------- DAILY SUMMARY ----------
@tasks.loop(hours=24)
async def daily_summary():
    await bot.wait_until_ready()
    channel = get_general_channel()
    if not channel:
        return

    msg = "📊 **Side Quest**\n\n"
    for uid, data in user_progress.items():
        user = await bot.fetch_user(int(uid))
        status = "✅ Solved" if data["solved"] else "❌ Not Solved"
        msg += f"{user.name}: {status}\n"

    await channel.send(msg)

# ---------- WEEKLY REPORT ----------
@tasks.loop(hours=24)
async def weekly_report():
    await bot.wait_until_ready()

    if datetime.today().weekday() != 6:  # Sunday
        return

    channel = get_general_channel()
    if not channel:
        return

    msg = "📅 **Weekly Stat**\n\n"
    for uid, data in user_progress.items():
        user = await bot.fetch_user(int(uid))
        msg += f"🔥 {user.name}: {data['streak']} day streak\n"

    await channel.send(msg)

token = os.getenv("BOT_TOKEN") 
