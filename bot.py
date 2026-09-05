import asyncio
import random
import discord

from config import DISCORD_TOKEN, POKETWO_BOT_ID, HELPER_BOT_IDS
from services.parser import extract_pokemon_name
from services.queue import CatchQueue
from services.stealth import simulate_typo

# discord.py-self does not require intents for user accounts
bot = discord.Client()
catch_queue = CatchQueue()

is_paused = False
is_afk = False

# --- NEW: Smart Miss Counter Variables ---
ping_counter = 0
next_miss_target = random.randint(10, 15)

async def afk_timer(afk_seconds: int) -> None:
    global is_afk
    print(f"🚶 [Stealth] Taking a bathroom break. AFK for {int(afk_seconds / 60)} minutes.")
    await asyncio.sleep(afk_seconds)
    is_afk = False
    print("🔙 [Stealth] Back at the keyboard.")

@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} - Ultimate Stealth Mode + Async Queue Active.")
    print(f"🎯 [Stealth] Next forced miss is scheduled in {next_miss_target} pings.")

@bot.event
async def on_message(message: discord.Message) -> None:
    global is_paused, is_afk
    global ping_counter, next_miss_target

    msg_content = message.content.strip().lower()

    # 1. Handle own commands (User Bot Command Routing)
    if message.author.id == bot.user.id:
        if msg_content == "!pause":
            is_paused = True
            print("⏸️ Bot manually paused.")
            return
        if msg_content == "!resume":
            is_paused = False
            print("▶️ Bot manually resumed.")
            return
        return # Ignore all other messages sent by our own account

    # 2. Safety conditions
    if (
        message.author.id == POKETWO_BOT_ID
        and "Please tell us you're human!" in message.content
        and str(bot.user.id) in message.content
    ):
        is_paused = True
        print("⚠️ Captcha detected targeting YOUR account. Script paused.")
        return

    if (
        message.author.id == POKETWO_BOT_ID
        and "These colors seem unusual..." in message.content
        and str(bot.user.id) in message.content
    ):
        is_paused = True
        print("✨ Shiny caught - script paused.")
        return

    if is_paused or is_afk:
        return

    # 3. Helper-bot notification & Catching Logic
    if message.author.id in HELPER_BOT_IDS and str(bot.user.id) in message.content:
        
        # ---------------------------------------------------------
        # NEW: Smart 1-in-10-to-15 Miss Logic
        # ---------------------------------------------------------
        ping_counter += 1
        
        if ping_counter >= next_miss_target:
            print(f"🙈 [Stealth] Simulated human error: Ignored ping #{ping_counter}.")
            
            # Reset counter and pick a new target for the next miss
            ping_counter = 0
            next_miss_target = random.randint(10, 15)
            print(f"🎯 [Stealth] Next forced miss is scheduled in {next_miss_target} pings.")
            return

        # 2% chance to go AFK for 10-20 minutes
        if random.random() < 0.02:
            is_afk = True
            afk_seconds = random.randint(600, 1200) # 10 to 20 minutes
            bot.loop.create_task(afk_timer(afk_seconds))
            return

        pokemon_name = extract_pokemon_name(message.content)

        if not pokemon_name:
            return

        print(f"\n📥 Ping {ping_counter}/{next_miss_target} added to the queue: {pokemon_name}")

        async def process_notification() -> None:
            if is_paused or is_afk:
                return

            print(f"⚙️ Processing queued catch for: {pokemon_name}")
            
            # Read delay (300ms - 600ms)
            read_delay = random.uniform(0.3, 0.6)

            # Distraction simulation
            if random.random() < 0.10:
                distraction_time = random.uniform(2.0, 5.0)
                read_delay += distraction_time
                print(f"[Stealth] Distraction triggered. Delaying reaction by {int(distraction_time*1000)}ms")

            await asyncio.sleep(read_delay)

            # Typing simulation
            ms_per_char = random.uniform(0.04, 0.08)
            typing_delay = len(pokemon_name) * ms_per_char

            # Native typing indicator in discord.py-self
            async with message.channel.typing():
                await asyncio.sleep(typing_delay)

            # Typo generation
            final_name = pokemon_name
            if random.random() < 0.05:
                final_name = simulate_typo(final_name)
                print(f"[Stealth] Made a typo: {final_name}")

            # Command formatting
            cmd = random.choice(["c", "catch"])
            if random.random() < 0.70:
                final_name = final_name.lower()

            r_space = random.random()
            extra_space = "" if r_space < 0.03 else ("  " if r_space < 0.3 else " ")
            final_message = f"<@{POKETWO_BOT_ID}>{extra_space}{cmd} {final_name}"

            # Final safety check before executing
            if is_paused:
                print("🛑 Aborted sending message because script was paused mid-type.")
                return

            # Send the catch command
            await message.channel.send(final_message)
            print(f"🏓 Caught: {final_name} (Read: {int(read_delay*1000)}ms | Typed: {int(typing_delay*1000)}ms)")

            # 30% chance to send a casual follow-up message
            if random.random() < 0.30:
                follow_up_msgs = ["nice", "ok", "shine", "shine when", "gg"]
                chosen_msg = random.choice(follow_up_msgs)
                
                # Human delay before starting to type the follow-up (1 to 3 seconds)
                reaction_delay = random.uniform(1.0, 3.0)
                await asyncio.sleep(reaction_delay)
                
                if is_paused or is_afk:
                    return

                msg_typing_delay = len(chosen_msg) * random.uniform(0.04, 0.08)
                async with message.channel.typing():
                    await asyncio.sleep(msg_typing_delay)
                
                await message.channel.send(chosen_msg)
                print(f"💬 [Stealth] Sent follow-up message: '{chosen_msg}'")

        await catch_queue.add(process_notification)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
