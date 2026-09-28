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

# --- Global State & Locks ---
is_paused = False
is_afk = False

# This lock ensures the bot can never type/send two different messages at the exact same time
bot_action_lock = asyncio.Lock() 

# Tracks how many pokemon are currently queued or being caught
pending_catches = 0 

# --- Smart Miss Counter Variables ---
ping_counter = 0
next_miss_target = random.randint(10, 15)

async def afk_timer(afk_seconds: int) -> None:
    global is_afk
    minutes = afk_seconds // 60
    seconds = afk_seconds % 60
    print(f"🚶 [Stealth] Taking a bathroom break. AFK for {minutes} minutes and {seconds} seconds.")
    
    await asyncio.sleep(afk_seconds)
    
    is_afk = False 
    print("🔙 [Stealth] Back at the keyboard. Resuming auto-catch automatically!")

@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} - Ultimate Stealth Mode + Async Queue Active.")
    print(f"🎯 [Stealth] Next forced miss is scheduled in {next_miss_target} pings.")

@bot.event
async def on_message(message: discord.Message) -> None:
    global is_paused, is_afk
    global ping_counter, next_miss_target, pending_catches

    msg_content = message.content.strip().lower()

    # 1. Handle own commands
    if message.author.id == bot.user.id:
        if msg_content == "!pause":
            is_paused = True
            print("⏸️ Bot manually paused.")
            return
        if msg_content == "!resume":
            is_paused = False
            print("▶️ Bot manually resumed.")
            return
        return 

    # 2. Safety conditions (Captcha)
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
            async with bot_action_lock:
                reaction = random.choice(["YOOOOOO", "finallyyy", "damnnn", "yayyaya"])
                await asyncio.sleep(random.uniform(1.6, 3.0)) 
                async with message.channel.typing():
                    await asyncio.sleep(len(reaction) * random.uniform(0.08, 0.16)) 
                await message.channel.send(reaction)

                ping_msg = "<@716390085896962058> i l"
                await asyncio.sleep(random.uniform(2.4, 5.0)) 
                async with message.channel.typing():
                    await asyncio.sleep(len(ping_msg) * random.uniform(0.08, 0.16))
                await message.channel.send(ping_msg)

                final_msg = "tyty!"
                await asyncio.sleep(random.uniform(2.0, 4.0)) 
                async with message.channel.typing():
                    await asyncio.sleep(len(final_msg) * random.uniform(0.08, 0.16))
                await message.channel.send(final_msg)

        bot.loop.create_task(shiny_reaction_sequence())
        return
    # -------------------------------------

    if is_paused or is_afk:
        return

    # 3. Helper-bot notification & Catching Logic
    if message.author.id in HELPER_BOT_IDS and str(bot.user.id) in message.content:

        # --- Smart Miss Logic ---
        ping_counter += 1
        if ping_counter >= next_miss_target:
            print(f"🙈 [Stealth] Simulated human error: Ignored ping #{ping_counter}.")
            ping_counter = 0
            next_miss_target = random.randint(10, 15)
            print(f"🎯 [Stealth] Next forced miss is scheduled in {next_miss_target} pings.")
            return

        # --- AFK Logic ---
        if random.random() < 0.002:
            is_afk = True
            afk_seconds = random.randint(180, 300) 
            bot.loop.create_task(afk_timer(afk_seconds))
            return

        pokemon_name = extract_pokemon_name(message.content)
        if not pokemon_name:
            return

        # Increase the queue counter right before adding it
        pending_catches += 1
        print(f"\n📥 Ping {ping_counter}/{next_miss_target} added to the queue: {pokemon_name} (Total Pending: {pending_catches})")

        async def process_notification() -> None:
            global pending_catches
            try:
                if is_paused or is_afk:
                    return

                print(f"⚙️ Processing queued catch for: {pokemon_name}")

                # 1. Read delay
                read_delay = random.uniform(0.5, 0.98)
                if random.random() < 0.10:
                    distraction_time = random.uniform(2.0, 5.0)
                    read_delay += distraction_time
                    print(f"[Stealth] Distraction triggered. Delaying reaction by {int(distraction_time*1000)}ms")

                await asyncio.sleep(read_delay)

                # 2. Start Typing / Catching
                async with bot_action_lock:
                    if is_paused or is_afk: return

                    ms_per_char = random.uniform(0.04, 0.08)
                    typing_delay = len(pokemon_name) * ms_per_char

                    async with message.channel.typing():
                        await asyncio.sleep(typing_delay)

                    final_name = pokemon_name
                    made_typo = False
                    if random.random() < 0.05:
                        final_name = simulate_typo(final_name)
                        made_typo = True
                        print(f"[Stealth] Made a typo: {final_name}")

                    cmd = random.choice(["c", "catch"])
                    if random.random() < 0.70:
                        final_name = final_name.lower()

                    r_space = random.random()
                    extra_space = "" if r_space < 0.03 else ("  " if r_space < 0.3 else " ")
                    final_message = f"<@{POKETWO_BOT_ID}>{extra_space}{cmd} {final_name}"

                    await message.channel.send(final_message)
                    print(f"🏓 Caught: {final_name} (Read: {int(read_delay*1000)}ms | Typed: {int(typing_delay*1000)}ms)")

                # 3. Typo Correction (if applicable)
                if made_typo:
                    realize_delay = random.uniform(0.5, 1.5)
                    await asyncio.sleep(realize_delay)

                    async with bot_action_lock:
                        if is_paused or is_afk: return

                        correct_typing_delay = len(pokemon_name) * random.uniform(0.04, 0.08)
                        async with message.channel.typing():
                            await asyncio.sleep(correct_typing_delay)

                        correct_cmd = random.choice(["c", "catch"])
                        correct_name = pokemon_name.lower() if random.random() < 0.70 else pokemon_name
                        correct_msg = f"<@{POKETWO_BOT_ID}> {correct_cmd} {correct_name}"

                        await message.channel.send(correct_msg)
                        print(f"🔧 [Stealth] Corrected typo quickly with: {correct_name}")

                # 4. Late Follow-up Message (Runs as a background task)
                if random.random() < 0.30:
                    async def delayed_follow_up():
                        late_delay = random.uniform(6.0, 14.0)
                        await asyncio.sleep(late_delay)

                        # Check if a new ping arrived while we were waiting
                        if pending_catches > 0:
                            print("🚫 [Stealth] Cancelled follow-up: Priority catch in queue.")
                            return

                        if is_paused or is_afk:
                            return

                        follow_up_msgs = ["ok", "shine", "<@716390085896962058> i l", "hmm", "<@716390085896962058> sh", "damn", "oh", "sheesh", "wow", "ggs"]
                        chosen_msg = random.choice(follow_up_msgs)
                        msg_typing_delay = len(chosen_msg) * random.uniform(0.04, 0.08)

                        # Grab the lock and check one last time before typing
                        async with bot_action_lock:
                            if is_paused or is_afk or pending_catches > 0: 
                                return
                            
                            async with message.channel.typing():
                                await asyncio.sleep(msg_typing_delay)

                            await message.channel.send(chosen_msg)
                            print(f"💬 [Stealth] Sent late follow-up message: '{chosen_msg}'")

                    bot.loop.create_task(delayed_follow_up())

            finally:
                # The catch sequence for this ping is fully done. Lower the counter.
                pending_catches -= 1

        await catch_queue.add(process_notification)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
