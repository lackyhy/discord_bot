import discord
import os

# token, bot
token = " "

DEFAULT_STATUS = discord.Activity(
    type=discord.ActivityType.streaming,
    status=discord.Status.idle,
    name="/help, одерживает топ -0)",
)


# user id
OWNER_USER = [ ]
ALLOWED_USERS = [ ]

# role id
ADMIN_ROLE = [

]

MODERATOR_ROLE = [

]

ALLOWED_ROLE = [

]

OWNER_ROLES = [ ]



# XP
XP_PER_MESSAGE = 5
XP_COOLDOWN =  5
LEVEL_MULTIPLIER = 100

# dir
sql_dir = "sqp\\"

# channels
id_log_channel = 

# language:
LANGUAGE = "ru"

def set_bot_language(lang):
    settings_path = os.path.join(os.path.dirname(__file__), '../config/settings.py')
    with open(settings_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(settings_path, "w", encoding="utf-8") as f:
        found = False
        for line in lines:
            if line.strip().startswith("LANGUAGE"):
                f.write(f'LANGUAGE = "{lang}"\n')
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f'\nLANGUAGE = "{lang}"\n')

def set_allowed_roles(new_ids):
    settings_path = os.path.join(os.path.dirname(__file__), '../config/settings.py')
    with open(settings_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(settings_path, "w", encoding="utf-8") as f:
        for line in lines:
            if line.strip().startswith("ALLOWED_ROLE"):
                f.write(f'ALLOWED_ROLE = {new_ids}\n')
            else:
                f.write(line)
