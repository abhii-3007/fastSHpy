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

# --- Smart Miss Counter Variables ---
ping_counter = 0
next_miss_target = random.randint(10, 15)

async def afk_timer(afk_seconds: int) -> None:
    global is_afk
    minutes = afk_seconds // 60
    seconds = afk_seconds % 60
    print(f"🚶 [Stealth] Taking a bathroom break. AFK for {minutes} minutes and {seconds} seconds.")
    
    await asyncio.sleep(afk_seconds)
    
    # This line automatically resumes the bot when the timer finishes
    is_afk = False 
    print("🔙 [Stealth] Back at the keyboard. Resuming auto-catch automatically!")

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

    # --- Shiny Catch Sequence ---
    if (
        message.author.id == POKETWO_BOT_ID
        and "These colors seem unusual..." in message.content
        and str(bot.user.id) in message.content
    ):
        is_paused = True
        print("✨ Shiny caught - script paused. Initiating reaction sequence.")

        async def shiny_reaction_sequence():
            # 1. Random reaction
            reaction = random.choice(["YOOOOOO", "finallyyy", "damnnn", "yayyaya"])
            await asyncio.sleep(random.uniform(1.6, 3.0)) # Initial realization delay (DOUBLED)
            async with message.channel.typing():
                await asyncio.sleep(len(reaction) * random.uniform(0.08, 0.16)) # Typing delay (DOUBLED)
            await message.channel.send(reaction)

            # 2. First follow-up ping
            ping_msg = "<@716390085896962058> i l"
            await asyncio.sleep(random.uniform(2.4, 5.0)) # Delay between messages (DOUBLED)
            async with message.channel.typing():
                await asyncio.sleep(len(ping_msg) * random.uniform(0.08, 0.16)) # Typing delay (DOUBLED)
            await message.channel.send(ping_msg)

            # 3. Final tyty! message
            final_msg = "tyty!"
            await asyncio.sleep(random.uniform(2.0, 4.0)) # Delay between messages (DOUBLED)
            async with message.channel.typing():
                await asyncio.sleep(len(final_msg) * random.uniform(0.08, 0.16)) # Typing delay (DOUBLED)
            await message.channel.send(final_msg)

        # Run the sequence without blocking the main event loop
        bot.loop.create_task(shiny_reaction_sequence())
        return
    # -------------------------------------

    if is_paused or is_afk:
        return

    # 3. Helper-bot notification & Catching Logic
    if message.author.id in HELPER_BOT_IDS and str(bot.user.id) in message.content:

        # ---------------------------------------------------------
        # Smart 1-in-10-to-15 Miss Logic
        # ---------------------------------------------------------
        ping_counter += 1

        if ping_counter >= next_miss_target:
            print(f"🙈 [Stealth] Simulated human error: Ignored ping #{ping_counter}.")

            # Reset counter and pick a new target for the next miss
            ping_counter = 0
            next_miss_target = random.randint(10, 15)
            print(f"🎯 [Stealth] Next forced miss is scheduled in {next_miss_target} pings.")
            return

        # 2% chance to go AFK for 3-5 minutes
        if random.random() < 0.02:
            is_afk = True
            afk_seconds = random.randint(180, 300) # 180s to 300s (3 to 5 minutes)
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

            # Read delay (already increased via random bounds)
            read_delay = random.uniform(0.4, 0.85)

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
            made_typo = False
            if random.random() < 0.05:
                final_name = simulate_typo(final_name)
                made_typo = True
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

            # --- Typo Correction Logic ---
            if made_typo:
                if is_paused or is_afk:
                    return

                # Human delay to realize the mistake (0.5 to 1.5 seconds)
                realize_delay = random.uniform(0.5, 1.5)
                await asyncio.sleep(realize_delay)

                # Type out the correct command
                correct_typing_delay = len(pokemon_name) * random.uniform(0.04, 0.08)
                async with message.channel.typing():
                    await asyncio.sleep(correct_typing_delay)

                # Format and send the corrected catch command
                correct_cmd = random.choice(["c", "catch"])
                correct_name = pokemon_name.lower() if random.random() < 0.70 else pokemon_name
                correct_msg = f"<@{POKETWO_BOT_ID}> {correct_cmd} {correct_name}"

                await message.channel.send(correct_msg)
                print(f"🔧 [Stealth] Corrected typo quickly with: {correct_name}")

            # 30% chance to send a casual follow-up message
            if random.random() < 0.30:
                follow_up_msgs = ["nice", "ok", "shine", "shine when", "gg", "damn", "oh", "sheesh", "crazy", "wow"]
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
