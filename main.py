import discord
from discord.ext import commands, tasks
import os
import asyncio

# -----------------------------
# Configurazione base del bot
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True  # Serve per leggere contenuti dei messaggi (solo legale se nel server centrale)
bot = commands.Bot(command_prefix='!', intents=intents)

# Coda utenti da verificare
user_queue = asyncio.Queue()

# -----------------------------
# CONFIGURAZIONE UTENTE
# -----------------------------
# Inserisci qui l'ID del canale del server centrale dove inviare i report
REPORT_CHANNEL_ID = 1411860980862029934  

# Livelli di sospetto supportati
LEVELS = ["Pulito", "Sospetto Medio", "Sospetto Alto", "Confermato"]

# -----------------------------
# EVENTI BASE
# -----------------------------
@bot.event
async def on_ready():
    print(f'{bot.user} è online!')
    process_queue.start()  # Avvia il task per processare la coda automatica

# -----------------------------
# FUNZIONI DI SUPPORTO
# -----------------------------
async def send_report(user_id, username, level, messages=None):
    """Invia un report embed nel canale centrale"""
    channel = bot.get_channel(REPORT_CHANNEL_ID)
    if not channel:
        print("Canale report non trovato")
        return

    embed = discord.Embed(title="Report Utente", color=0xff0000)
    embed.add_field(name="Utente", value=username, inline=True)
    embed.add_field(name="ID", value=str(user_id), inline=True)
    embed.add_field(name="Livello", value=level, inline=True)

    if messages:
        embed.add_field(name="Messaggi rilevanti", value="\n".join(messages), inline=False)

    if level == "Confermato":
        await channel.send("@everyone", embed=embed)
    else:
        await channel.send(embed=embed)

# -----------------------------
# TASK PER CODA AUTOMATICA
# -----------------------------
@tasks.loop(seconds=10)
async def process_queue():
    """Processa utenti dalla coda automatica"""
    while not user_queue.empty():
        user = await user_queue.get()
        await send_report(
            user_id=user["id"],
            username=user["username"],
            level=user["level"],
            messages=user.get("messages")
        )
        await asyncio.sleep(1)  # Pausa per non spam

# -----------------------------
# COMANDI DEL BOT
# -----------------------------
@bot.command()
async def controlla(ctx, user_id: int, username: str, level: str):
    """
    Verifica manuale di un utente.
    Uso: /controlla <ID> <username> <Livello>
    """
    if level not in LEVELS:
        await ctx.send(f"Livello non valido. Usa: {', '.join(LEVELS)}")
        return

    await send_report(user_id=user_id, username=username, level=level, messages=[])
    await ctx.send(f"Report generato per {username} (ID: {user_id})")

@bot.command()
async def add_queue(ctx, user_id: int, username: str, level: str):
    """
    Aggiunge un utente alla coda automatica.
    Uso: !add_queue <ID> <username> <Livello>
    """
    if level not in LEVELS:
        await ctx.send(f"Livello non valido. Usa: {', '.join(LEVELS)}")
        return

    await user_queue.put({"id": user_id, "username": username, "level": level, "messages": []})
    await ctx.send(f"Utente {username} aggiunto alla coda automatica")

# -----------------------------
# AVVIO BOT
# -----------------------------
TOKEN = os.environ['DISCORD_TOKEN']  # Usa variabile d'ambiente
bot.run(TOKEN)
