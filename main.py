import discord
from discord.ext import commands
import sqlite3
import datetime
import re
import os

# ---------- Config Bot ----------
TOKEN = os.environ.get('DISCORD_TOKEN')  # Metti il token nelle Shared Variables di Railway
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

# ---------- Database SQLite ----------
conn = sqlite3.connect('fortgreely.db')
c = conn.cursor()

# Tabella per messaggi dai server esterni
c.execute('''
CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    discord_id TEXT,
    username TEXT,
    license TEXT,
    reason TEXT,
    duration TEXT,
    staff TEXT,
    server TEXT,
    channel TEXT,
    timestamp TEXT
)
''')

# Tabella per log FiveGuard
c.execute('''
CREATE TABLE IF NOT EXISTS fiveguard_logs (
    log_id TEXT PRIMARY KEY,
    discord_id TEXT,
    name TEXT,
    violation TEXT,
    info TEXT,
    steam TEXT,
    license TEXT,
    live TEXT,
    xbox TEXT,
    ip TEXT,
    timestamp TEXT
)
''')
conn.commit()

# ---------- Comandi ----------

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# -------- Paste blocco messaggi server esterni ----------
@bot.command()
async def paste_db(ctx, *, blocco):
    timestamp = datetime.datetime.utcnow().isoformat()
    lines = blocco.split('\n')
    buffer = {}
    count = 0

    for line in lines:
        line = line.strip()
        if line.startswith("Player:"):
            buffer['username'] = line.replace("Player:", "").strip()
        elif line.startswith("Discord:"):
            match = re.search(r'(\d{17,19})', line)
            buffer['discord_id'] = match.group(1) if match else None
        elif line.lower().startswith("license:"):
            buffer['license'] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("motivazione:") or line.lower().startswith("motivo:"):
            buffer['reason'] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("scadenza:") or line.lower().startswith("durata:"):
            buffer['duration'] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("staff:"):
            buffer['staff'] = line.split(":", 1)[1].strip()

        # Inserisci nel DB se discord_id e username sono presenti
        if 'discord_id' in buffer and 'username' in buffer:
            message_id = f"{buffer['discord_id']}_{timestamp}_{count}"
            c.execute('''
            INSERT OR REPLACE INTO messages
            (message_id, discord_id, username, license, reason, duration, staff, server, channel, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id,
                buffer.get('discord_id'),
                buffer.get('username'),
                buffer.get('license'),
                buffer.get('reason'),
                buffer.get('duration'),
                buffer.get('staff'),
                ctx.guild.name,
                ctx.channel.name,
                timestamp
            ))
            conn.commit()
            buffer = {}
            count += 1

    await ctx.send(f"{count} messaggi aggiunti al database.")

# -------- Paste blocco log FiveGuard ----------
@bot.command()
async def paste_fiveguard(ctx, *, blocco):
    timestamp = datetime.datetime.utcnow().isoformat()
    lines = blocco.split('\n')
    buffer = {}
    count = 0

    for line in lines:
        line = line.strip()
        if line.startswith("Name"):
            buffer['name'] = line.split(":",1)[1].strip()
        elif line.startswith("Discord"):
            match = re.search(r'(\d{17,19})', line)
            buffer['discord_id'] = match.group(1) if match else None
        elif line.startswith("Violation"):
            buffer['violation'] = line.split(":",1)[1].strip()
        elif line.startswith("Additional Info"):
            buffer['info'] = line.split(":",1)[1].strip()
        elif line.startswith("Steam"):
            buffer['steam'] = line.split(":",1)[1].strip()
        elif line.startswith("License"):
            buffer['license'] = line.split(":",1)[1].strip()
        elif line.startswith("Live"):
            buffer['live'] = line.split(":",1)[1].strip()
        elif line.startswith("Xbox"):
            buffer['xbox'] = line.split(":",1)[1].strip()
        elif line.startswith("IP Address"):
            buffer['ip'] = line.split(":",1)[1].strip()

        if 'discord_id' in buffer and buffer['discord_id']:
            log_id = f"{buffer['discord_id']}_{timestamp}_{count}"
            c.execute('''
            INSERT OR REPLACE INTO fiveguard_logs
            (log_id, discord_id, name, violation, info, steam, license, live, xbox, ip, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_id,
                buffer.get('discord_id'),
                buffer.get('name'),
                buffer.get('violation'),
                buffer.get('info'),
                buffer.get('steam'),
                buffer.get('license'),
                buffer.get('live'),
                buffer.get('xbox'),
                buffer.get('ip'),
                timestamp
            ))
            conn.commit()
            buffer = {}
            count += 1

    await ctx.send(f"{count} log FiveGuard aggiunti al database.")

# -------- Comando controlla ID ----------
@bot.command()
async def controlla(ctx, discord_id: str):
    report = f"Report per <@{discord_id}> ({discord_id}):\n\n"

    # Cerca messaggi esterni
    c.execute("SELECT * FROM messages WHERE discord_id=?", (discord_id,))
    rows = c.fetchall()
    if rows:
        for r in rows:
            line = f"- {r[4]} | Staff: {r[6]} | Server: {r[7]} | Channel: {r[8]}"
            report += line + "\n"
    else:
        report += "Nessun ban/warn registrato dai server esterni.\n"

    # Cerca log FiveGuard
    c.execute("SELECT * FROM fiveguard_logs WHERE discord_id=?", (discord_id,))
    logs = c.fetchall()
    if logs:
        report += "\nFiveGuard FLAG RoyalRP:\n"
        for log in logs:
            report += f"- Violation: {log[3]}\n"
            report += f"- Additional Info: {log[4]}\n"
            report += f"- Steam: {log[5]}\n"
            report += f"- License: {log[6]}\n"
            report += f"- Live: {log[7]}\n"
            report += f"- Xbox: {log[8]}\n"
            report += f"- IP Address: {log[9]}\n"
            report += "----------------------\n"

    await ctx.send(report or "Nessun dato trovato.")

# ---------- Avvio Bot ----------
bot.run(TOKEN)
