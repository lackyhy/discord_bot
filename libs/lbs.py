import time as _time
from code import interact

import discord
import os
import importlib.util

from colorama import Fore
from config.settings import ALLOWED_ROLE

def check_permissions(interaction: discord.Interaction) -> bool:
    return any(role.id in ALLOWED_ROLE for role in interaction.user.roles)


def log_message(message, log_type="INFO"):
    timestamp = _time.strftime('%Y-%m-%d %H:%M:%S')
    if log_type == "INFO":
        log_entry = f"[{timestamp}] [{log_type}]:    {message}"
    elif log_type == "ERROR":
        log_entry = f"[{timestamp}] {Fore.RED}[{log_type}]:    {message} {Fore.WHITE}"
    elif log_type == "WARN":
        log_entry = f"[{timestamp}] {Fore.YELLOW}[{log_type}]:    {message} {Fore.WHITE}"
    elif log_type == "SUCCESS":
        log_entry = f"[{timestamp}] {Fore.GREEN}[{log_type}]:    {message} {Fore.WHITE}"
    else:
        log_entry = f"[{timestamp}] [UNKNOWN]:    {message}"
    print(log_entry)


async def send_message(interaction: discord.Interaction, message=None, ephemeral=False, file=None, embed=None):
    try:
        kwargs = {"ephemeral": ephemeral}
        
        if isinstance(message, discord.Embed):
            print("Message is an embed, moving to embed parameter")
            embed = message
            message = None
        
        if message is not None:
            kwargs["content"] = message
        if file is not None:
            kwargs["file"] = file
        if embed is not None:
            kwargs["embed"] = embed

        await interaction.response.send_message(**kwargs)
    except discord.InteractionResponded:
        print("EROR (lbs.py discord.InteractionResponded): ", discord.InteractionResponded)

def get_bot_language():
    settings_path = os.path.join(os.path.dirname(__file__), '../config/settings.py')
    spec = importlib.util.spec_from_file_location("settings", settings_path)
    settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings)
    return getattr(settings, "LANGUAGE", "ru")

def set_bot_language(lang):
    settings_path = os.path.join(os.path.dirname(__file__), '../config/settings.py')
    with open(settings_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    with open(settings_path, "w", encoding="utf-8") as f:
        found = False
        for line in lines:
            if line.strip().startswith("LANGUAGE"):
                f.write(f'LANGUAGE = "{lang}"')
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f'\nLANGUAGE = "{lang}"')