import asyncio

import discord
from discord.ext import commands

from config import DISCORD_TOKEN, POKETWO_BOT_ID, HELPER_BOT_IDS
from services.parser import extract_pokemon_name
from services.queue import CatchQueue


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)

catch_queue = CatchQueue()

is_paused = False
is_afk = False


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user}.")


@bot.command()
async def pause(ctx: commands.Context) -> None:
    global is_paused

    is_paused = True
    await ctx.send("Paused.")


@bot.command()
async def resume(ctx: commands.Context) -> None:
    global is_paused

    is_paused = False
    await ctx.send("Resumed.")


@bot.event
async def on_message(message: discord.Message) -> None:
    global is_paused
    global is_afk

    # Ignore our own bot messages.
    if message.author.id == bot.user.id:
        return

    # Process commands.
    await bot.process_commands(message)

    # Safety conditions.
    if (
        message.author.id == POKETWO_BOT_ID
        and "Please tell us you're human!" in message.content
        and str(bot.user.id) in message.content
    ):
        is_paused = True
        print("CAPTCHA-related message detected. Paused.")
        return

    if (
        message.author.id == POKETWO_BOT_ID
        and "These colors seem unusual..." in message.content
        and str(bot.user.id) in message.content
    ):
        is_paused = True
        print("Shiny-related message detected. Paused.")
        return

    if is_paused or is_afk:
        return

    # Helper-bot notification.
    if (
        message.author.id in HELPER_BOT_IDS
        and str(bot.user.id) in message.content
    ):
        pokemon_name = extract_pokemon_name(message.content)

        if not pokemon_name:
            return

        print(f"Received notification for: {pokemon_name}")

        async def process_notification() -> None:
            if is_paused or is_afk:
                return

            # Safe action: report/log the notification rather than
            # automatically impersonating a user to catch it.
            print(
                f"[Queue] Pokémon notification processed: "
                f"{pokemon_name}"
            )

        await catch_queue.add(process_notification)


bot.run(DISCORD_TOKEN)
