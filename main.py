import asyncio
import sys
import logging
import shutil

from discord.ext import commands

from libs.lbs import *
from config.settings import token, DEFAULT_STATUS, XP_PER_MESSAGE, XP_COOLDOWN, LEVEL_MULTIPLIER
from config.database import Database


with open("data/logs.txt", "w", encoding="utf-8") as f:
    f.truncate(0)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("data/logs.txt", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

class StreamToLogger:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass

sys.stdout = StreamToLogger(logging.getLogger(), logging.INFO)
sys.stderr = StreamToLogger(logging.getLogger(), logging.ERROR)

class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix="/",
            intents=intents,
            activity=DEFAULT_STATUS
        )
        self.last_message_time = {}
        self.db = Database()

    async def setup_hook(self):
        for filename in os.listdir("cogs"):
            if filename.endswith(".py") and not filename.startswith("_"):
                if not filename.endswith("._"):
                    try:
                        await self.load_extension(f"cogs.{filename[:-3]}")
                        print(f"Loaded extension: {Fore.GREEN}{filename[:-3]}.py{Fore.RESET}")
                    except Exception as e:
                        print(f"Failed to load extension {filename}: {Fore.RED}{e}{Fore.RESET}")

    async def on_ready(self):
        print(f'\nLogged in as {self.user}')
        columns = shutil.get_terminal_size().columns
        print("-" * columns + "\n\n")
        try:
            await self.tree.sync()
        except Exception as e:
            print(f"Error syncing commands: {e}")

    async def update_user_xp(self, user_id: int, xp_to_add: int):
        user_id_str = str(user_id)
        user_data = self.db.get_user_level(user_id_str)
        
        if not user_data:
            current_xp = xp_to_add
            current_level = 0
        else:
            current_xp, current_level = user_data
            current_xp += xp_to_add

        new_level = int(current_xp / LEVEL_MULTIPLIER)
        
        if new_level > current_level:
            self.db.update_user_level(user_id_str, current_xp, new_level)
            return True, new_level

        self.db.update_user_level(user_id_str, current_xp, current_level)
        return False, current_level

    async def on_message(self, message):
        if message.author.bot:
            return

        await self.process_commands(message)

        current_time = message.created_at.timestamp()

        if message.author.id in self.last_message_time:
            time_diff = current_time - self.last_message_time[message.author.id]
            if time_diff < XP_COOLDOWN:
                return

        self.last_message_time[message.author.id] = current_time

        await self.update_user_xp(message.author.id, XP_PER_MESSAGE)

    async def close(self):
        self.db.close()
        await super().close()

async def main():
    async with Bot() as bot:
        await bot.start(token)

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    asyncio.run(main())